import pytest
import json
from agent.ingestion.ingestion import fetch_reviews
from agent.models.types import Review
from agent.config import Config, ProductConfig

class MockContent:
    def __init__(self, text):
        self.text = text

class MockResult:
    def __init__(self, text):
        self.content = [MockContent(text)]

class MockSession:
    async def call_tool(self, name, args):
        if name == "fetch_reviews":
            data = {
                "reviews": [
                    {
                        "rating": 5,
                        "text": "test test test test test test test test",
                        "thumbs_up": 0
                    }
                ]
            }
            return MockResult(json.dumps(data))
        return MockResult("{}")

@pytest.fixture
def mock_config():
    product = ProductConfig(
        id="groww", play_store_app_id="com.mock",
        display_name="Mock", google_doc_id="mock",
        stakeholder_emails=[]
    )
    return Config(product=product, review_window_weeks=10)

@pytest.mark.asyncio
async def test_fetch_reviews(mock_config):
    session = MockSession()
    reviews = await fetch_reviews(session, mock_config)
    assert len(reviews) == 1
    assert reviews[0].rating == 5
