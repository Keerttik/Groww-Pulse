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
from agent.delivery.email_delivery import create_email_draft, send_email

logger = get_logger(__name__)

# Constants for retries
MAX_RETRIES_MCP = 3

async def _call_with_retry(func, *args, retries=MAX_RETRIES_MCP, **kwargs):
    last_exception: Exception = RuntimeError(f"Unknown error in {func.__name__}")
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
        
        # 2. Connect to Play Store MCP and fetch data
        reviews = []
        app_info = {}
        try:
            async with AsyncExitStack() as stack:
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
                logger.info("Fetching reviews via MCP...")
                reviews = await _call_with_retry(fetch_reviews, session, config)
                app_info = await _call_with_retry(get_app_info, session, config)
        except Exception as mcp_err:
            logger.warning(f"Play Store MCP stdio connection failed: {mcp_err}. Falling back to direct store scraper.")
            from play_store_mcp.scraper import fetch_reviews_from_store, get_app_info_from_store
            from agent.models.types import Review
            raw_reviews = await fetch_reviews_from_store(
                app_id=config.product.play_store_app_id,
                country="in",
                count=config.max_reviews
            )
            reviews = [
                Review(
                    rating=r.rating,
                    text=r.text,
                    thumbs_up=r.thumbs_up,
                    app_version=r.app_version
                )
                for r in raw_reviews
            ]
            app_info = await get_app_info_from_store(
                app_id=config.product.play_store_app_id,
                country="in"
            )
        
        record.reviews_fetched = len(reviews)
        insert_record(record)
        
        if not reviews:
            logger.warning("Zero reviews fetched. Aborting pipeline.")
            record.status = "success"  # It's a success, just empty
            record.completed_at = datetime.datetime.now(datetime.timezone.utc)
            insert_record(record)
            return
            
        logger.info(f"Fetched {len(reviews)} reviews. Running processing pipeline...")
        
        # Export reviews to CSV for grading deliverables
        import csv
        data_dir = os.environ.get('DATA_DIR', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data'))
        os.makedirs(data_dir, exist_ok=True)
        csv_path = os.path.join(data_dir, 'reviews_export.csv')
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Rating', 'Text', 'ThumbsUp'])
                for r in reviews:
                    writer.writerow([r.rating, r.text, r.thumbs_up])
            logger.info(f"Exported {len(reviews)} reviews to {csv_path}")
        except Exception as e:
            logger.warning(f"Could not write reviews CSV: {e}")

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
        rest_url = os.environ.get("REST_SERVER_URL", config.delivery.rest_server_url)
        doc_result = await _call_with_retry(append_section_to_doc, config.product.google_doc_id, doc_content, rest_url, config.delivery.mcp_api_secret_key)
        
        if doc_result.status == "error":
            raise RuntimeError(f"Document delivery failed: {doc_result.error_message or 'Unknown error'}")
        
        # 7. Deliver Email
        logger.info(f"Delivering email ({email_mode} mode)...")
        recipients = config.product.stakeholder_emails
        if email_mode == "send":
            email_result = await _call_with_retry(send_email, email_content, recipients, rest_url, config.delivery.mcp_api_secret_key)
            if email_result.status == "error":
                logger.error("Email sending failed, but doc succeeded.")
                record.status = "partial"
                record.error_message = email_result.error_message or "Email send failed"
            else:
                record.status = "success"
                record.email_message_id = email_result.message_id
        else:
            email_result = await _call_with_retry(create_email_draft, email_content, recipients, rest_url, config.delivery.mcp_api_secret_key)
            if email_result.status == "error":
                logger.error("Email draft creation failed, but doc succeeded.")
                record.status = "partial"
                record.error_message = email_result.error_message or "Email draft delivery failed"
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
        err_msg = str(e)
        if hasattr(e, "exceptions"):
            # Unpack ExceptionGroup / BaseExceptionGroup
            sub_msgs = []
            for sub in e.exceptions:
                if hasattr(sub, "exceptions"):
                    sub_msgs.extend(str(s) for s in sub.exceptions)
                else:
                    sub_msgs.append(str(sub))
            err_msg = "; ".join(sub_msgs) if sub_msgs else str(e)

        logger.exception(f"Pipeline failed with error: {err_msg}")
        record.status = "failed"
        record.error_message = err_msg
        record.completed_at = datetime.datetime.now(datetime.timezone.utc)
        insert_record(record)
