import pytest
from agent.models.types import Review
from agent.processing.embeddings import generate_embeddings

def test_generate_embeddings():
    reviews = [
        Review(rating=5, text="This is a great app for investing.", thumbs_up=0, app_version="1.0"),
        Review(rating=1, text="Terrible experience with customer support.", thumbs_up=0, app_version="1.0")
    ]
    
    embeddings = generate_embeddings(reviews)
    assert len(embeddings) == 2
    assert embeddings[0].review.rating == 5
    # sentence-transformers/all-MiniLM-L6-v2 produces 384-dimensional vectors
    assert len(embeddings[0].vector) == 384
