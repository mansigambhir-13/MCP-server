# MCP Server - Model Context Protocol Server

A high-performance HTTP-based server implementing the Model Context Protocol (MCP) for text processing operations.

## Overview
This server provides three NLP processing endpoints:
- **Summarize**: Generate concise summaries of large text
- **Extract Keywords**: Identify important keywords with relevance scores  
- **Sentiment Analysis**: Classify text sentiment as positive, negative, or neutral

- ## workflow
- <img width="2052" height="2565" alt="_- visual selection" src="https://github.com/user-attachments/assets/fc405cc8-03e6-4fe7-a6b4-785f14ad09f0" />


## Quick Start

### 1. Setup Environment
pip install -r requirements.txt

### 2. Run Server
python main.py

### 3. Test API
# Health check
curl http://localhost:8000/health

## API Endpoints

### Authentication
All requests require an API key in the header: X-Api-Key: test-api-key

### Available Endpoints
- GET /health - Returns server health status
- POST /v1/summarize - Generate text summary
- POST /v1/keywords - Extract important keywords
- POST /v1/sentiment - Analyze text sentiment

## PowerShell Testing Examples
$headers = @{"Content-Type" = "application/json"; "X-Api-Key" = "test-api-key"}
$body = @{requestId = [System.Guid]::NewGuid().ToString(); text = "Your text here"; options = @{}} | ConvertTo-Json
Invoke-RestMethod -Uri http://localhost:8000/v1/summarize -Method Post -Headers $headers -Body $body

## Performance
- Latency: ≤500ms for texts ≤1MB (typically <100ms)
- Concurrency: Supports ≥10 simultaneous connections
- Text Limit: 10MB maximum per request

## Features
✅ Three NLP endpoints (Summarize, Keywords, Sentiment)  
✅ HTTP REST API with proper versioning  
✅ API key authentication  
✅ Request tracing with UUIDs  
✅ Input validation (UUID format checking)
✅ Performance ≤500ms requirement  
✅ Comprehensive error handling  
✅ Production-ready deployment  

## Testing
pytest test_main.py -v

## Docker
docker build -t mcp-server .
docker run -p 8000:8000 mcp-server
