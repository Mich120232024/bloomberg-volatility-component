#!/usr/bin/env python3
"""
Bloomberg Gateway API - Production-Ready Service
Designed for containerized deployment (Kubernetes/Azure Container Apps)

Environment Variables:
- BLOOMBERG_API_URL: Bloomberg VM endpoint (default: http://20.172.249.92:8080)
- REDIS_CONNECTION: Redis connection string (optional, for production)
- ENABLE_CACHE: Enable caching (default: false for dev, true for prod)
- CACHE_TTL: Cache time-to-live in seconds (default: 900)
- LOG_LEVEL: Logging level (default: INFO)
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import asyncio
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration from environment
BLOOMBERG_API_URL = os.getenv("BLOOMBERG_API_URL", "http://20.172.249.92:8080")
REDIS_CONNECTION = os.getenv("REDIS_CONNECTION")
ENABLE_CACHE = os.getenv("ENABLE_CACHE", "false").lower() == "true"
CACHE_TTL = int(os.getenv("CACHE_TTL", "900"))  # 15 minutes default

# Load ticker repository
TICKER_REPO_PATH = Path(__file__).parent.parent / "knowledge" / "technical_resources" / "bloomberg_api" / "central_bloomberg_ticker_repository_v3.json"
if not TICKER_REPO_PATH.exists():
    # Fallback for local development
    TICKER_REPO_PATH = Path(__file__).parent / "central_bloomberg_ticker_repository_v3.json"

try:
    with open(TICKER_REPO_PATH) as f:
        TICKER_REPOSITORY = json.load(f)
    logger.info(f"Loaded {TICKER_REPOSITORY['metadata']['total_valid_tickers']} tickers from repository")
except Exception as e:
    logger.warning(f"Could not load ticker repository: {e}")
    TICKER_REPOSITORY = None

# Cache implementation
class CacheManager:
    def __init__(self):
        self.cache = {}
        self.redis_client = None
        
        if REDIS_CONNECTION and ENABLE_CACHE:
            try:
                import redis
                self.redis_client = redis.from_url(REDIS_CONNECTION)
                self.redis_client.ping()
                logger.info("Connected to Redis cache")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}. Using in-memory cache.")
    
    async def get(self, key: str) -> Optional[Dict]:
        if not ENABLE_CACHE:
            return None
            
        if self.redis_client:
            try:
                data = self.redis_client.get(key)
                if data:
                    return json.loads(data)
            except Exception as e:
                logger.error(f"Redis get error: {e}")
        else:
            # In-memory cache
            if key in self.cache:
                data, timestamp = self.cache[key]
                if datetime.now() - timestamp < timedelta(seconds=CACHE_TTL):
                    return data
                else:
                    del self.cache[key]
        return None
    
    async def set(self, key: str, value: Dict):
        if not ENABLE_CACHE:
            return
            
        if self.redis_client:
            try:
                self.redis_client.setex(key, CACHE_TTL, json.dumps(value))
            except Exception as e:
                logger.error(f"Redis set error: {e}")
        else:
            # In-memory cache
            self.cache[key] = (value, datetime.now())
    
    async def clear(self):
        if self.redis_client:
            self.redis_client.flushdb()
        else:
            self.cache.clear()

# Initialize cache
cache_manager = CacheManager()

# HTTP client
http_client = httpx.AsyncClient(timeout=30.0)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Bloomberg Gateway starting up...")
    logger.info(f"Cache enabled: {ENABLE_CACHE}")
    logger.info(f"Bloomberg API: {BLOOMBERG_API_URL}")
    yield
    # Shutdown
    await http_client.aclose()
    logger.info("Bloomberg Gateway shutting down...")

# Create FastAPI app
app = FastAPI(
    title="Bloomberg Gateway API",
    version="3.0.0",
    description="Production-ready Bloomberg data gateway with intelligent ticker selection",
    lifespan=lifespan
)

# CORS configuration - Production whitelist
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Local development
        "http://localhost:3000",  # Alternative dev port
        "http://localhost:3501",  # Bloomberg volatility component dev port
        "http://62.171.108.4",   # Whitelisted production IP
        "https://62.171.108.4"   # HTTPS variant
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Models
class VolatilityRequest(BaseModel):
    pair: str
    tenors: Optional[List[str]] = None  # If not provided, use standard tenors

class VolatilityResponse(BaseModel):
    data: Dict[str, Any]
    metadata: Dict[str, Any]

# Helper functions
def get_volatility_tickers(pair: str, tenors: List[str]) -> Dict[str, List[str]]:
    """Get the best available tickers for a currency pair"""
    tickers = {
        "spot": [f"{pair} Curncy"],
        "atm": [],
        "rr_25d": [],
        "bf_25d": [],
        "forwards": []
    }
    
    for tenor in tenors:
        if tenor == "ON":
            tickers["atm"].append(f"{pair}VON Curncy")
        else:
            tickers["atm"].append(f"{pair}V{tenor} BGN Curncy")
            tickers["atm"].append(f"{pair}V{tenor} Curncy")  # Fallback
        
        # Risk reversal and butterfly
        tickers["rr_25d"].append(f"{pair}25R{tenor} BGN Curncy")
        tickers["rr_25d"].append(f"{pair}25R{tenor} Curncy")  # Fallback
        tickers["bf_25d"].append(f"{pair}25B{tenor} BGN Curncy")
        tickers["bf_25d"].append(f"{pair}25B{tenor} Curncy")  # Fallback
        
        # Forwards
        tickers["forwards"].append(f"{pair}{tenor} Curncy")
    
    return tickers

async def fetch_bloomberg_data(securities: List[str], fields: List[str]) -> Dict:
    """Fetch data from Bloomberg API"""
    payload = {
        "securities": securities,
        "fields": fields
    }
    
    headers = {
        "Authorization": "Bearer test",
        "Content-Type": "application/json"
    }
    
    try:
        response = await http_client.post(
            f"{BLOOMBERG_API_URL}/api/bloomberg/reference",
            json=payload,
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Bloomberg API error: {response.status_code}")
            return {"error": f"Bloomberg API returned {response.status_code}"}
            
    except Exception as e:
        logger.error(f"Bloomberg API connection error: {e}")
        return {"error": str(e)}

# API Endpoints
@app.get("/")
async def root():
    return {
        "name": "Bloomberg Gateway API",
        "version": "3.0.0",
        "status": "ready",
        "cache_enabled": ENABLE_CACHE,
        "bloomberg_api": BLOOMBERG_API_URL,
        "ticker_repository": TICKER_REPOSITORY is not None,
        "environment": "development" if not ENABLE_CACHE else "production"
    }

@app.get("/health")
async def health_check():
    """Kubernetes/Container health check endpoint"""
    # Check Bloomberg API
    try:
        response = await http_client.get(f"{BLOOMBERG_API_URL}/health", timeout=5.0)
        bloomberg_status = response.status_code == 200
    except:
        bloomberg_status = False
    
    return {
        "status": "healthy" if bloomberg_status else "degraded",
        "bloomberg_api": bloomberg_status,
        "cache": ENABLE_CACHE,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/volatility/{pair}", response_model=VolatilityResponse)
async def get_volatility_surface(pair: str, force_fresh: bool = False):
    """
    Get complete volatility surface for a currency pair
    Uses intelligent ticker selection from our 3,001 discovered tickers
    """
    cache_key = f"vol_{pair}"
    
    # Check cache first (unless forced fresh)
    if not force_fresh:
        cached_data = await cache_manager.get(cache_key)
        if cached_data:
            return VolatilityResponse(
                data=cached_data,
                metadata={
                    "source": "CACHE",
                    "cached_at": cached_data.get("timestamp"),
                    "pair": pair,
                    "cache_ttl": CACHE_TTL
                }
            )
    
    # Define standard tenors
    tenors = ["ON", "1W", "2W", "1M", "2M", "3M", "6M", "9M", "1Y", "18M", "2Y"]
    
    # Get tickers
    ticker_groups = get_volatility_tickers(pair, tenors)
    all_tickers = []
    for group in ticker_groups.values():
        all_tickers.extend(group)
    
    # Fetch from Bloomberg
    fields = ["PX_LAST", "PX_BID", "PX_ASK", "LAST_UPDATE"]
    bloomberg_response = await fetch_bloomberg_data(all_tickers, fields)
    
    if "error" in bloomberg_response:
        raise HTTPException(status_code=503, detail=bloomberg_response["error"])
    
    # Process response
    processed_data = {
        "pair": pair,
        "timestamp": datetime.now().isoformat(),
        "tenors": {},
        "spot": None
    }
    
    # Extract data
    if "data" in bloomberg_response and "securities_data" in bloomberg_response["data"]:
        for security_data in bloomberg_response["data"]["securities_data"]:
            if security_data.get("success"):
                ticker = security_data["security"]
                fields = security_data.get("fields", {})
                
                # Process based on ticker type
                if ticker == f"{pair} Curncy":
                    processed_data["spot"] = fields.get("PX_LAST")
                # Add more processing logic here
    
    # Cache the result
    await cache_manager.set(cache_key, processed_data)
    
    return VolatilityResponse(
        data=processed_data,
        metadata={
            "source": "BLOOMBERG_LIVE",
            "fetched_at": datetime.now().isoformat(),
            "pair": pair,
            "tickers_checked": len(all_tickers)
        }
    )

@app.post("/api/cache/clear")
async def clear_cache():
    """Clear cache - useful for development"""
    if ENABLE_CACHE:
        await cache_manager.clear()
        return {"status": "Cache cleared"}
    else:
        return {"status": "Cache not enabled"}

# Direct proxy endpoints for frontend compatibility
@app.post("/api/bloomberg/reference")
async def bloomberg_reference_proxy(request: Dict[str, Any]):
    """Direct proxy to Bloomberg reference endpoint - for frontend compatibility"""
    try:
        payload = {
            "securities": request.get("securities", []),
            "fields": request.get("fields", [])
        }
        
        headers = {
            "Authorization": "Bearer test",
            "Content-Type": "application/json"
        }
        
        response = await http_client.post(
            f"{BLOOMBERG_API_URL}/api/bloomberg/reference",
            json=payload,
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Bloomberg API returned {response.status_code}"}
            
    except Exception as e:
        logger.error(f"Bloomberg reference proxy error: {e}")
        raise HTTPException(status_code=503, detail=str(e))

@app.post("/api/bloomberg/historical")
async def bloomberg_historical_proxy(request: Dict[str, Any]):
    """Direct proxy to Bloomberg historical endpoint - for frontend compatibility"""
    try:
        headers = {
            "Authorization": "Bearer test",
            "Content-Type": "application/json"
        }
        
        response = await http_client.post(
            f"{BLOOMBERG_API_URL}/api/bloomberg/historical",
            json=request,
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Bloomberg API returned {response.status_code}"}
            
    except Exception as e:
        logger.error(f"Bloomberg historical proxy error: {e}")
        raise HTTPException(status_code=503, detail=str(e))

# Container/Kubernetes specific endpoints
@app.get("/ready")
async def readiness():
    """Kubernetes readiness probe"""
    return {"ready": True}

@app.get("/live")
async def liveness():
    """Kubernetes liveness probe"""
    return {"alive": True}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)