import numpy as np
import umap
import hdbscan
from typing import List
from agent.models.types import Review, ReviewEmbedding, Cluster
from agent.config import Config

def cluster_reviews(review_embeddings: List[ReviewEmbedding], config: Config) -> List[Cluster]:
    if not review_embeddings:
        return []
        
    total_reviews = len(review_embeddings)
    
    # ML Floor check
    if total_reviews < config.min_reviews_floor:
        return []
        
    # If we have very few reviews (but above floor), skip clustering and return 1 cluster
    if total_reviews < config.min_cluster_size:
        return [
            Cluster(
                cluster_id=0,
                reviews=[re.review for re in review_embeddings],
                centroid=[0.0] * len(review_embeddings[0].vector),
                size=total_reviews
            )
        ]
        
    vectors = np.array([re.vector for re in review_embeddings])
    
    # 1. Dimensionality reduction with UMAP
    n_neighbors = min(15, len(vectors) - 1)
    reducer = umap.UMAP(
        n_neighbors=n_neighbors,
        n_components=5,
        metric='cosine',
        random_state=42
    )
    reduced_embeddings = reducer.fit_transform(vectors)
    
    # 2. Density-based clustering with HDBSCAN
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=config.min_cluster_size,
        metric='euclidean',
        cluster_selection_method='eom'
    )
    labels = clusterer.fit_predict(reduced_embeddings)
    
    # 3. Group reviews by cluster
    clusters = []
    unique_labels = set(labels)
    
    for label in unique_labels:
        idx = np.where(labels == label)[0]
        cluster_vecs = vectors[idx]
        cluster_recs = [review_embeddings[i].review for i in idx]
        
        centroid = np.mean(cluster_vecs, axis=0).tolist()
        
        clusters.append(Cluster(
            cluster_id=int(label),
            reviews=cluster_recs,
            centroid=centroid,
            size=len(idx)
        ))
        
    # Fallback: Mega-cluster Check
    mega_threshold = int(total_reviews * config.mega_cluster_threshold)
    for c in clusters:
        if c.size >= mega_threshold:
            c.cluster_id = 9999 # denote mega cluster
            
    # Calculate explicit ranking formula: score = cluster_size * (6 - avg_rating)
    def cluster_score(c: Cluster) -> float:
        if not c.reviews:
            return 0.0
        avg_rating = sum(r.rating for r in c.reviews) / c.size
        # Penalize noise cluster (-1)
        if c.cluster_id == -1:
            return (c.size * (6 - avg_rating)) * 0.5 
        return c.size * (6 - avg_rating)
        
    # Sort clusters descending by score
    clusters.sort(key=cluster_score, reverse=True)
    
    return clusters
