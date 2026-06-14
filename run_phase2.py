import asyncio
import json
import datetime
import os
from dotenv import load_dotenv

from agent.models.types import Review
from agent.config import load_config
from agent.processing.pipeline import run_processing_pipeline

async def main():
    # Load env vars from .env file
    load_dotenv()
    
    config = load_config()
    print(f"Loaded config for: {config.product.display_name}")
    
    # We will use the test fixtures from Phase 1 to avoid needing the full MCP server running
    with open("tests/test_play_store_mcp/fixtures/sample_reviews.json", "r") as f:
        data = json.load(f)
        
    reviews = []
    for r in data.get("reviews", []):
        reviews.append(Review(
            rating=r.get("rating", 0),
            text=r.get("text", ""),
            thumbs_up=r.get("thumbs_up", 0),
            app_version=r.get("app_version")
        ))
        
    print(f"Loaded {len(reviews)} reviews from fixtures.")
    
    # Duplicate them a bit so they form clusters if there are too few in the fixture
    if len(reviews) < 50:
        reviews = reviews * 50
        print(f"Duplicated reviews to {len(reviews)} for better clustering.")
    
    app_info = {
        "title": config.product.display_name,
        "score": 4.5
    }
    
    start_date = datetime.date.today() - datetime.timedelta(days=7)
    end_date = datetime.date.today()
    
    print("Running Phase 2 processing pipeline...")
    try:
        report = await run_processing_pipeline(reviews, app_info, config, start_date, end_date)
        print("\n--- PULSE REPORT GENERATED ---")
        print(f"Themes discovered: {len(report.themes)}")
        for t in report.themes:
            print(f" - [{t.sentiment}] {t.name}: {t.description} (Reviews: {t.review_count})")
            
        print(f"\nQuotes validated: {len(report.quotes)}")
        for q in report.quotes:
            print(f" - \"{q.text}\" (Rating: {q.rating})")
            
        print(f"\nAction Ideas: {len(report.action_ideas)}")
        for a in report.action_ideas:
            print(f" - {a.title}: {a.description} (Related to: {a.related_theme})")
            
    except Exception as e:
        print(f"Pipeline failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
