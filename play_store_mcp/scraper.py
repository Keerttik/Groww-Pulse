import asyncio
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import re
from google_play_scraper import reviews as gp_reviews, app as gp_app, Sort
from play_store_mcp.config import config
from play_store_mcp.models import FormattedReview

def is_valid_review(text: str) -> bool:
    if not text:
        return False
        
    # 1. Less than 8 words
    if len(text.split()) < 8:
        return False
        
    # 2. Contains emojis or non-English characters
    # Allowed: ASCII (0-127), smart quotes, ellipsis, Rupee symbol
    allowed_pattern = re.compile(r'^[\x00-\x7F\u2018\u2019\u201C\u201D\u2026\u20B9]*$')
    if not allowed_pattern.match(text):
        return False
        
    return True

def format_review(raw: Dict[Any, Any]) -> FormattedReview:
    return FormattedReview(
        rating=raw.get("score", 0),
        text=raw.get("content", "") or "",
        thumbs_up=raw.get("thumbsUpCount", 0),
        app_version=raw.get("reviewCreatedVersion")
    )

async def fetch_reviews_from_store(
    app_id: str,
    country: str = config.default_country,
    language: str = config.default_lang,
    count: int = config.max_reviews,
    sort_by: str = "newest",
    filter_score: Optional[int] = None
) -> List[FormattedReview]:
    sort_enum = Sort.NEWEST if sort_by == "newest" else Sort.MOST_RELEVANT
    if sort_by == "rating":
        sort_enum = Sort.RATING

    # Add artificial throttle delay to respect config
    await asyncio.sleep(config.throttle_ms / 1000.0)

    # Use asyncio.to_thread since google_play_scraper is synchronous
    result, _ = await asyncio.to_thread(
        gp_reviews,
        app_id,
        lang=language,
        country=country,
        sort=sort_enum,
        count=count,
        filter_score_with=filter_score
    )

    # Dump actual reviews
    os.makedirs("data", exist_ok=True)
    with open("data/actual_reviews.json", "w", encoding="utf-8") as f:
        def default_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError
        json.dump(result, f, default=default_serializer, indent=2, ensure_ascii=False)

    formatted = []
    for r in result:
        rev = format_review(r)
        if is_valid_review(rev.text):
            formatted.append(rev)
            
    # Dump normalized reviews
    with open("data/normalized_reviews.json", "w", encoding="utf-8") as f:
        json.dump([r.model_dump() for r in formatted], f, indent=2, ensure_ascii=False)

    return formatted

async def get_app_info_from_store(
    app_id: str,
    country: str = config.default_country,
    language: str = config.default_lang
) -> Dict[str, Any]:
    
    # Add artificial throttle delay
    await asyncio.sleep(config.throttle_ms / 1000.0)
    
    result = await asyncio.to_thread(
        gp_app,
        app_id,
        lang=language,
        country=country
    )
    return {
        "app_id": app_id,
        "title": result.get("title", ""),
        "rating": result.get("score", 0.0),
        "ratings_count": result.get("ratings", 0),
        "current_version": result.get("version"),
        "installs": result.get("installs", "0+"),
        "updated": result.get("updated")
    }
