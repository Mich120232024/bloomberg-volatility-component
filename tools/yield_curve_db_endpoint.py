#!/usr/bin/env python3
"""
Yield Curve Database Endpoint Extension for Bloomberg Gateway
Provides yield curve configurations from PostgreSQL database
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import psycopg2
import json
import os
import subprocess

# Create router for yield curve endpoints
yield_curve_router = APIRouter(prefix="/api/yield-curves", tags=["yield-curves"])

# Request/Response models
class YieldCurveRequest(BaseModel):
    currency: str
    include_data: Optional[bool] = False  # Whether to fetch live Bloomberg data

class CurveInstrument(BaseModel):
    ticker: str
    tenor: int      # Days to maturity
    label: str      # Display label
    years: float    # Years to maturity for scaling
    instrumentType: str  # 'money_market', 'swap', or 'bond'
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
        # Fallback to environment variable
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

def tenor_to_label(days: int) -> str:
    """Convert tenor in days to display label"""
    if days == 1:
        return "O/N"
    elif days < 30:
        weeks = days // 7
        return f"{weeks}W" if weeks > 1 else "1W"
    elif days < 365:
        months = round(days / 30)
        return f"{months}M"
    else:
        years = round(days / 365)
        return f"{years}Y"

def get_instrument_type(ticker: str) -> str:
    """Determine instrument type from ticker"""
    ticker_upper = ticker.upper()
    
    # Money market indicators
    if any(x in ticker_upper for x in ['RATE', 'LIBOR', 'EURIBOR', 'TIBOR', 'BBSW', 'CDOR', 'PRIBOR', 'WIBOR']):
        return 'money_market'
    # Government bonds
    elif any(x in ticker_upper for x in ['USGG', 'GDBR', 'GUKG', 'GJGB', 'GSWISS', 'GCAN', 'GACGB']):
        return 'bond'
    # Everything else is likely a swap
    else:
        return 'swap'

@yield_curve_router.get("/available")
async def get_available_curves():
    """Get list of available yield curves from database"""
    conn = None
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Get all defined curves with member count
        cursor.execute("""
            SELECT 
                rcd.curve_name,
                rcd.currency_code,
                rcd.curve_type,
                rcd.methodology as description,
                COUNT(DISTINCT rcm.bloomberg_ticker) as member_count
            FROM rate_curve_definitions rcd
            LEFT JOIN rate_curve_mappings rcm ON rcd.curve_name = rcm.curve_name
            WHERE rcd.is_active = true
            GROUP BY rcd.id, rcd.curve_name, rcd.currency_code, rcd.curve_type, rcd.methodology
            ORDER BY rcd.currency_code, rcd.curve_type
        """)
        
        curves = []
        for row in cursor.fetchall():
            curves.append({
                "curve_name": row[0],
                "currency": row[1],
                "curve_type": row[2],
                "description": row[3],
                "member_count": row[4]
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
    """Get yield curve configuration from database using actual schema"""
    conn = None
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Get all tickers for this currency through curve mappings
        ticker_query = """
            SELECT 
                bt.bloomberg_ticker,
                bt.tenor,
                bt.tenor_numeric,
                bt.properties,
                rcd.curve_name,
                bt.category,
                rcm.sorting_order
            FROM rate_curve_definitions rcd
            JOIN rate_curve_mappings rcm ON rcd.curve_name = rcm.curve_name
            JOIN bloomberg_tickers bt ON bt.bloomberg_ticker = rcm.bloomberg_ticker
            WHERE rcd.currency_code = %s 
            AND rcd.is_active = true
            AND bt.is_active = true
            ORDER BY 
                rcd.curve_name,
                COALESCE(rcm.sorting_order, 999),
                CASE 
                    WHEN bt.tenor_numeric IS NOT NULL THEN bt.tenor_numeric
                    ELSE 999999
                END
        """
        
        cursor.execute(ticker_query, (request.currency,))
        ticker_results = cursor.fetchall()
        
        if not ticker_results:
            return YieldCurveResponse(
                success=False,
                currency=request.currency,
                title=f"{request.currency} Yield Curve",
                instruments=[],
                error=f"No curve members found for {request.currency}"
            )
        
        instruments = []
        curve_name = f"{request.currency}_OIS"  # Default curve name
        
        for bloomberg_ticker, tenor, tenor_numeric, properties, db_curve_name, category, sorting_order in ticker_results:
            # Use tenor_numeric if available, otherwise try to parse tenor
            days = tenor_numeric
            if days is None and tenor:
                # Try to parse tenor string to days
                try:
                    if tenor == 'O/N':
                        days = 1
                    elif tenor.endswith('W'):
                        days = int(tenor[:-1]) * 7
                    elif tenor.endswith('M'):
                        days = int(tenor[:-1]) * 30
                    elif tenor.endswith('Y'):
                        days = int(tenor[:-1]) * 365
                    else:
                        days = 0
                except:
                    days = 0
            
            # Calculate years (handle Decimal from database)
            years = float(days) / 365.0 if days else 0
            
            # Use label from properties or generate from tenor
            label = tenor or "N/A"
            if properties and isinstance(properties, dict) and 'label' in properties:
                label = properties['label']
            
            # Determine instrument type from category or ticker
            instrument_type = category or get_instrument_type(bloomberg_ticker)
            
            # Use sorting_order from mappings table or properties
            order = sorting_order
            if order is None and properties and isinstance(properties, dict) and 'curve_order' in properties:
                order = properties['curve_order']
            
            instruments.append(CurveInstrument(
                ticker=bloomberg_ticker,
                tenor=int(days) if days else 0,
                label=label,
                years=round(years, 3),
                instrumentType=instrument_type,
                order=order
            ))
        
        # Use curve name from database or generate default
        if db_curve_name:
            curve_name = db_curve_name
        
        title = f"{request.currency} Yield Curve ({len(instruments)} instruments)"
        
        response = YieldCurveResponse(
            success=True,
            currency=request.currency,
            title=title,
            instruments=instruments
        )
        
        # Optionally fetch live Bloomberg data
        if request.include_data and instruments:
            # This would call the Bloomberg API with all tickers
            # For now, we'll leave this as a placeholder
            pass
        
        return response
        
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

# Add this router to your main FastAPI app:
# app.include_router(yield_curve_router)