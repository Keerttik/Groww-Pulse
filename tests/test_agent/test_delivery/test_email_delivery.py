import pytest
import httpx
from agent.rendering.models import EmailContent
from agent.delivery.models import EmailDeliveryResult
from agent.delivery.email_delivery import create_email_draft

@pytest.mark.asyncio
async def test_create_email_draft_success(httpx_mock):
    rest_server_url = "https://mcp-production-9791.up.railway.app"
    recipients = ["test@example.com", "stakeholder@example.com"]
    email = EmailContent(subject="Test Subject", html_body="<p>Body</p>", text_body="Body")
    
    # Mock the POST request
    httpx_mock.add_response(
        method="POST",
        url=f"{rest_server_url}/create_email_draft",
        json={"draft_id": "draft_12345"}
    )
    
    result = await create_email_draft(email, recipients, rest_server_url)
    
    assert result.status == "drafted"
    assert result.draft_id == "draft_12345"

@pytest.mark.asyncio
async def test_create_email_draft_http_error(httpx_mock):
    rest_server_url = "https://mcp-production-9791.up.railway.app"
    recipients = ["test@example.com"]
    email = EmailContent(subject="Test Subject", html_body="<p>Body</p>", text_body="Body")
    
    # Mock an error response
    httpx_mock.add_response(
        method="POST",
        url=f"{rest_server_url}/create_email_draft",
        status_code=403,
        text="Action denied by operator."
    )
    
    result = await create_email_draft(email, recipients, rest_server_url)
    
    assert result.status == "error"

@pytest.mark.asyncio
async def test_create_email_draft_network_error(httpx_mock):
    rest_server_url = "https://mcp-production-9791.up.railway.app"
    recipients = ["test@example.com"]
    email = EmailContent(subject="Test Subject", html_body="<p>Body</p>", text_body="Body")
    
    # Mock a network error
    httpx_mock.add_exception(
        httpx.ConnectError("Connection refused"),
        method="POST",
        url=f"{rest_server_url}/create_email_draft"
    )
    
    result = await create_email_draft(email, recipients, rest_server_url)
    
    assert result.status == "error"
