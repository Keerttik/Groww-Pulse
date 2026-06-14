import pytest
import os
from datetime import datetime, timezone
from agent.models.types import RunRecord
from agent.run_record import init_db, insert_record, find_record, list_records

@pytest.fixture
def temp_db(tmp_path):
    # Use pytest's tmp_path to create a unique file for each test
    db_path = tmp_path / "test_pulse_runs.db"
    return str(db_path)

@pytest.fixture
def sample_record():
    return RunRecord(
        run_id="run-123",
        product="groww",
        iso_week="2026-W24",
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        status="success",
        reviews_fetched=500,
        clusters_found=4,
        themes_generated=8,
        doc_heading_anchor="groww-pulse-2026-w24",
        doc_id="doc-456",
        email_message_id="msg-789",
        email_mode="draft",
        llm_tokens_used=15000,
        error_message=None
    )

def test_init_db(temp_db):
    init_db(temp_db)
    assert os.path.exists(temp_db)

def test_insert_and_find_record(temp_db, sample_record):
    insert_record(sample_record, db_path=temp_db)
    
    found = find_record("groww", "2026-W24", db_path=temp_db)
    assert found is not None
    assert found.run_id == sample_record.run_id
    assert found.status == "success"
    assert found.reviews_fetched == 500

def test_find_record_not_found(temp_db):
    # Not initialized db, so find_record should return None gracefully
    found = find_record("groww", "2026-W24", db_path=temp_db)
    assert found is None

def test_find_record_only_returns_success(temp_db, sample_record):
    sample_record.status = "failed"
    insert_record(sample_record, db_path=temp_db)
    
    found = find_record("groww", "2026-W24", db_path=temp_db)
    assert found is None

def test_list_records(temp_db, sample_record):
    insert_record(sample_record, db_path=temp_db)
    
    # Insert another record for different week
    record_dict = sample_record.to_dict()
    record_dict["run_id"] = "run-124"
    record_dict["iso_week"] = "2026-W23"
    record2 = RunRecord.from_dict(record_dict)
    
    insert_record(record2, db_path=temp_db)
    
    records = list_records("groww", limit=10, db_path=temp_db)
    assert len(records) == 2
    
def test_upsert_behavior(temp_db, sample_record):
    # Insert initial partial record
    sample_record.status = "partial"
    sample_record.email_message_id = None
    insert_record(sample_record, db_path=temp_db)
    
    # Complete the run and update
    sample_record.email_message_id = "msg-789"
    insert_record(sample_record, db_path=temp_db)
    
    records = list_records("groww", limit=10, db_path=temp_db)
    assert len(records) == 1
    assert records[0].email_message_id == "msg-789"
    assert records[0].status == "partial"
