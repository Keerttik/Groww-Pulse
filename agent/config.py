import json
import os
import yaml
from dataclasses import dataclass, field
from typing import List

@dataclass
class ProductConfig:
    id: str
    play_store_app_id: str
    display_name: str
    google_doc_id: str
    stakeholder_emails: List[str]

@dataclass
class ClusteringConfig:
    umap_n_components: int = 5
    hdbscan_min_cluster_size: int = 10

@dataclass
class LLMConfig:
    model: str = "gemini-2.0-flash"
    max_input_tokens: int = 50000
    max_output_tokens: int = 4000
    temperature: float = 0.3

@dataclass
class DeliveryConfig:
    email_mode: str = "draft"
    email_from_name: str = "Review Pulse Bot"
    rest_server_url: str = "http://localhost:8000"
    mcp_api_secret_key: str | None = None

@dataclass
class Config:
    product: ProductConfig
    review_window_weeks: int = 12
    max_reviews: int = 500
    throttle_ms: int = 1000
    min_cluster_size: int = 10
    
    # LLM and Pipeline config
    max_tokens_per_run: int = 12000
    request_interval_seconds: int = 2
    sample_size_per_cluster: int = 5
    max_retries_429: int = 3
    min_reviews_floor: int = 20
    mega_cluster_threshold: float = 0.8
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    clustering: ClusteringConfig = field(default_factory=ClusteringConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    delivery: DeliveryConfig = field(default_factory=DeliveryConfig)
    run_records_dir: str = "data/run_records"

def load_config(path: str = "config.json") -> Config:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    product_data = data.get("product")
    if not product_data:
        raise ValueError("Missing 'product' configuration")
    
    if "play_store_app_id" not in product_data:
        raise ValueError("Missing 'play_store_app_id' in product config")
    
    # Support reading GOOGLE_DOC_ID from environment to override config.json
    doc_id = os.getenv("GOOGLE_DOC_ID", product_data.get("google_doc_id"))
    if not doc_id or doc_id == "<GOOGLE_DOC_ID>":
        raise ValueError("Missing or placeholder 'google_doc_id' in product config and environment")

    product = ProductConfig(
        id=product_data.get("id", "groww"),
        play_store_app_id=product_data["play_store_app_id"],
        display_name=product_data.get("display_name", "Groww"),
        google_doc_id=doc_id,
        stakeholder_emails=product_data.get("stakeholder_emails", [])
    )

    clustering_data = data.get("clustering", {})
    clustering = ClusteringConfig(**clustering_data)

    llm_data = data.get("llm", {})
    llm = LLMConfig(**llm_data)

    delivery_data = data.get("delivery", {})
    if "mcp_api_secret_key" not in delivery_data:
        delivery_data["mcp_api_secret_key"] = os.getenv("MCP_API_SECRET_KEY")
    delivery = DeliveryConfig(**delivery_data)

    # Load YAML if exists
    yaml_path = os.path.join(os.path.dirname(path), "config", "pipeline.yaml")
    pipeline_data = {}
    if os.path.exists(yaml_path):
        with open(yaml_path, "r", encoding="utf-8") as f:
            pipeline_data = yaml.safe_load(f) or {}

    llm_cfg = pipeline_data.get("llm", {})
    clust_cfg = pipeline_data.get("clustering", {})

    return Config(
        product=product,
        review_window_weeks=data.get("review_window_weeks", 12),
        max_reviews=data.get("max_reviews", 500),
        throttle_ms=data.get("throttle_ms", 1000),
        min_cluster_size=data.get("min_cluster_size", 10),
        max_tokens_per_run=llm_cfg.get("max_tokens_per_run", 12000),
        request_interval_seconds=llm_cfg.get("request_interval_seconds", 2),
        sample_size_per_cluster=llm_cfg.get("sample_size_per_cluster", 5),
        max_retries_429=llm_cfg.get("max_retries_429", 3),
        min_reviews_floor=clust_cfg.get("min_reviews_floor", 20),
        mega_cluster_threshold=clust_cfg.get("mega_cluster_threshold", 0.8),
        embedding_model=data.get("embedding_model", "BAAI/bge-small-en-v1.5"),
        clustering=clustering,
        llm=llm,
        delivery=delivery,
        run_records_dir=data.get("run_records_dir", "data/run_records")
    )
