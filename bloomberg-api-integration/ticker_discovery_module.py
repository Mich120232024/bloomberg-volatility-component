#!/usr/bin/env python3
"""
Bloomberg Ticker Discovery Module for VM Integration
Adds ticker discovery capability using Bloomberg's instrumentListRequest
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import blpapi

# Create router for ticker discovery endpoints
ticker_discovery_router = APIRouter(prefix="/api/bloomberg", tags=["ticker-discovery"])

# Request/Response models
class TickerSearchRequest(BaseModel):
    search_type: str  # 'ois', 'irs', 'fx_spot', 'fx_vol', 'govt_bond'
    currency: str  # 'USD', 'EUR', 'GBP', etc.
    asset_class: Optional[str] = "Curncy"
    max_results: Optional[int] = 100

class TickerSearchResponse(BaseModel):
    success: bool
    search_criteria: Dict[str, Any]
    tickers_found: int
    tickers: List[Dict[str, Any]]
    error: Optional[str] = None

# Bloomberg query patterns for different instrument types
# Updated to use text-based search instead of wildcard patterns
SEARCH_PATTERNS = {
    'ois': {
        'USD': 'USD OIS',
        'EUR': 'EUR OIS',
        'GBP': 'GBP OIS',
        'JPY': 'JPY OIS',
        'CHF': 'CHF OIS',
        'CAD': 'CAD OIS',
        'AUD': 'AUD OIS',
        'NZD': 'NZD OIS',
        'SEK': 'SEK OIS',
        'NOK': 'NOK OIS'
    },
    'irs': {
        'USD': 'USD swap',
        'EUR': 'EUR swap',
        'GBP': 'GBP swap',
        'JPY': 'JPY swap'
    },
    'fx_vol': {
        'EUR': 'EURUSDV* BGN Curncy OR EUR25R* BGN Curncy OR EUR10R* BGN Curncy',
        'USD': 'USDJPYV* BGN Curncy OR JPY25R* BGN Curncy',
        'GBP': 'GBPUSDV* BGN Curncy OR GBP25R* BGN Curncy'
    },
    'govt_bond': {
        'USD': 'GT* Govt OR T * Govt',
        'EUR': 'DBR* Govt OR GDBR* Index',
        'GBP': 'UKT* Govt OR GUKG* Index',
        'JPY': 'JGB* Govt'
    }
}

@ticker_discovery_router.post("/ticker-discovery", response_model=TickerSearchResponse)
async def discover_tickers(request: TickerSearchRequest, bloomberg_service=None):
    """
    Discover Bloomberg tickers using instrumentListRequest
    """
    try:
        # Get query pattern
        query_string = SEARCH_PATTERNS.get(request.search_type, {}).get(request.currency, '')
        if not query_string:
            return TickerSearchResponse(
                success=False,
                search_criteria={
                    "search_type": request.search_type,
                    "currency": request.currency
                },
                tickers_found=0,
                tickers=[],
                error=f"No search pattern defined for {request.search_type} {request.currency}"
            )

        # Use Bloomberg service from main app if available
        if not bloomberg_service or not bloomberg_service.session:
            return TickerSearchResponse(
                success=False,
                search_criteria={"search_type": request.search_type, "currency": request.currency},
                tickers_found=0,
                tickers=[],
                error="Bloomberg service not available"
            )

        session = bloomberg_service.session
        
        # Get instruments service
        if not session.openService("//blp/instruments"):
            return TickerSearchResponse(
                success=False,
                search_criteria={"search_type": request.search_type, "currency": request.currency},
                tickers_found=0,
                tickers=[],
                error="Failed to open instruments service"
            )

        instruments_service = session.getService("//blp/instruments")
        
        # Create and send request
        request_obj = instruments_service.createRequest("instrumentListRequest")
        request_obj.set("query", query_string)
        request_obj.set("maxResults", request.max_results)
        
        logging.info(f"Sending instrumentListRequest with query: {query_string}")
        session.sendRequest(request_obj)
        
        # Process response
        tickers = []
        timeout = 10000  # 10 seconds
        
        while True:
            event = session.nextEvent(timeout)
            
            for msg in event:
                if msg.hasElement("results"):
                    results = msg.getElement("results")
                    
                    for i in range(results.numValues()):
                        result = results.getValue(i)
                        ticker = result.getElementAsString("security")
                        description = result.getElementAsString("description") if result.hasElement("description") else ""
                        
                        # Parse tenor from ticker if OIS
                        tenor = None
                        if request.search_type == "ois":
                            if "USSO" in ticker:
                                # Extract tenor from USSO1, USSO2Y, etc
                                import re
                                match = re.search(r'USSO(\d+[MY]?)', ticker)
                                if match:
                                    tenor = match.group(1)
                            elif "JYSO" in ticker:
                                match = re.search(r'JYSO(\d+[MY]?)', ticker)
                                if match:
                                    tenor = match.group(1)
                        
                        ticker_info = {
                            "ticker": ticker,
                            "description": description,
                            "instrument_type": request.search_type,
                            "currency": request.currency,
                            "tenor": tenor
                        }
                        
                        # Add curve membership for OIS
                        if request.search_type == "ois":
                            ticker_info["curve_membership"] = f"{request.currency}_OIS"
                        
                        tickers.append(ticker_info)
            
            if event.eventType() == blpapi.Event.RESPONSE:
                break
        
        logging.info(f"Found {len(tickers)} tickers for {request.currency} {request.search_type}")
        
        return TickerSearchResponse(
            success=True,
            search_criteria={
                "search_type": request.search_type,
                "currency": request.currency,
                "query_used": query_string
            },
            tickers_found=len(tickers),
            tickers=tickers
        )
        
    except Exception as e:
        logging.error(f"Ticker discovery error: {str(e)}")
        return TickerSearchResponse(
            success=False,
            search_criteria={
                "search_type": request.search_type,
                "currency": request.currency
            },
            tickers_found=0,
            tickers=[],
            error=str(e)
        )

@ticker_discovery_router.post("/validate-tickers")
async def validate_tickers(tickers: List[str], bloomberg_service=None):
    """
    Validate if tickers exist in Bloomberg
    """
    try:
        if not bloomberg_service or not bloomberg_service.session:
            return {
                "success": False,
                "error": "Bloomberg service not available"
            }

        session = bloomberg_service.session
        
        # Use reference data service for validation
        if not session.openService("//blp/refdata"):
            return {
                "success": False,
                "error": "Failed to open refdata service"
            }

        refdata_service = session.getService("//blp/refdata")
        request = refdata_service.createRequest("ReferenceDataRequest")
        
        # Add securities
        for ticker in tickers:
            request.append("securities", ticker)
        
        # Request basic fields
        request.append("fields", "NAME")
        request.append("fields", "PX_LAST")
        
        session.sendRequest(request)
        
        # Process response
        results = []
        timeout = 5000  # 5 seconds
        
        while True:
            event = session.nextEvent(timeout)
            
            for msg in event:
                if msg.hasElement("securityData"):
                    secDataArray = msg.getElement("securityData")
                    
                    for i in range(secDataArray.numValues()):
                        secData = secDataArray.getValue(i)
                        ticker = secData.getElementAsString("security")
                        
                        if secData.hasElement("securityError"):
                            results.append({
                                "ticker": ticker,
                                "valid": False,
                                "error": "Security not found"
                            })
                        else:
                            fieldData = secData.getElement("fieldData")
                            results.append({
                                "ticker": ticker,
                                "valid": True,
                                "name": fieldData.getElementAsString("NAME") if fieldData.hasElement("NAME") else "",
                                "last_price": fieldData.getElementAsFloat("PX_LAST") if fieldData.hasElement("PX_LAST") else None
                            })
            
            if event.eventType() == blpapi.Event.RESPONSE:
                break
        
        return {
            "success": True,
            "validated_count": len(results),
            "results": results
        }
        
    except Exception as e:
        logging.error(f"Ticker validation error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }