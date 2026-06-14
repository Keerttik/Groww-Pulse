import json
from typing import List
from mcp import ClientSession
from agent.models.types import Review
from agent.config import Config

async def fetch_reviews(session: ClientSession, config: Config) -> List[Review]:
    result_raw = await session.call_tool("fetch_reviews", {
        "app_id": config.product.play_store_app_id,
        "count": config.max_reviews,
        "country": "in",
    })
    
    if not result_raw.content:
        return []
        
    text = result_raw.content[0].text
    data = json.loads(text)

    if "error" in data:
        raise RuntimeError(f"Play Store MCP Error: {data['error']}")
        
    reviews_data = data.get("reviews", [])
    reviews = []
    for r in reviews_data:
        reviews.append(Review(
            rating=r.get("rating", 0),
            text=r.get("text", ""),
            thumbs_up=r.get("thumbs_up", 0),
            app_version=r.get("app_version")
        ))
        
    return reviews

async def get_app_info(session: ClientSession, config: Config) -> dict:
    result_raw = await session.call_tool("get_app_info", {
        "app_id": config.product.play_store_app_id,
        "country": "in",
    })
    
    if not result_raw.content:
        return {}
        
    text = result_raw.content[0].text
    data = json.loads(text)
        
    if "error" in data:
        raise RuntimeError(f"Play Store MCP Error: {data['error']}")
        
    return data
