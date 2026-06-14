import pytest
import os
from agent.models.types import Cluster, Review
from agent.processing.summarizer import extract_themes_and_quotes

@pytest.mark.live
@pytest.mark.asyncio
async def test_summarizer_live():
    if not os.environ.get("GROQ_API_KEY"):
        pytest.skip("GROQ_API_KEY not set")
        
    cluster = Cluster(
        cluster_id=1,
        reviews=[
            Review(rating=5, text="The mutual fund investment process is very smooth.", thumbs_up=0, app_version="1.0"),
            Review(rating=4, text="Easy to invest in mutual funds.", thumbs_up=0, app_version="1.0")
        ],
        centroid=[0.0],
        size=2
    )
    
    from agent.config import Config, ProductConfig
    config = Config(
        product=ProductConfig(id="x", play_store_app_id="x", display_name="x", google_doc_id="x", stakeholder_emails=[]),
        max_tokens_per_run=12000,
        request_interval_seconds=0,
        sample_size_per_cluster=5,
        max_retries_429=0
    )
    themes, quotes, ideas = await extract_themes_and_quotes([cluster], {"title": "Groww"}, config)
    
    assert len(themes) > 0
    assert themes[0].name
    assert themes[0].description
