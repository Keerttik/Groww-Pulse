import datetime
from typing import List
from agent.models.types import Review, PulseReport
from agent.config import Config
from agent.processing.pii_scrubber import scrub_pii
from agent.processing.embeddings import generate_embeddings
from agent.processing.clustering import cluster_reviews
from agent.processing.summarizer import extract_themes_and_quotes
from agent.processing.validator import validate_quotes

async def run_processing_pipeline(reviews: List[Review], app_info: dict, config: Config, review_window_start: datetime.date, review_window_end: datetime.date) -> PulseReport:
    """End-to-end processing pipeline: from raw reviews to PulseReport."""
    if not reviews:
        raise ValueError("No reviews provided to the pipeline.")
        
    # 1. PII Scrubbing is handled BEFORE embedding to avoid leaking PII to local model
    # Note: We do NOT scrub the original reviews for the validator to match against.
    # We should make a copy or scrub texts specifically for embeddings.
    
    # In Phase 2 plan, scrub is applied before embedding and LLM. 
    # The validator needs the original unscrubbed text. Let's keep original reviews untouched
    # but create scrubbed versions for embeddings.
    
    # 2. Embeddings (handles scrubbing internally for vector creation)
    embeddings = generate_embeddings(reviews)
    
    # 3. Clustering
    clusters = cluster_reviews(embeddings, config)
    
    if not clusters:
        # ML Floor aborted
        raise ValueError("Not enough reviews to form clusters (below min_reviews_floor).")
        
    # Scrub the clusters before sending to LLM
    for c in clusters:
        for r in c.reviews:
            r.text = scrub_pii(r.text)
            
    # 4. LLM Summarization
    themes, quotes, ideas = await extract_themes_and_quotes(clusters, app_info, config)
    
    # 5. Quote Validation
    # We validate against the ORIGINAL unscrubbed reviews
    validated_quotes = validate_quotes(quotes, reviews)
    
    # Filter out invalid quotes
    valid_quotes = [q for q in validated_quotes if q.validated]
    
    # 6. Generate Report
    report = PulseReport(
        product=config.product.id,
        iso_week=datetime.date.today().strftime("%G-W%V"),
        generated_at=datetime.datetime.now(),
        review_window=(review_window_start, review_window_end),
        total_reviews_analyzed=len(reviews),
        themes=themes,
        quotes=valid_quotes,
        action_ideas=ideas,
        app_info=app_info
    )
    
    return report
