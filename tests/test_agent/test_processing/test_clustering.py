import pytest
from agent.models.types import Review, ReviewEmbedding
from agent.processing.clustering import cluster_reviews
from agent.config import Config, ProductConfig

config = Config(product=ProductConfig(id="x", play_store_app_id="x", display_name="x", google_doc_id="x", stakeholder_emails=[]), min_cluster_size=5, min_reviews_floor=2)

def test_cluster_few_reviews():
    # If we have less than min_cluster_size (10), it should return a single cluster
    embeddings = [
        ReviewEmbedding(
            review=Review(rating=5, text=f"Review {i}", thumbs_up=0, app_version="1.0"),
            vector=[0.1] * 384
        ) for i in range(5)
    ]
    
    config.min_cluster_size = 10
    clusters = cluster_reviews(embeddings, config)
    assert len(clusters) == 1
    assert clusters[0].cluster_id == 0
    assert clusters[0].size == 5

def test_cluster_many_reviews():
    # Generate mock embeddings that clearly form two clusters
    embeddings = []
    # Cluster 1
    for i in range(15):
        embeddings.append(ReviewEmbedding(
            review=Review(rating=5, text=f"Cluster 1 Review {i}", thumbs_up=0, app_version="1.0"),
            vector=[1.0, 0.0] * 192
        ))
    # Cluster 2
    for i in range(15):
        embeddings.append(ReviewEmbedding(
            review=Review(rating=1, text=f"Cluster 2 Review {i}", thumbs_up=0, app_version="1.0"),
            vector=[0.0, 1.0] * 192
        ))
        
    config.min_cluster_size = 5
    clusters = cluster_reviews(embeddings, config)
    # HDBSCAN might find 2 clusters + noise, but it should definitely find >= 2
    assert len(clusters) >= 2
    total_size = sum(c.size for c in clusters)
    assert total_size == 30
