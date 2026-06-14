import pytest
from datetime import datetime, timezone
from agent.models.types import Review, Quote, Theme, ActionIdea, RunRecord, PulseReport, ReviewEmbedding, Cluster

def test_review_serialization():
    r = Review(
        rating=5,
        text="Great app",
        thumbs_up=10,
        app_version="4.9.0"
    )
    d = r.to_dict()
    assert d['rating'] == 5
    r2 = Review.from_dict(d)
    assert r == r2

def test_run_record_serialization():
    r = RunRecord(
        run_id="uuid-1",
        product="groww",
        iso_week="2026-W24",
        started_at=datetime.now(timezone.utc),
        completed_at=None,
        status="success",
        reviews_fetched=100,
        clusters_found=5,
        themes_generated=3,
        doc_heading_anchor="anchor-1",
        doc_id="doc1",
        email_message_id=None,
        email_mode="draft",
        llm_tokens_used=1000,
        error_message=None
    )
    d = r.to_dict()
    r2 = RunRecord.from_dict(d)
    assert r == r2
