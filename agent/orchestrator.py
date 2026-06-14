import asyncio
import os
import sys
import time
import datetime
from contextlib import AsyncExitStack
from typing import Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from agent.config import load_config
from agent.logger import get_logger
from agent.models.types import RunRecord, PulseReport
from agent.run_record import find_record, insert_record
from agent.ingestion.ingestion import fetch_reviews, get_app_info
from agent.processing.pipeline import run_processing_pipeline
from agent.rendering.report_renderer import render_doc_content
from agent.rendering.email_renderer import render_email
from agent.delivery.docs_delivery import append_section_to_doc
from agent.delivery.email_delivery import create_email_draft

logger = get_logger(__name__)

# Constants for retries
MAX_RETRIES_MCP = 3

async def _call_with_retry(func, *args, retries=MAX_RETRIES_MCP, **kwargs):
    last_exception = None
    for attempt in range(1, retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            logger.warning(f"Attempt {attempt}/{retries} failed for {func.__name__}: {str(e)}")
            if attempt < retries:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    logger.error(f"All {retries} attempts failed for {func.__name__}")
    raise last_exception

async def run_pulse(week: str, force: bool = False, email_mode: str = "draft"):
    """
    Run the full Groww Pulse pipeline for a given ISO week.
    """
    run_id = f"run-{int(time.time())}"
    config = load_config()
    product_id = config.product.id
    
    logger.info(f"Starting pulse run {run_id} for {product_id} week {week}", extra={"run_id": run_id, "iso_week": week})
    
    # 1. Idempotency Check
    existing_record = find_record(product_id, week)
    if existing_record:
        if existing_record.status == "success" and not force:
            logger.info(f"Skipping: Success record already exists for {product_id} {week}.")
            return
        elif force:
            logger.info(f"Force mode enabled. Re-running over existing record (status: {existing_record.status}).")
            # If it was a partial run, we might want to skip some steps, but for simplicity, we re-run
            # the pipeline and let delivery layer idempotency handle it (or just recreate).
    
    started_at = datetime.datetime.now(datetime.timezone.utc)
    
    record = RunRecord(
        run_id=run_id,
        product=product_id,
        iso_week=week,
        started_at=started_at,
        completed_at=None,
        status="running",
        reviews_fetched=0,
        clusters_found=0,
        themes_generated=0,
        doc_heading_anchor=None,
        doc_id=None,
        email_message_id=None,
        email_mode=email_mode,
        llm_tokens_used=0,
        error_message=None
    )
    
    # Insert the initial 'running' record so the UI sees it immediately
    insert_record(record)
    
    try:
        # Determine date range based on week (mocked logic or simple window for now)
        # Using today minus 60 days as a placeholder window for pipeline arguments
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=60)
        
        async with AsyncExitStack() as stack:
            # 2. Connect to Play Store MCP
            env = os.environ.copy()
            env["PYTHONPATH"] = os.getcwd()
            server_params = StdioServerParameters(
                command=sys.executable,
                args=["-m", "play_store_mcp.server"],
                env=env
            )
            
            logger.info("Connecting to Play Store MCP...")
            stdio_transport = await stack.enter_async_context(stdio_client(server_params))
            read, write = stdio_transport
            session = await stack.enter_async_context(ClientSession(read, write))
            
            await session.initialize()
            
            # 3. Fetch reviews and app info
            logger.info("Fetching reviews...")
            reviews = await _call_with_retry(fetch_reviews, session, config)
            app_info = await _call_with_retry(get_app_info, session, config)
            
            record.reviews_fetched = len(reviews)
            insert_record(record)
            
            if not reviews:
                logger.warning("Zero reviews fetched. Aborting pipeline.")
                record.status = "success"  # It's a success, just empty
                record.completed_at = datetime.datetime.now(datetime.timezone.utc)
                insert_record(record)
                return
                
            logger.info(f"Fetched {len(reviews)} reviews. Running processing pipeline...")
            
            # 4. Processing Pipeline
            report = await run_processing_pipeline(reviews, app_info, config, start_date, end_date)
            
            record.clusters_found = len(report.themes)  # Approx mapping
            record.themes_generated = len(report.themes)
            # LLM tokens used tracking could be added here if pipeline returned it
            
            # 5. Render Doc and Email
            logger.info("Rendering document and email content...")
            doc_content = render_doc_content(report, app_info)
            email_content = render_email(report, f"https://docs.google.com/document/d/{config.product.google_doc_id}")
            
            record.doc_heading_anchor = doc_content.anchor_id
            record.doc_id = config.product.google_doc_id
            
            # 6. Deliver Doc
            logger.info("Delivering document section...")
            rest_url = os.environ.get("REST_SERVER_URL", config.rest_server_url)
            doc_result = await _call_with_retry(append_section_to_doc, config.product.google_doc_id, doc_content, rest_url)
            
            if doc_result.status == "error":
                raise RuntimeError("Document delivery failed.")
            
            # 7. Deliver Email
            logger.info(f"Delivering email ({email_mode} mode)...")
            recipients = config.stakeholder_emails
            # In 'draft' mode, it creates a draft. In 'send' mode, it would send (not implemented fully in REST server but handled there).
            email_result = await _call_with_retry(create_email_draft, email_content, recipients, rest_url)
            
            if email_result.status == "error":
                logger.error("Email delivery failed, but doc succeeded.")
                record.status = "partial"
                record.error_message = "Email delivery failed"
            else:
                record.status = "success"
                record.email_message_id = email_result.draft_id
                
            record.completed_at = datetime.datetime.now(datetime.timezone.utc)
            insert_record(record)
            
            if record.status == "success":
                logger.info(f"Pulse run completed successfully for {product_id} {week}")
            else:
                logger.warning(f"Pulse run completed with partial failures for {product_id} {week}")

    except Exception as e:
        logger.exception(f"Pipeline failed with error: {str(e)}")
        record.status = "failed"
        record.error_message = str(e)
        record.completed_at = datetime.datetime.now(datetime.timezone.utc)
        insert_record(record)
