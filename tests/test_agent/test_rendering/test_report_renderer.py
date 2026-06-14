import pytest
from datetime import datetime, date
from agent.models.types import PulseReport, Theme, Quote, ActionIdea
from agent.rendering.report_renderer import render_doc_content

@pytest.fixture
def sample_report():
    return PulseReport(
        product="groww",
        iso_week="2026-w24",
        generated_at=datetime(2026, 6, 9, 6, 0),
        review_window=(date(2026, 6, 9), date(2026, 6, 15)),
        total_reviews_analyzed=487,
        themes=[
            Theme(name="App performance & bugs", description="Lag and crashes", review_count=50, sentiment="negative"),
            Theme(name="Trading Experience", description="Great execution", review_count=36, sentiment="positive"),
        ],
        quotes=[
            Quote(text="App crashed during market hours.", rating=1, validated=True),
            Quote(text="Excellent app for trading.", rating=5, validated=True),
        ],
        action_ideas=[
            ActionIdea(title="Improve App Stability", description="Fix crashes", related_theme="App performance & bugs"),
        ],
        app_info={}
    )

def test_report_renderer_anchor_id(sample_report):
    doc_content = render_doc_content(sample_report, {"title": "Groww"})
    assert doc_content.anchor_id == "groww-pulse-2026-w24"

def test_report_renderer_content(sample_report):
    doc_content = render_doc_content(sample_report, {"title": "Groww"})
    
    # Verify main contents are present
    assert "Groww — Week 2026-W24" in doc_content.plain_text
    assert "[Bookmark: groww-pulse-2026-w24]" in doc_content.plain_text
    
    # Verify Theme extraction
    assert "App performance & bugs" in doc_content.plain_text
    assert "🔴" in doc_content.plain_text
    
    # Verify Quotes
    assert "App crashed during market hours." in doc_content.plain_text
