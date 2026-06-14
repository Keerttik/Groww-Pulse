import pytest
import json
import os
from agent.config import load_config

def test_load_valid_config(tmp_path):
    config_file = tmp_path / "config.json"
    data = {
        "product": {
            "id": "groww",
            "play_store_app_id": "com.nextbillion.groww",
            "google_doc_id": "doc123"
        }
    }
    with open(config_file, "w") as f:
        json.dump(data, f)
    
    config = load_config(str(config_file))
    assert config.product.id == "groww"
    assert config.product.play_store_app_id == "com.nextbillion.groww"
    assert config.product.google_doc_id == "doc123"

def test_load_missing_fields(tmp_path):
    config_file = tmp_path / "config.json"
    data = {"product": {"id": "groww"}}
    with open(config_file, "w") as f:
        json.dump(data, f)
    
    with pytest.raises(ValueError, match="Missing 'play_store_app_id'"):
        load_config(str(config_file))

def test_load_malformed_config(tmp_path):
    config_file = tmp_path / "config.json"
    with open(config_file, "w") as f:
        f.write("{ invalid json")
    
    with pytest.raises(json.JSONDecodeError):
        load_config(str(config_file))
