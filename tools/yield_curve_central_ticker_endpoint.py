#!/usr/bin/env python3
"""
Simplified Yield Curve Endpoint using ONLY ticker_reference table
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import psycopg2
import os
import subprocess

# Create router for yield curve endpoints
yield_curve_router = APIRouter(prefix="/api/yield-curves", tags=["yield-curves"])

# Request/Response models
class YieldCurveRequest(BaseModel):
    currency: str
    include_data: Optional[bool] = False

class CurveInstrument(BaseModel):
    ticker: str
    tenor: str
    label: str
    years: float
    instrumentType: str
    order: Optional[int] = None

class YieldCurveResponse(BaseModel):
    success: bool
    currency: str
    title: str
    instruments: List[CurveInstrument]
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

def get_postgres_password():
    """Get PostgreSQL password from Azure Key Vault"""
    try:
        result = subprocess.run([
            'az', 'keyvault', 'secret', 'show', 
            '--vault-name', 'gzc-finma-keyvault',
            '--name', 'postgres-connection-string',
            '--query', 'value', 
            '-o', 'tsv'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            connection_string = result.stdout.strip()
            if '://' in connection_string and '@' in connection_string:
                password_part = connection_string.split('://')[1].split('@')[0]
                if ':' in password_part:
                    return password_part.split(':')[1]
        
        raise ValueError("Cannot parse password from connection string")
    except Exception as e:
        logging.error(f"Failed to get password from Key Vault: {e}")
        return os.environ.get('POSTGRES_PASSWORD', '')

def get_database_connection():
    """Create database connection"""
    password = get_postgres_password()
    return psycopg2.connect(
        host='gzcdevserver.postgres.database.azure.com',
        database='gzc_platform',
        user='mikael',
        password=password,
        port=5432,
        sslmode='require'
    )

def parse_tenor_from_ticker(ticker: str) -> tuple[str, float, int]:
    """Parse tenor information from ticker symbol"""
    # Extract tenor from ticker patterns like USSO1, USSO10, etc.
    ticker_upper = ticker.upper()
    
    # Common patterns
    if 'O/N' in ticker_upper or 'RATE' in ticker_upper:
        return 'O/N', 1/365, 1
    
    # Extract numeric part from patterns like USSO1, USSO10
    import re
    match = re.search(r'([A-Z]+)(\d+)', ticker_upper)
    if match:
        numeric = int(match.group(2))
        if numeric <= 11:  # Likely months
            if numeric == 1:
                return '1Y', 1.0, 365
            else:
                return f'{numeric}M', numeric/12, numeric * 30
        else:  # Years
            return f'{numeric}Y', float(numeric), numeric * 365
    
    return 'Unknown', 0, 0

@yield_curve_router.get("/available")
async def get_available_curves():
    """Get list of available curves from ticker_reference"""
    conn = None
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                currency_code,
                curve_name,
                COUNT(*) as ticker_count
            FROM ticker_reference
            WHERE is_active = true
            GROUP BY currency_code, curve_name
            ORDER BY currency_code, curve_name
        """)
        
        curves = []
        for row in cursor.fetchall():
            curves.append({
                "currency": row[0],
                "curve_name": row[1],
                "ticker_count": row[2]
            })
        
        return {
            "success": True,
            "curves": curves,
            "total": len(curves)
        }
        
    except Exception as e:
        logging.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@yield_curve_router.post("/config", response_model=YieldCurveResponse)
async def get_yield_curve_config(request: YieldCurveRequest):
    """Get yield curve configuration from ticker_reference table"""
    conn = None
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Simple query - just get tickers for this currency from ticker_reference
        cursor.execute("""
            SELECT 
                bloomberg_ticker,
                instrument_type,
                curve_name
            FROM ticker_reference
            WHERE currency_code = %s 
            AND is_active = true
            ORDER BY bloomberg_ticker
        """, (request.currency,))
        
        ticker_results = cursor.fetchall()
        
        if not ticker_results:
            return YieldCurveResponse(
                success=False,
                currency=request.currency,
                title=f"{request.currency} Yield Curve",
                instruments=[],
                error=f"No tickers found for {request.currency}"
            )
        
        instruments = []
        curve_name = None
        
        for bloomberg_ticker, instrument_type, db_curve_name in ticker_results:
            # Parse tenor from ticker
            tenor_label, years, order = parse_tenor_from_ticker(bloomberg_ticker)
            
            if db_curve_name and not curve_name:
                curve_name = db_curve_name
            
            instruments.append(CurveInstrument(
                ticker=bloomberg_ticker,
                tenor=tenor_label,
                label=tenor_label,
                years=years,
                instrumentType=instrument_type or 'ois',
                order=order
            ))
        
        # Sort by order/years
        instruments.sort(key=lambda x: x.order)
        
        title = f"{request.currency} {curve_name or 'Yield Curve'} ({len(instruments)} instruments)"
        
        return YieldCurveResponse(
            success=True,
            currency=request.currency,
            title=title,
            instruments=instruments
        )
        
    except Exception as e:
        logging.error(f"Database error: {e}")
        return YieldCurveResponse(
            success=False,
            currency=request.currency,
            title=f"{request.currency} Yield Curve",
            instruments=[],
            error=str(e)
        )
    finally:
        if conn:
            conn.close()

@yield_curve_router.post("/batch-config")
async def get_batch_yield_curves(currencies: List[str]):
    """Get multiple yield curve configurations at once"""
    results = {}
    
    for currency in currencies:
        try:
            result = await get_yield_curve_config(YieldCurveRequest(currency=currency))
            results[currency] = result.dict()
        except Exception as e:
            results[currency] = {
                "success": False,
                "error": str(e)
            }
    
    return {
        "success": True,
        "curves": results
    }

# Usage: app.include_router(yield_curve_router)