import asyncio
import json
import datetime
from dotenv import load_dotenv

from agent.models.types import Review
from agent.config import load_config
from agent.processing.pipeline import run_processing_pipeline
from agent.rendering.report_renderer import render_doc_content
from agent.delivery.docs_delivery import append_section_to_doc

async def main():
    # Load env vars from .env file
    load_dotenv()
    
    config = load_config()
    print(f"Loaded config for: {config.product.display_name}")
    print(f"Target Google Doc ID: {config.product.google_doc_id}")
    
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
    
    print("\nRunning Phase 2 processing pipeline...")
    try:
        report = await run_processing_pipeline(reviews, app_info, config, start_date, end_date)
        
        print("\n--- PHASE 3 RENDERING ---")
        doc_content = render_doc_content(report, app_info)
        print("Rendered plain text output successfully.")
        
        print("\n--- PHASE 4 & 5 DELIVERY (Docs + Gmail via REST) ---")
        print(f"Connecting to REST API: {config.delivery.rest_server_url}")
        
        # 1. Google Docs
        doc_result = await append_section_to_doc(
            doc_id=config.product.google_doc_id,
            content=doc_content,
            rest_server_url=config.delivery.rest_server_url,
            secret_key=config.delivery.mcp_api_secret_key
        )
        print(f"Docs Delivery Result: {doc_result.status}")
        
        if doc_result.status == "appended":
            print(f"✅ SUCCESS! Check your Google Doc: https://docs.google.com/document/d/{config.product.google_doc_id}/edit")
        else:
            print("❌ FAILED to append to document.")
            
        # 2. Gmail Draft
        from agent.rendering.email_renderer import render_email
        from agent.delivery.email_delivery import create_email_draft
        
        doc_link = f"https://docs.google.com/document/d/{config.product.google_doc_id}/edit"
        email_content = render_email(report, doc_link)
        
        email_result = await create_email_draft(
            email=email_content,
            recipients=config.product.stakeholder_emails,
            rest_server_url=config.delivery.rest_server_url,
            secret_key=config.delivery.mcp_api_secret_key
        )
        print(f"Email Delivery Result: {email_result.status}")
        if email_result.status == "drafted":
            print("✅ SUCCESS! Check your Gmail Drafts.")
        else:
            print("❌ FAILED to create Gmail draft.")
        
    except Exception as e:
        print(f"Pipeline failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
