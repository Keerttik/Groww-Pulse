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
        err = f"HTTP error {e.response.status_code} while creating email draft: {e.response.text}"
        logger.error(err)
        return EmailDeliveryResult(status="error", error_message=err)
    except Exception as e:
        err = f"Error creating email draft: {str(e)}"
        logger.error(err)
        return EmailDeliveryResult(status="error", error_message=err)


async def send_email(
    email: EmailContent,
    recipients: List[str],
    rest_server_url: str,
    secret_key: str | None = None
) -> EmailDeliveryResult:
    """
    Sends an email via Gmail via the external REST API.
    Falls back to create_email_draft if send_email endpoint is not yet supported.
    """
    url = f"{rest_server_url.rstrip('/')}/send_email"
    
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
            if response.status_code == 404:
                logger.warning("/send_email endpoint not found on REST server. Falling back to creating a draft.")
                return await create_email_draft(email, recipients, rest_server_url, secret_key)
            response.raise_for_status()
            
            data = response.json() if response.text else {}
            message_id = data.get("message_id")
            
            return EmailDeliveryResult(status="sent", message_id=message_id)
            
    except httpx.HTTPStatusError as e:
        err = f"HTTP error {e.response.status_code} while sending email: {e.response.text}"
        logger.error(err)
        return EmailDeliveryResult(status="error", error_message=err)
    except Exception as e:
        err = f"Error sending email: {str(e)}"
        logger.error(err)
        return EmailDeliveryResult(status="error", error_message=err)
