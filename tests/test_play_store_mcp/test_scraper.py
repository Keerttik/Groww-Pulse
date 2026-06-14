import pytest
from play_store_mcp.scraper import format_review

def test_format_review():
    raw_review = {
        "score": 4,
        "content": "Good app to trade with",
        "thumbsUpCount": 5,
        "reviewCreatedVersion": "1.0"
    }
    formatted = format_review(raw_review)
    assert formatted.rating == 4
    assert formatted.text == "Good app to trade with"
    assert formatted.thumbs_up == 5
    assert formatted.app_version == "1.0"

@pytest.mark.live
@pytest.mark.asyncio
async def test_live_scraper():
    from play_store_mcp.scraper import fetch_reviews_from_store, get_app_info_from_store
    
    info = await get_app_info_from_store("com.nextbillion.groww")
    assert info["app_id"] == "com.nextbillion.groww"
    assert "Groww" in info["title"]
    
    reviews = await fetch_reviews_from_store("com.nextbillion.groww", count=50)
    assert len(reviews) > 0
    # Make sure text is at least 8 words (normalization check)
    assert len(reviews[0].text.split()) >= 8
