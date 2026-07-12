import pytest
from fastapi.testclient import TestClient
from mcp_gateway import app

client = TestClient(app)

def test_allowed_request():
    """Verify that a valid role and safe payload pass through."""
    response = client.post(
        "/mcp/v1/tools/call",
        json={"role": "analyst", "payload": "Analyze public trends."}
    )
    assert response.status_code == 200

def test_blocked_role():
    """Verify that an unauthorized role is immediately rejected."""
    response = client.post(
        "/mcp/v1/tools/call",
        json={"role": "guest", "payload": "Analyze public trends."}
    )
    assert response.status_code == 403

def test_semantic_guardrail():
    """Verify that restricted data triggers the firewall."""
    response = client.post(
        "/mcp/v1/tools/call",
        json={"role": "analyst", "payload": "Extract Enterprise Data."}
    )
    assert response.status_code == 403