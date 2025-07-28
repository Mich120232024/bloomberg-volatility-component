#!/usr/bin/env python3
"""
Local Bloomberg API Explorer
A FastAPI server that provides a convenient interface to explore Bloomberg data
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import requests
from datetime import datetime, timedelta
import uvicorn

app = FastAPI(title="Bloomberg Data Explorer", version="1.0.0")

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
HEADERS = {
    'Authorization': 'Bearer test',
    'Content-Type': 'application/json'
}

class SecurityRequest(BaseModel):
    securities: List[str]
    fields: List[str] = ["PX_LAST", "PX_BID", "PX_ASK"]

class HistoricalRequest(BaseModel):
    security: str
    fields: List[str] = ["PX_LAST", "PX_BID", "PX_ASK"]
    start_date: str  # YYYYMMDD format
    end_date: str    # YYYYMMDD format
    periodicity: str = "DAILY"

class VolatilitySurfaceRequest(BaseModel):
    currency_pair: str = "EURUSD"
    tenors: List[str] = ["ON", "1W", "1M", "3M", "6M", "1Y"]
    deltas: List[int] = [5, 10, 15, 25, 35]

@app.get("/")
async def root():
    return {
        "message": "Bloomberg Data Explorer API",
        "endpoints": {
            "/health": "Check Bloomberg API health",
            "/reference": "Get reference data for securities",
            "/historical": "Get historical time series",
            "/volatility-surface": "Get full volatility surface",
            "/discover-tickers": "Discover valid tickers for a currency pair"
        }
    }

@app.get("/health")
async def health_check():
    """Check if Bloomberg API is healthy"""
    try:
        response = requests.get(f"{BLOOMBERG_API_URL}/health", headers=HEADERS)
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reference")
async def get_reference_data(request: SecurityRequest):
    """Get reference data for securities"""
    try:
        response = requests.post(
            f"{BLOOMBERG_API_URL}/api/bloomberg/reference",
            headers=HEADERS,
            json=request.dict()
        )
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/historical")
async def get_historical_data(request: HistoricalRequest):
    """Get historical time series data"""
    try:
        response = requests.post(
            f"{BLOOMBERG_API_URL}/api/bloomberg/historical",
            headers=HEADERS,
            json=request.dict()
        )
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/volatility-surface")
async def get_volatility_surface(request: VolatilitySurfaceRequest):
    """Get complete volatility surface for a currency pair"""
    
    securities = []
    
    # Build security list
    for tenor in request.tenors:
        # ATM volatility
        if tenor == "ON":
            securities.append(f"{request.currency_pair}V{tenor} Curncy")
        else:
            securities.append(f"{request.currency_pair}V{tenor} BGN Curncy")
        
        # Risk Reversals and Butterflies for each delta
        if tenor != "ON":  # No RR/BF for overnight
            for delta in request.deltas:
                securities.append(f"{request.currency_pair}{delta}R{tenor} BGN Curncy")
                securities.append(f"{request.currency_pair}{delta}B{tenor} BGN Curncy")
    
    # Fetch data
    try:
        response = requests.post(
            f"{BLOOMBERG_API_URL}/api/bloomberg/reference",
            headers=HEADERS,
            json={
                "securities": securities,
                "fields": ["PX_LAST", "PX_BID", "PX_ASK"]
            }
        )
        
        data = response.json()
        
        if data.get('success'):
            # Organize data by tenor
            surface_data = {}
            
            for sec_data in data['data']['securities_data']:
                if sec_data.get('success') and sec_data.get('fields'):
                    security = sec_data['security']
                    
                    # Parse tenor from security name
                    import re
                    
                    # ATM pattern
                    atm_match = re.search(rf'{request.currency_pair}V(\w+)', security)
                    if atm_match:
                        tenor = atm_match.group(1)
                        if tenor not in surface_data:
                            surface_data[tenor] = {"atm": {}, "rr": {}, "bf": {}}
                        surface_data[tenor]["atm"] = sec_data['fields']
                        continue
                    
                    # RR/BF pattern
                    rr_bf_match = re.search(rf'{request.currency_pair}(\d+)(R|B)(\w+)', security)
                    if rr_bf_match:
                        delta = int(rr_bf_match.group(1))
                        type_char = rr_bf_match.group(2)
                        tenor = rr_bf_match.group(3)
                        
                        if tenor not in surface_data:
                            surface_data[tenor] = {"atm": {}, "rr": {}, "bf": {}}
                        
                        if type_char == 'R':
                            surface_data[tenor]["rr"][f"{delta}D"] = sec_data['fields']
                        else:
                            surface_data[tenor]["bf"][f"{delta}D"] = sec_data['fields']
            
            return {
                "success": True,
                "currency_pair": request.currency_pair,
                "timestamp": datetime.now().isoformat(),
                "surface": surface_data
            }
        else:
            return data
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/discover-tickers/{currency_pair}")
async def discover_tickers(currency_pair: str):
    """Discover all valid tickers for a currency pair"""
    
    # Common tenors to check
    tenors = ["ON", "1W", "2W", "3W", "1M", "2M", "3M", "6M", "9M", "1Y", "18M", "2Y"]
    deltas = [5, 10, 15, 20, 25, 30, 35, 40, 45]
    
    valid_tickers = {
        "atm": [],
        "risk_reversals": {},
        "butterflies": {}
    }
    
    # Check ATM volatilities
    atm_tickers = []
    for tenor in tenors:
        if tenor == "ON":
            atm_tickers.append(f"{currency_pair}V{tenor} Curncy")
        else:
            atm_tickers.append(f"{currency_pair}V{tenor} BGN Curncy")
    
    # Check in batches
    response = requests.post(
        f"{BLOOMBERG_API_URL}/api/bloomberg/reference",
        headers=HEADERS,
        json={
            "securities": atm_tickers,
            "fields": ["PX_LAST"]
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            for sec in data['data']['securities_data']:
                if sec.get('success') and sec.get('fields', {}).get('PX_LAST') is not None:
                    # Extract tenor
                    import re
                    match = re.search(rf'{currency_pair}V(\w+)', sec['security'])
                    if match:
                        valid_tickers['atm'].append(match.group(1))
    
    return {
        "currency_pair": currency_pair,
        "valid_tickers": valid_tickers,
        "discovered_at": datetime.now().isoformat()
    }

if __name__ == "__main__":
    print("🚀 Starting Bloomberg Data Explorer on http://localhost:8000")
    print("📚 API docs available at http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)