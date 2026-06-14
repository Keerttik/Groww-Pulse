import httpx
import logging
from agent.rendering.models import DocContent
from agent.delivery.models import DeliveryResult

logger = logging.getLogger(__name__)

async def append_section_to_doc(doc_id: str, content: DocContent, rest_server_url: str, secret_key: str | None = None) -> DeliveryResult:
    """
    Appends a formatted text block to a Google Doc via the external REST API.
    Since the REST API currently doesn't support reading to check for the anchor_id,
    idempotency is deferred to the SQLite run record level (Orchestrator).
    """
    url = f"{rest_server_url.rstrip('/')}/append_to_doc"
    payload = {
        "doc_id": doc_id,
        "content": content.plain_text
    }
    
    headers = {}
    if secret_key:
        headers["Authorization"] = f"Bearer {secret_key}"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=30.0)
            response.raise_for_status()
            
            return DeliveryResult(status="appended", anchor=content.anchor_id)
            
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error {e.response.status_code} while appending to doc: {e.response.text}")
        return DeliveryResult(status="error", anchor=content.anchor_id)
    except Exception as e:
        logger.error(f"Error appending to doc: {str(e)}")
        return DeliveryResult(status="error", anchor=content.anchor_id)
