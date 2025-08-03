# VM Integration Steps for Ticker Discovery

## Step 1: Copy the module to VM

```powershell
# Copy ticker_discovery_module.py to the VM
# Place it in the same directory as main.py
```

## Step 2: Modify main.py

Add these lines to the VM's main.py:

```python
# At the top with other imports
from ticker_discovery_module import ticker_discovery_router

# After creating the FastAPI app
app.include_router(ticker_discovery_router)

# Pass bloomberg_service to endpoints
# In the router configuration, add dependency injection:
from fastapi import Depends

def get_bloomberg_service():
    # Return the bloomberg service instance used by main app
    return bloomberg_service  # or however it's named in main.py

# Update the router endpoints to use the service
@ticker_discovery_router.post("/ticker-discovery")
async def discover_tickers(
    request: TickerSearchRequest, 
    bloomberg_service = Depends(get_bloomberg_service)
):
    # ... rest of the function
```

## Step 3: Test the endpoints

```bash
# Test ticker discovery
curl -X POST "http://20.172.249.92:8080/api/bloomberg/ticker-discovery" \
  -H "Authorization: Bearer test" \
  -H "Content-Type: application/json" \
  -d '{
    "search_type": "ois",
    "currency": "GBP"
  }'

# Test ticker validation
curl -X POST "http://20.172.249.92:8080/api/bloomberg/validate-tickers" \
  -H "Authorization: Bearer test" \
  -H "Content-Type: application/json" \
  -d '["SONIOA BGN Curncy", "SONIOB BGN Curncy"]'
```

## Step 4: Verify in API docs

Check http://20.172.249.92:8080/docs to see the new endpoints