# Bloomberg Ticker Discovery System - Agent Guide

## Overview

Systematic ticker discovery system for building OIS curve inventories across all currencies using Bloomberg Terminal data.

## Architecture

```
Claude Code Agent → Local Gateway → VM FastAPI → Bloomberg Terminal
                        ↓
                   Ticker Data
                        ↓
                 Database Scripts
```

## Available Endpoints

### 1. Ticker Discovery
**Endpoint:** `POST http://localhost:8000/api/bloomberg/ticker-discovery`

**Purpose:** Find tickers by instrument type and currency

**Request:**
```json
{
  "search_type": "ois",
  "currency": "USD",
  "max_results": 50
}
```

**Response:**
```json
{
  "success": true,
  "search_criteria": {
    "search_type": "ois",
    "currency": "USD",
    "query_used": "USD OIS"
  },
  "tickers_found": 5,
  "tickers": [
    {
      "ticker": "USOSFR1<crncy>",
      "description": "USD OIS Annual VS SOFR 1Y",
      "instrument_type": "ois",
      "currency": "USD",
      "tenor": null,
      "curve_membership": "USD_OIS"
    }
  ]
}
```

### 2. Ticker Validation
**Endpoint:** `POST http://localhost:8000/api/bloomberg/validate-tickers`

**Purpose:** Validate tickers exist and get live prices

**Request:**
```json
["USOSFR1 Curncy", "USOSFR2 Curncy", "USOSFR5 Curncy"]
```

**Response:**
```json
{
  "success": true,
  "validated_count": 3,
  "results": [
    {
      "ticker": "USOSFR1 Curncy",
      "valid": true,
      "name": "USD OIS ANN VS SOFR 1Y",
      "last_price": 3.99706
    }
  ]
}
```

## Systematic Discovery Process

### Step 1: Currency Discovery
Discover OIS tickers for any currency:

```bash
curl -X POST "http://localhost:8000/api/bloomberg/ticker-discovery" \
  -H "Content-Type: application/json" \
  -d '{"search_type": "ois", "currency": "EUR", "max_results": 100}'
```

### Step 2: Validation
Validate discovered tickers work:

```bash
curl -X POST "http://localhost:8000/api/bloomberg/validate-tickers" \
  -H "Content-Type: application/json" \
  -d '["EESWEA BGN Curncy", "EESWE1 BGN Curncy", "EESWE2 BGN Curncy"]'
```

### Step 3: Data Processing
Extract validated tickers for database insertion.

## Supported Currencies

**Tested:** USD, EUR, GBP, JPY (confirmed working)
**Theoretical:** Any currency Bloomberg supports (CHF, CAD, AUD, NZD, SEK, NOK, DKK, PLN, CZK, etc.)

**Note:** System uses dynamic query construction (`{currency} OIS`) so no hardcoded limitations.

## Current Limitations

**Known Issue:** VM endpoint has hardcoded search patterns for ~10 currencies only. Currencies not in hardcoded list return:
```json
{
  "success": false,
  "error": "No search pattern defined for ois PLN"
}
```

**Workaround:** Focus on supported currencies first: USD, EUR, GBP, JPY, CHF, CAD, AUD, NZD, SEK, NOK.

## Agent Usage Examples

### Example 1: Full USD OIS Discovery
```bash
# Discover all USD OIS tickers
curl -X POST "http://localhost:8000/api/bloomberg/ticker-discovery" \
  -d '{"search_type": "ois", "currency": "USD", "max_results": 100}' \
  -H "Content-Type: application/json"

# Extract tickers and validate
curl -X POST "http://localhost:8000/api/bloomberg/validate-tickers" \
  -d '["USOSFR1 Curncy", "USOSFR2 Curncy", "USOSFR3 Curncy", "USOSFR5 Curncy", "USOSFR10 Curncy", "USOSFR20 Curncy", "USOSFR30 Curncy"]' \
  -H "Content-Type: application/json"
```

### Example 2: Multi-Currency Batch Processing
```bash
# Process each G10 currency systematically
for currency in USD EUR GBP JPY CHF CAD AUD NZD; do
  echo "Processing $currency OIS..."
  curl -X POST "http://localhost:8000/api/bloomberg/ticker-discovery" \
    -d "{\"search_type\": \"ois\", \"currency\": \"$currency\", \"max_results\": 50}" \
    -H "Content-Type: application/json" | jq
done
```

## Database Integration

**Storage Strategy:**
1. Agent discovers and validates tickers
2. Generate structured CSV/JSON output  
3. Use separate database scripts to populate PostgreSQL
4. App retrieves from database inventory

**Data Format for Database:**
```json
{
  "currency": "USD",
  "instrument_type": "ois", 
  "tickers": [
    {
      "ticker": "USOSFR1 Curncy",
      "description": "USD OIS Annual VS SOFR 1Y",
      "validated": true,
      "last_price": 3.99706,
      "tenor_days": 365,
      "curve_membership": "USD_OIS"
    }
  ]
}
```

## Error Handling

**Common Errors:**
- Gateway timeout: Restart local gateway
- VM unreachable: Check network access to 20.172.249.92:8080
- Bloomberg disconnected: VM shows cached data with timestamps
- Currency not supported: Use supported currency list

**Validation:**
- Always validate tickers before database insertion
- Check `valid: true` in validation response
- Verify `last_price` is not null for live tickers

## Next Steps

1. **Remove VM hardcoded patterns** - Make discovery truly dynamic
2. **Expand to all currencies** - Test emerging market currencies
3. **Database automation** - Direct PostgreSQL integration
4. **Curve construction** - Build complete yield curves from discovered tickers

---
**System Status:** ✅ OPERATIONAL (2025-07-30)
**Last Updated:** 2025-07-30T19:25:00Z