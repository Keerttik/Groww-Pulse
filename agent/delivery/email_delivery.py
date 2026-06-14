import httpx
import logging
from typing import List
from agent.rendering.models import EmailContent
from agent.delivery.models import EmailDeliveryResult

logger = logging.getLogger(__name__)

async def create_email_draft(
    email: EmailContent, 
    recipients: List[str], 
    rest_server_url: str, 
    secret_key: str | None = None
) -> EmailDeliveryResult:
    """
    Creates an email draft in Gmail via the external REST API.
    """
    url = f"{rest_server_url.rstrip('/')}/create_email_draft"
    
    # The server expects 'to', 'subject', 'body'
    payload = {
        "to": ", ".join(recipients),
        "subject": email.subject,
        "body": email.html_body
    }
    
    headers = {}
    if secret_key:
        headers["Authorization"] = f"Bearer {secret_key}"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=30.0)
            response.raise_for_status()
            
            # Optionally parse the draft_id if the server returns it, e.g., {"draft_id": "..."}
            data = response.json() if response.text else {}
            draft_id = data.get("draft_id")
            
            return EmailDeliveryResult(status="drafted", draft_id=draft_id)
            
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error {e.response.status_code} while creating email draft: {e.response.text}")
        return EmailDeliveryResult(status="error")
    except Exception as e:
        logger.error(f"Error creating email draft: {str(e)}")
        return EmailDeliveryResult(status="error")
