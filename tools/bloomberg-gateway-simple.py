#!/usr/bin/env python3
"""
Simple Bloomberg Gateway - Minimal proxy to Bloomberg VM API
Just passes through requests with proper structure
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import httpx
import asyncio
from datetime import datetime
import os

app = FastAPI(title="Bloomberg Gateway", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Local development
        "http://localhost:3000",  # Alternative dev port
        "http://62.171.108.4",   # Whitelisted production IP
        "https://62.171.108.4"   # HTTPS variant
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Bloomberg VM API
BLOOMBERG_API_URL = "http://20.172.249.92:8080"
http_client = httpx.AsyncClient(timeout=30.0)

class BloombergRequest(BaseModel):
    securities: List[str]
    fields: List[str]

@app.get("/")
async def root():
    return {
        "name": "Bloomberg Gateway",
        "version": "1.0.0",
        "bloomberg_api": BLOOMBERG_API_URL,
        "status": "running"
    }

@app.get("/health")
async def health():
    """Proxy health check to Bloomberg API"""
    try:
        response = await http_client.get(f"{BLOOMBERG_API_URL}/health")
        return response.json()
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "data": {"api_status": "error"}
        }

@app.post("/api/bloomberg/reference")
async def bloomberg_reference(request: BloombergRequest):
    """Direct proxy to Bloomberg reference endpoint"""
    try:
        response = await http_client.post(
            f"{BLOOMBERG_API_URL}/api/bloomberg/reference",
            json=request.dict(),
            headers={"Authorization": "Bearer test"}
        )
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@app.post("/api/bloomberg/historical")
async def bloomberg_historical(request: Dict[str, Any]):
    """Direct proxy to Bloomberg historical endpoint"""
    try:
        response = await http_client.post(
            f"{BLOOMBERG_API_URL}/api/bloomberg/historical",
            json=request,
            headers={"Authorization": "Bearer test"}
        )
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@app.on_event("shutdown")
async def shutdown():
    await http_client.aclose()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)