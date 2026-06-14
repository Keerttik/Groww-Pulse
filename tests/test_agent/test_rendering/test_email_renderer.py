import pytest
from datetime import datetime, date
from agent.models.types import PulseReport, Theme, Quote, ActionIdea
from agent.rendering.email_renderer import render_email

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
        quotes=[],
        action_ideas=[],
        app_info={}
    )

def test_email_renderer_subject(sample_report):
    email = render_email(sample_report, "http://doc.link")
    assert email.subject == "Groww Review Pulse — Week 2026-W24"

def test_email_renderer_body(sample_report):
    email = render_email(sample_report, "http://doc.link")
    
    # Verify HTML body
    assert "487 reviews" in email.html_body
    assert "App performance & bugs" in email.html_body
    assert "http://doc.link" in email.html_body
    assert "🔴" in email.html_body
    assert "🟢" in email.html_body
    
    # Verify Text body
    assert "487 reviews" in email.text_body
    assert "App performance & bugs" in email.text_body
    assert "http://doc.link" in email.text_body
    assert "🔴" in email.text_body
