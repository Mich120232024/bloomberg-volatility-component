# Ticker Discovery Integration Plan

## Current Architecture Confirmed
- ✅ Bloomberg VM API is FastAPI (confirmed via `/docs` endpoint)
- ✅ Running as `main.py` with Python 3.11
- ✅ Has standard FastAPI endpoints structure

## Integration Steps

### 1. Create Integration Module
Since the VM API is FastAPI, we can create a clean integration module:

```python
# ticker_discovery_router.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import blpapi

router = APIRouter(prefix="/api/bloomberg", tags=["ticker-discovery"])

class TickerSearchRequest(BaseModel):
    search_type: str
    currency: str
    asset_class: Optional[str] = "Curncy"
    max_results: Optional[int] = 100

@router.post("/ticker-discovery")
async def discover_tickers(request: TickerSearchRequest):
    # Implementation here
    pass

@router.post("/validate-tickers")
async def validate_tickers(tickers: List[str]):
    # Implementation here
    pass
```

### 2. Integration in main.py
```python
# In the VM's main.py, add:
from ticker_discovery_router import router as ticker_discovery_router

app.include_router(ticker_discovery_router)
```

### 3. Test OIS Discovery Patterns

Based on the documentation, these are the key search patterns:

#### G10 OIS Patterns
- **USD**: SOFR*, USSO*, USSOA, USSOB, USSOC
- **EUR**: ESTR*, EURON*, EURONA, EURONB
- **GBP**: SONIA*, SONIO*, SONIOA, SONIOB
- **JPY**: TONA*, TONAON, MTON*, JYSO*
- **CHF**: SARON*, SSARON*, SSARA*
- **CAD**: CORRA*, CDOR*
- **AUD**: AONIA*, RBACOR*
- **NZD**: NZIONA*, RBNZON*
- **SEK**: STINA*, SWESTR*
- **NOK**: NOWA*, NIBOR*

### 4. Safety Measures

1. **Backup Current API**
   ```powershell
   Copy-Item main.py main_backup_$(Get-Date -Format 'yyyyMMdd').py
   ```

2. **Test in Isolation**
   - Create standalone test script first
   - Verify Bloomberg instrumentListRequest works
   - Only integrate after successful testing

3. **Rollback Plan**
   - Keep backup of working main.py
   - Document current working endpoints
   - Test health endpoint after changes

## Local Testing Strategy

While VM API is unavailable, we can:

1. **Test Known OIS Tickers**
   ```bash
   # Test via local gateway when API returns
   curl -X POST "http://localhost:8000/api/bloomberg/reference" \
     -H "Authorization: Bearer test" \
     -H "Content-Type: application/json" \
     -d '{
       "securities": [
         "SONIO/N Index",
         "SONIOA BGN Curncy", 
         "ESTRON Index",
         "EURONA BGN Curncy"
       ],
       "fields": ["PX_LAST", "NAME"]
     }'
   ```

2. **Prepare Database Update Script**
   - Script to insert discovered tickers into PostgreSQL
   - Map tickers to curve memberships
   - Update OIS coverage for all G10 currencies

## Risk Assessment
- **Low Risk**: Adding new router to FastAPI app
- **Medium Risk**: Bloomberg API calls may have rate limits
- **Mitigation**: Test thoroughly, keep backups, monitor logs