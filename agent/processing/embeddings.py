import os
import torch
from typing import List
from sentence_transformers import SentenceTransformer
from agent.models.types import Review, ReviewEmbedding
from agent.processing.pii_scrubber import scrub_pii

# Load the model lazily
_model = None

def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        # Use BAAI/bge-small-en-v1.5 as requested by user
        _model = SentenceTransformer('BAAI/bge-small-en-v1.5')
    return _model

def generate_embeddings(reviews: List[Review]) -> List[ReviewEmbedding]:
    if not reviews:
        return []
        
    model = get_model()
    
    # Clean and scrub reviews before embedding
    # We scrub PII so personal info doesn't influence the embedding clusters
    texts = [scrub_pii(r.text).strip().lower() for r in reviews]
    
    # Encode all texts at once
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    
    review_embeddings = []
    for review, vec in zip(reviews, embeddings):
        review_embeddings.append(ReviewEmbedding(
            review=review,
            vector=vec.tolist()
        ))
        
    return review_embeddings
