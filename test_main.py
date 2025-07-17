import pytest
import uuid
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
VALID_API_KEY = "test-api-key"

def create_request_payload(text: str, options: dict = None) -> dict:
    return {
        "requestId": str(uuid.uuid4()),
        "text": text,
        "options": options or {}
    }

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_summarize_endpoint():
    payload = create_request_payload("This is a test. It has multiple sentences.", {"maxSentences": 1})
    headers = {"X-Api-Key": VALID_API_KEY}
    
    response = client.post("/v1/summarize", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["tool"] == "Summarize"
    assert "summary" in data["result"]

def test_keywords_endpoint():
    payload = create_request_payload("machine learning artificial intelligence", {"topN": 2})
    headers = {"X-Api-Key": VALID_API_KEY}
    
    response = client.post("/v1/keywords", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["tool"] == "ExtractKeywords"
    assert "keywords" in data["result"]

def test_sentiment_endpoint():
    payload = create_request_payload("I love this amazing product!")
    headers = {"X-Api-Key": VALID_API_KEY}
    
    response = client.post("/v1/sentiment", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["tool"] == "Sentiment"
    assert "label" in data["result"]
