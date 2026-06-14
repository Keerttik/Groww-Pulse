import pytest
import datetime
from agent.models.types import Review, Theme, Quote, ActionIdea
from agent.config import Config, ProductConfig
from agent.processing.pipeline import run_processing_pipeline

# Mock the summarizer so we don't hit the real Groq API in regular tests
@pytest.fixture
def mock_summarizer(monkeypatch):
    async def mock_extract(*args, **kwargs):
        return (
            [Theme(name="Test Theme", description="Test Description", review_count=5, sentiment="positive")],
            [Quote(text="Great app", rating=5, validated=False)],
            [ActionIdea(title="More features", description="Add feature X", related_theme="Test Theme")]
        )
    monkeypatch.setattr("agent.processing.pipeline.extract_themes_and_quotes", mock_extract)

@pytest.mark.asyncio
async def test_pipeline_e2e_mocked(mock_summarizer):
    config = Config(
        product=ProductConfig(id="groww", play_store_app_id="com.nextbillion.groww", display_name="Groww", google_doc_id="x", stakeholder_emails=[]),
        min_cluster_size=5,
        min_reviews_floor=2 # lowered for test
    )
    
    reviews = []
    # Create 15 identical positive reviews
    for _ in range(15):
        reviews.append(Review(rating=5, text="Great app, highly recommend it.", thumbs_up=0, app_version="1.0"))
    # Create 15 identical negative reviews
    for _ in range(15):
        reviews.append(Review(rating=1, text="Terrible app, crashes all the time.", thumbs_up=0, app_version="1.0"))
        
    start_date = datetime.date(2026, 6, 1)
    end_date = datetime.date(2026, 6, 7)
    
    report = await run_processing_pipeline(reviews, {"title": "Groww"}, config, start_date, end_date)
    
    assert report.total_reviews_analyzed == 30
    assert len(report.themes) == 1
    assert report.themes[0].name == "Test Theme"
    # The quote validator drops the mocked quote "Great app" because it's not a fuzzy match for the actual review texts provided above
    # Wait, "Great app" is a substring of "Great app, highly recommend it."! So it SHOULD be validated!
    assert len(report.quotes) == 1
    assert report.quotes[0].validated is True
    assert report.quotes[0].rating == 5
