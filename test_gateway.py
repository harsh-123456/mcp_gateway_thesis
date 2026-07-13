import pytest
import warnings
from fastapi.testclient import TestClient
from mcp_gateway import app

# Suppress FastAPI deprecation warnings for a perfectly clean terminal output
warnings.filterwarnings("ignore", category=DeprecationWarning)

# ---------------------------------------------------------
# AUTOMATED SECURITY TEST SUITE FOR MCP GATEWAY
# ---------------------------------------------------------

def test_allowed_request():
    """
    Scenario 1: Authorized Access
    Verify that a valid role ('internal_auditor') requesting a 
    safe payload ('config.yaml') successfully passes through.
    """
    # The 'with' block forces FastAPI to run startup events (metrics/logging)
    with TestClient(app) as client:
        response = client.post(
            "/mcp/v1/tools/call",
            headers={"x-agent-role": "internal_auditor"},
            json={"name": "read_sensitive_file", "arguments": {"filename": "config.yaml"}}
        )
        assert response.status_code == 200

def test_blocked_role():
    """
    Scenario 2: Role-Based Access Control (RBAC) Enforcement
    Verify that an unauthorized role ('public_agent') is 
    immediately rejected by the gateway.
    """
    with TestClient(app) as client:
        response = client.post(
            "/mcp/v1/tools/call",
            headers={"x-agent-role": "public_agent"},
            json={"name": "read_sensitive_file", "arguments": {"filename": "config.yaml"}}
        )
        assert response.status_code == 403

def test_semantic_guardrail():
    """
    Scenario 3: Semantic Firewall Enforcement
    Verify that restricted data patterns ('master_key.pem') 
    trigger the firewall even for authorized roles.
    """
    with TestClient(app) as client:
        response = client.post(
            "/mcp/v1/tools/call",
            headers={"x-agent-role": "internal_auditor"},
            json={"name": "read_sensitive_file", "arguments": {"filename": "master_key.pem"}}
        )
        assert response.status_code == 403