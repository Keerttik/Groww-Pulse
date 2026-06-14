from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from agent.api import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@patch("agent.api.list_records")
@patch("agent.api.load_config")
def test_get_runs(mock_config, mock_list):
    mock_conf = MagicMock()
    mock_conf.product.id = "groww"
    mock_config.return_value = mock_conf
    
    mock_record = MagicMock()
    mock_record.to_dict.return_value = {"run_id": "123", "status": "success"}
    mock_list.return_value = [mock_record]
    
    response = client.get("/api/runs")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["run_id"] == "123"

@patch("agent.api.run_pulse")
def test_start_pulse(mock_run_pulse):
    response = client.post("/api/runs/start", json={"week": "2026-W25"})
    assert response.status_code == 200
    assert "triggered in the background" in response.json()["message"]
    # The BackgroundTask should call the mocked run_pulse eventually, 
    # FastAPI's TestClient executes background tasks inline.
    mock_run_pulse.assert_called_once_with("2026-W25", False, "draft")
