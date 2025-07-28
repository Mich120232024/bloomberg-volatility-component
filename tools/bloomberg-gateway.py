#!/usr/bin/env python3
"""
Bloomberg Gateway API - Generic interface to Bloomberg Terminal
Provides flexible access to any Bloomberg data
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import requests
from datetime import datetime
import uvicorn
import json

app = FastAPI(title="Bloomberg Gateway", version="2.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Bloomberg VM API configuration
BLOOMBERG_API_URL = "http://20.172.249.92:8080"
DEFAULT_HEADERS = {
    'Authorization': 'Bearer test',
    'Content-Type': 'application/json'
}

class GenericRequest(BaseModel):
    """Generic request that can handle any Bloomberg query"""
    securities: List[str]
    fields: List[str]
    # Optional parameters for specific request types
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    periodicity: Optional[str] = "DAILY"
    
    class Config:
        extra = "allow"  # Allow additional fields

@app.get("/")
async def root():
    return {
        "name": "Bloomberg Gateway API",
        "version": "2.0.0",
        "description": "Generic gateway to Bloomberg Terminal data",
        "endpoints": {
            "/query": "Generic query endpoint - send any securities and fields",
            "/batch": "Batch multiple queries in one request",
            "/explore/{pattern}": "Explore tickers matching a pattern",
            "/health": "Check Bloomberg API health",
            "/docs": "Interactive API documentation"
        },
        "bloomberg_api": BLOOMBERG_API_URL
    }

@app.get("/health")
async def health_check():
    """Check Bloomberg API health and capabilities"""
    try:
        response = requests.get(
            f"{BLOOMBERG_API_URL}/health", 
            headers=DEFAULT_HEADERS,
            timeout=5
        )
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Bloomberg API unavailable: {str(e)}")

@app.post("/query")
async def generic_query(request: GenericRequest):
    """
    Generic endpoint to query any Bloomberg data
    
    Examples:
    - Real-time: {"securities": ["EURUSD Curncy"], "fields": ["PX_LAST"]}
    - Volatility: {"securities": ["EURUSDV1M BGN Curncy"], "fields": ["PX_BID", "PX_ASK"]}
    - Historical: Add start_date and end_date in YYYYMMDD format
    """
    
    # Determine if this is a historical or reference query
    if request.start_date and request.end_date:
        # Historical query - process one security at a time
        all_results = []
        
        for security in request.securities:
            try:
                response = requests.post(
                    f"{BLOOMBERG_API_URL}/api/bloomberg/historical",
                    headers=DEFAULT_HEADERS,
                    json={
                        "security": security,
                        "fields": request.fields,
                        "start_date": request.start_date,
                        "end_date": request.end_date,
                        "periodicity": request.periodicity
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    all_results.append(response.json())
                else:
                    all_results.append({
                        "security": security,
                        "error": f"HTTP {response.status_code}",
                        "details": response.text
                    })
                    
            except Exception as e:
                all_results.append({
                    "security": security,
                    "error": str(e)
                })
        
        return {
            "query_type": "historical",
            "results": all_results,
            "timestamp": datetime.now().isoformat()
        }
    
    else:
        # Reference/real-time query
        try:
            response = requests.post(
                f"{BLOOMBERG_API_URL}/api/bloomberg/reference",
                headers=DEFAULT_HEADERS,
                json={
                    "securities": request.securities,
                    "fields": request.fields
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    "query_type": "reference",
                    "results": response.json(),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Bloomberg API error: {response.text}"
                )
                
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=503, detail=f"Request failed: {str(e)}")

@app.post("/batch")
async def batch_queries(queries: List[GenericRequest]):
    """Execute multiple queries in a single request"""
    results = []
    
    for i, query in enumerate(queries):
        try:
            result = await generic_query(query)
            results.append({
                "query_index": i,
                "status": "success",
                "data": result
            })
        except Exception as e:
            results.append({
                "query_index": i,
                "status": "error",
                "error": str(e)
            })
    
    return {
        "total_queries": len(queries),
        "successful": sum(1 for r in results if r["status"] == "success"),
        "failed": sum(1 for r in results if r["status"] == "error"),
        "results": results,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/explore/{pattern}")
async def explore_tickers(
    pattern: str,
    asset_class: Optional[str] = "FX",
    max_results: int = 50
):
    """
    Explore Bloomberg tickers matching a pattern
    
    Examples:
    - /explore/EURUSD - Find all EURUSD related tickers
    - /explore/V1M - Find all 1-month volatility tickers
    """
    
    # Build common ticker patterns based on asset class
    tickers = []
    
    if asset_class.upper() == "FX":
        # FX patterns
        if len(pattern) == 6 and pattern.isalpha():  # Currency pair like EURUSD
            # Spot
            tickers.append(f"{pattern} Curncy")
            
            # Common tenors
            tenors = ["ON", "1W", "2W", "1M", "2M", "3M", "6M", "9M", "1Y", "2Y"]
            
            # Volatilities
            for tenor in tenors:
                if tenor == "ON":
                    tickers.append(f"{pattern}V{tenor} Curncy")
                else:
                    tickers.append(f"{pattern}V{tenor} BGN Curncy")
            
            # Risk Reversals and Butterflies (common deltas)
            deltas = [5, 10, 15, 25, 35]
            for tenor in tenors[1:]:  # Skip ON
                for delta in deltas:
                    tickers.append(f"{pattern}{delta}R{tenor} BGN Curncy")
                    tickers.append(f"{pattern}{delta}B{tenor} BGN Curncy")
        
        elif "V" in pattern.upper():  # Volatility pattern
            # Extract components if possible
            parts = pattern.upper().split("V")
            if len(parts) == 2:
                pair = parts[0]
                tenor = parts[1]
                if tenor == "ON":
                    tickers.append(f"{pair}V{tenor} Curncy")
                else:
                    tickers.append(f"{pair}V{tenor} BGN Curncy")
    
    # Check which tickers are valid
    if tickers:
        # Check in batches
        valid_tickers = []
        batch_size = 20
        
        for i in range(0, min(len(tickers), max_results), batch_size):
            batch = tickers[i:i+batch_size]
            
            try:
                response = requests.post(
                    f"{BLOOMBERG_API_URL}/api/bloomberg/reference",
                    headers=DEFAULT_HEADERS,
                    json={
                        "securities": batch,
                        "fields": ["PX_LAST"]
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success') and 'data' in data:
                        for sec in data['data'].get('securities_data', []):
                            if sec.get('success'):
                                valid_tickers.append({
                                    "ticker": sec['security'],
                                    "has_data": sec.get('fields', {}).get('PX_LAST') is not None
                                })
            except:
                pass
        
        return {
            "pattern": pattern,
            "asset_class": asset_class,
            "tickers_checked": len(tickers[:max_results]),
            "valid_tickers": len(valid_tickers),
            "results": valid_tickers
        }
    
    return {
        "pattern": pattern,
        "asset_class": asset_class,
        "message": "No tickers generated for this pattern",
        "hint": "Try patterns like 'EURUSD', 'GBPUSD', or 'EURUSDV1M'"
    }

@app.post("/raw")
async def raw_proxy(request: Request):
    """
    Raw proxy to Bloomberg API - pass through any request
    Useful for direct Bloomberg API access
    """
    body = await request.json()
    path = request.url.path.replace("/raw", "")
    
    # Forward to Bloomberg API
    try:
        response = requests.request(
            method=request.method,
            url=f"{BLOOMBERG_API_URL}{path}",
            headers=DEFAULT_HEADERS,
            json=body,
            timeout=30
        )
        
        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Proxy error: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting Bloomberg Gateway on http://localhost:8000")
    print("📚 Interactive API docs: http://localhost:8000/docs")
    print("🔧 Generic query endpoint: POST http://localhost:8000/query")
    uvicorn.run(app, host="0.0.0.0", port=8000)