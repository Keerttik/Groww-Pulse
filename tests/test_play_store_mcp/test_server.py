import pytest
import json
from play_store_mcp.server import list_tools, call_tool

@pytest.mark.asyncio
async def test_list_tools():
    tools = await list_tools()
    assert len(tools) == 2
    names = [t.name for t in tools]
    assert "fetch_reviews" in names
    assert "get_app_info" in names

@pytest.mark.asyncio
async def test_call_tool_fetch_reviews(monkeypatch):
    async def mock_fetch(*args, **kwargs):
        from play_store_mcp.models import FormattedReview
        return [FormattedReview(
            rating=5, text="test",
            thumbs_up=0
        )]
    
    import play_store_mcp.server
    monkeypatch.setattr(play_store_mcp.server, "fetch_reviews_from_store", mock_fetch)
    
    result = await call_tool("fetch_reviews", {"app_id": "com.mock"})
    assert len(result) == 1
    data = json.loads(result[0].text)
    assert data["app_id"] == "com.mock"
    assert data["review_count"] == 1
    assert data["reviews"][0]["rating"] == 5

@pytest.mark.asyncio
async def test_call_tool_invalid():
    with pytest.raises(ValueError):
        await call_tool("invalid_tool", {})
