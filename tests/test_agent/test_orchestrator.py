import pytest
import datetime
from unittest.mock import patch, MagicMock, AsyncMock
from agent.models.types import Review, PulseReport, Theme, Quote, ActionIdea
from agent.orchestrator import run_pulse
from agent.run_record import find_record, init_db
from agent.delivery.models import DeliveryResult, EmailDeliveryResult

@pytest.fixture
def mock_config():
    with patch('agent.orchestrator.load_config') as mock_load:
        config = MagicMock()
        config.product.id = "groww"
        config.product.google_doc_id = "test-doc-id"
        config.stakeholder_emails = ["test@example.com"]
        config.rest_server_url = "http://localhost:8000"
        mock_load.return_value = config
        yield config

@pytest.fixture
def mock_pipeline_deps():
    with patch('agent.orchestrator.stdio_client') as mock_stdio, \
         patch('agent.orchestrator.ClientSession') as mock_session_cls, \
         patch('agent.orchestrator.fetch_reviews') as mock_fetch, \
         patch('agent.orchestrator.get_app_info') as mock_app_info, \
         patch('agent.orchestrator.run_processing_pipeline') as mock_pipeline, \
         patch('agent.orchestrator.render_doc_content') as mock_render_doc, \
         patch('agent.orchestrator.render_email') as mock_render_email, \
         patch('agent.orchestrator.append_section_to_doc') as mock_append, \
         patch('agent.orchestrator.create_email_draft') as mock_email:
         
        # Mock MCP session
        mock_stdio.return_value.__aenter__.return_value = (AsyncMock(), AsyncMock())
        mock_session = AsyncMock()
        mock_session_cls.return_value.__aenter__.return_value = mock_session
        
        # Mock ingestion
        mock_fetch.return_value = [Review(rating=5, text="Great", thumbs_up=0, app_version="1.0")]
        mock_app_info.return_value = {"title": "Groww"}
        
        # Mock processing
        mock_pipeline.return_value = PulseReport(
            product="groww",
            iso_week="2026-W24",
            generated_at=datetime.datetime.now(),
            review_window=(datetime.date.today(), datetime.date.today()),
            total_reviews_analyzed=1,
            themes=[Theme("Test", "Desc", 1, "positive")],
            quotes=[],
            action_ideas=[],
            app_info={"title": "Groww"}
        )
        
        # Mock rendering
        mock_doc_content = MagicMock()
        mock_doc_content.anchor_id = "test-anchor"
        mock_render_doc.return_value = mock_doc_content
        mock_render_email.return_value = MagicMock()
        
        # Mock delivery
        mock_append.return_value = DeliveryResult(status="appended", anchor="test-anchor")
        mock_email.return_value = EmailDeliveryResult(status="drafted", draft_id="draft-123")
        
        yield {
            "fetch": mock_fetch,
            "pipeline": mock_pipeline,
            "append": mock_append,
            "email": mock_email
        }

@pytest.fixture
def clean_db():
    import sqlite3
    import os
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'run_records', 'pulse_runs.db')
    if os.path.exists(db_path):
        os.remove(db_path)
    init_db(db_path)
    yield db_path

@pytest.mark.asyncio
async def test_run_pulse_happy_path(mock_config, mock_pipeline_deps, clean_db):
    await run_pulse("2026-W24")
    
    # Assertions
    mock_pipeline_deps["fetch"].assert_called_once()
    mock_pipeline_deps["pipeline"].assert_called_once()
    mock_pipeline_deps["append"].assert_called_once()
    mock_pipeline_deps["email"].assert_called_once()
    
    record = find_record("groww", "2026-W24")
    assert record is not None
    assert record.status == "success"
    assert record.email_message_id == "draft-123"

@pytest.mark.asyncio
async def test_run_pulse_idempotency_skip(mock_config, mock_pipeline_deps, clean_db):
    # Run once
    await run_pulse("2026-W24")
    assert mock_pipeline_deps["fetch"].call_count == 1
    
    # Run again without force
    await run_pulse("2026-W24")
    # Fetch should NOT be called again
    assert mock_pipeline_deps["fetch"].call_count == 1

@pytest.mark.asyncio
async def test_run_pulse_force_rerun(mock_config, mock_pipeline_deps, clean_db):
    # Run once
    await run_pulse("2026-W24")
    assert mock_pipeline_deps["fetch"].call_count == 1
    
    # Run again with force
    await run_pulse("2026-W24", force=True)
    # Fetch SHOULD be called again
    assert mock_pipeline_deps["fetch"].call_count == 2

@pytest.mark.asyncio
async def test_run_pulse_partial_failure(mock_config, mock_pipeline_deps, clean_db):
    # Make email delivery fail
    mock_pipeline_deps["email"].return_value = EmailDeliveryResult(status="error")
    
    await run_pulse("2026-W24")
    
    # Record should be partial
    import sqlite3
    with sqlite3.connect(clean_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM runs WHERE product='groww' AND iso_week='2026-W24'")
        status = cursor.fetchone()[0]
        assert status == "partial"

@pytest.mark.asyncio
async def test_run_pulse_zero_reviews(mock_config, mock_pipeline_deps, clean_db):
    # Return empty reviews
    mock_pipeline_deps["fetch"].return_value = []
    
    await run_pulse("2026-W24")
    
    # Pipeline and delivery should NOT be called
    mock_pipeline_deps["pipeline"].assert_not_called()
    mock_pipeline_deps["append"].assert_not_called()
    
    record = find_record("groww", "2026-W24")
    assert record is not None
    assert record.status == "success"
    assert record.reviews_fetched == 0
