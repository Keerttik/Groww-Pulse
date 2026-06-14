import pytest
import httpx
from agent.rendering.models import DocContent
from agent.delivery.models import DeliveryResult
from agent.delivery.docs_delivery import append_section_to_doc

@pytest.mark.asyncio
async def test_append_section_to_doc_success(httpx_mock):
    rest_server_url = "https://mcp-production-9791.up.railway.app"
    doc_id = "test_doc_id"
    content = DocContent(anchor_id="test-anchor-1", plain_text="== Heading ==\nSome content.")
    
    # Mock the POST request
    httpx_mock.add_response(
        method="POST",
        url=f"{rest_server_url}/append_to_doc",
        json={"status": "success"}
    )
    
    result = await append_section_to_doc(doc_id, content, rest_server_url)
    
    assert result.status == "appended"
    assert result.anchor == "test-anchor-1"

@pytest.mark.asyncio
async def test_append_section_to_doc_http_error(httpx_mock):
    rest_server_url = "https://mcp-production-9791.up.railway.app"
    doc_id = "test_doc_id"
    content = DocContent(anchor_id="test-anchor-1", plain_text="== Heading ==\nSome content.")
    
    # Mock an error response
    httpx_mock.add_response(
        method="POST",
        url=f"{rest_server_url}/append_to_doc",
        status_code=500,
        text="Internal Server Error"
    )
    
    result = await append_section_to_doc(doc_id, content, rest_server_url)
    
    assert result.status == "error"
    assert result.anchor == "test-anchor-1"

@pytest.mark.asyncio
async def test_append_section_to_doc_network_error(httpx_mock):
    rest_server_url = "https://mcp-production-9791.up.railway.app"
    doc_id = "test_doc_id"
    content = DocContent(anchor_id="test-anchor-1", plain_text="== Heading ==\nSome content.")
    
    # Mock a network error
    httpx_mock.add_exception(
        httpx.ConnectError("Connection refused"),
        method="POST",
        url=f"{rest_server_url}/append_to_doc"
    )
    
    result = await append_section_to_doc(doc_id, content, rest_server_url)
    
    assert result.status == "error"
    assert result.anchor == "test-anchor-1"
