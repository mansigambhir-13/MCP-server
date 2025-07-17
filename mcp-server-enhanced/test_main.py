import pytest
import asyncio
import uuid
import json
from fastapi.testclient import TestClient
from main import app

# Test client
client = TestClient(app)

# Valid API key for testing
VALID_API_KEY = "test-api-key"
INVALID_API_KEY = "invalid-key"

# Test data
SAMPLE_TEXT = "This is a sample text for testing. It contains multiple sentences. Each sentence provides different information about the testing process."
LARGE_TEXT = "A" * 1000  # 1KB text
VERY_LARGE_TEXT = "B" * (11 * 1024 * 1024)  # 11MB text (exceeds limit)

def create_request_payload(text: str, options: dict = None) -> dict:
    """Helper function to create request payload."""
    return {
        "requestId": str(uuid.uuid4()),
        "text": text,
        "options": options or {}
    }

class TestHealthEndpoint:
    """Test the health endpoint."""
    
    def test_health_check_success(self):
        """Test successful health check."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

class TestAuthentication:
    """Test API key authentication."""
    
    def test_missing_api_key(self):
        """Test request without API key."""
        payload = create_request_payload(SAMPLE_TEXT)
        response = client.post("/v1/summarize", json=payload)
        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "401"
    
    def test_invalid_api_key(self):
        """Test request with invalid API key."""
        payload = create_request_payload(SAMPLE_TEXT)
        headers = {"X-Api-Key": INVALID_API_KEY}
        response = client.post("/v1/summarize", json=payload, headers=headers)
        assert response.status_code == 401
    
    def test_valid_api_key(self):
        """Test request with valid API key."""
        payload = create_request_payload(SAMPLE_TEXT)
        headers = {"X-Api-Key": VALID_API_KEY}
        response = client.post("/v1/summarize", json=payload, headers=headers)
        assert response.status_code == 200

class TestSummarizeEndpoint:
    """Test the summarize endpoint."""
    
    def test_summarize_success(self):
        """Test successful text summarization."""
        payload = create_request_payload(SAMPLE_TEXT, {"maxSentences": 2})
        headers = {"X-Api-Key": VALID_API_KEY}
        
        response = client.post("/v1/summarize", json=payload, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["requestId"] == payload["requestId"]
        assert data["tool"] == "Summarize"
        assert "durationMs" in data
        assert "result" in data
        assert "summary" in data["result"]
        assert isinstance(data["result"]["summary"], str)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
