import asyncio
import json
import logging
import time
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from fastapi import FastAPI, HTTPException, Header, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MAX_TEXT_SIZE = 10 * 1024 * 1024  # 10MB
API_VERSION = "v1"

# Pydantic Models
class RequestModel(BaseModel):
    requestId: str = Field(..., description="UUID for tracing")
    text: str = Field(..., max_length=MAX_TEXT_SIZE, description="Text to process (up to 10MB)")
    options: Dict[str, Any] = Field(default_factory=dict, description="Tool-specific options")
    
    @field_validator('requestId')
    def validate_request_id(cls, v):
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError('requestId must be a valid UUID')

class ResponseModel(BaseModel):
    requestId: str
    tool: str
    durationMs: int
    result: Dict[str, Any]

class ErrorResponse(BaseModel):
    requestId: str
    error: Dict[str, str]

class HealthResponse(BaseModel):
    status: str = "healthy"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

# Mock NLP implementations
class MockNLPProcessor:
    @staticmethod
    async def summarize(text: str, max_sentences: int = 3) -> str:
        sentences = text.split('.')[:max_sentences]
        return '. '.join(sentences).strip() + ('.' if sentences else '')
    
    @staticmethod
    async def extract_keywords(text: str, top_n: int = 10) -> List[Dict[str, Any]]:
        words = text.lower().split()
        word_freq = {}
        for word in words:
            word = word.strip('.,!?;:"()[]{}')
            if len(word) > 3:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:top_n]
        return [{"term": word, "score": freq / len(words)} for word, freq in sorted_words]
    
    @staticmethod
    async def analyze_sentiment(text: str) -> str:
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'love']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'disappointing']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"

# FastAPI app
app = FastAPI(
    title="MCP Server",
    description="Model Context Protocol Server for text processing",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

VALID_API_KEYS = {"test-api-key", "development-key"}

def validate_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    if not x_api_key or x_api_key not in VALID_API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return x_api_key

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info(
        f"{request.method} {request.url} - "
        f"Status: {response.status_code} - "
        f"Duration: {process_time:.3f}s"
    )
    return response

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "requestId": request_id,
            "error": {
                "code": str(exc.status_code),
                "message": exc.detail
            }
        }
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse()

async def process_request(request_data: RequestModel, tool_name: str, processor_func, api_key: str) -> ResponseModel:
    start_time = time.time()
    
    text_size = len(request_data.text.encode('utf-8'))
    if text_size > MAX_TEXT_SIZE:
        raise HTTPException(status_code=413, detail=f"Text size {text_size} exceeds maximum {MAX_TEXT_SIZE}")
    
    logger.info(f"Processing {tool_name} request {request_data.requestId} - Text size: {text_size} bytes")
    
    try:
        result = await processor_func(request_data.text, request_data.options)
        duration_ms = int((time.time() - start_time) * 1000)
        
        response = ResponseModel(
            requestId=request_data.requestId,
            tool=tool_name,
            durationMs=duration_ms,
            result=result
        )
        
        logger.info(f"Completed {tool_name} request {request_data.requestId} in {duration_ms}ms")
        return response
        
    except Exception as e:
        logger.error(f"Error processing {tool_name} request {request_data.requestId}: {e}")
        raise HTTPException(status_code=500, detail="Processing failed")

@app.post(f"/{API_VERSION}/summarize", response_model=ResponseModel)
async def summarize_endpoint(request_data: RequestModel, api_key: str = Depends(validate_api_key)):
    async def process(text: str, options: Dict[str, Any]) -> Dict[str, Any]:
        max_sentences = options.get('maxSentences', 3)
        summary = await MockNLPProcessor.summarize(text, max_sentences)
        return {"summary": summary}
    
    return await process_request(request_data, "Summarize", process, api_key)

@app.post(f"/{API_VERSION}/keywords", response_model=ResponseModel)
async def extract_keywords_endpoint(request_data: RequestModel, api_key: str = Depends(validate_api_key)):
    async def process(text: str, options: Dict[str, Any]) -> Dict[str, Any]:
        top_n = options.get('topN', 10)
        keywords = await MockNLPProcessor.extract_keywords(text, top_n)
        return {"keywords": keywords}
    
    return await process_request(request_data, "ExtractKeywords", process, api_key)

@app.post(f"/{API_VERSION}/sentiment", response_model=ResponseModel)
async def sentiment_endpoint(request_data: RequestModel, api_key: str = Depends(validate_api_key)):
    async def process(text: str, options: Dict[str, Any]) -> Dict[str, Any]:
        sentiment = await MockNLPProcessor.analyze_sentiment(text)
        return {"label": sentiment}
    
    return await process_request(request_data, "Sentiment", process, api_key)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")

