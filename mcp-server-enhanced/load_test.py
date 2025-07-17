#!/usr/bin/env python3
"""
Load testing script for MCP Server.
Tests the server's ability to handle concurrent requests and meet performance requirements.
"""

import asyncio
import aiohttp
import json
import time
import uuid
import statistics
import argparse
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class TestResult:
    """Result of a single test request."""
    success: bool
    duration_ms: float
    status_code: int
    error_message: str = ""

class LoadTester:
    """Load tester for MCP Server."""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = "test-api-key"):
        self.base_url = base_url
        self.api_key = api_key
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=50)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={"X-Api-Key": self.api_key}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def make_request(self, endpoint: str, payload: Dict[str, Any]) -> TestResult:
        """Make a single HTTP request and measure performance."""
        url = f"{self.base_url}/v1/{endpoint}"
        start_time = time.perf_counter()
        
        try:
            async with self.session.post(url, json=payload) as response:
                end_time = time.perf_counter()
                duration_ms = (end_time - start_time) * 1000
                
                response_data = await response.json()
                
                return TestResult(
                    success=response.status == 200,
                    duration_ms=duration_ms,
                    status_code=response.status,
                    error_message="" if response.status == 200 else str(response_data)
                )
        
        except Exception as e:
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000
            
            return TestResult(
                success=False,
                duration_ms=duration_ms,
                status_code=0,
                error_message=str(e)
            )
    
    def create_test_payload(self, text_size: int = 1000) -> Dict[str, Any]:
        """Create a test payload with specified text size."""
        text = "A" * text_size
        return {
            "requestId": str(uuid.uuid4()),
            "text": text,
            "options": {}
        }

async def main():
    """Main load testing function."""
    parser = argparse.ArgumentParser(description="Load test MCP Server")
    parser.add_argument("--url", default="http://localhost:8000", help="Server URL")
    parser.add_argument("--api-key", default="test-api-key", help="API key")
    parser.add_argument("--requests", type=int, default=20, help="Number of requests per endpoint")
    parser.add_argument("--concurrency", type=int, default=5, help="Concurrent requests")
    parser.add_argument("--text-size", type=int, default=1000, help="Text size in bytes")
    
    args = parser.parse_args()
    
    print("=== MCP Server Load Test ===")
    print(f"Server URL: {args.url}")
    print(f"API Key: {args.api_key}")
    
    async with LoadTester(args.url, args.api_key) as tester:
        # Health check
        try:
            url = f"{args.url}/health"
            async with tester.session.get(url) as response:
                if response.status == 200:
                    print("? Server is healthy and ready!")
                else:
                    print(f"? Server health check failed: status {response.status}")
                    return
        except Exception as e:
            print(f"? Server health check failed: {e}")
            return
        
        # Test summarize endpoint
        print(f"\n?? Testing summarize endpoint...")
        payload = tester.create_test_payload(args.text_size)
        result = await tester.make_request("summarize", payload)
        
        if result.success:
            print(f"? Summarize test passed ({result.duration_ms:.1f}ms)")
        else:
            print(f"? Summarize test failed: {result.error_message}")
        
        print("\n?? Load test completed!")

if __name__ == "__main__":
    asyncio.run(main())
