# Development Guide - Bloomberg Volatility Component

This guide provides comprehensive information for developers working on this project.

## Architecture Overview

### Component Architecture
```
Bloomberg Terminal → Azure VM API → Local Gateway → React Frontend
     (Real Data)     (FastAPI)    (Python Proxy)   (TypeScript)
```

### Key Design Principles
1. **Real Data Only**: No synthetic fallbacks or placeholder values
2. **Generic Endpoints**: Use Bloomberg's generic reference/historical endpoints
3. **Frontend Processing**: All calculations done in components, not backend
4. **Transparency**: Show Bloomberg tickers in tooltips

## Bloomberg API Integration

### Local Gateway Pattern
Always use the local gateway (`bloomberg-gateway-enhanced.py`) instead of direct VM connection:

```javascript
// ✅ CORRECT - Use local gateway
const apiUrl = 'http://localhost:8000'

// ❌ WRONG - Direct VM connection causes CORS/network issues
const apiUrl = 'http://20.172.249.92:8080'
```

### Generic Endpoint Usage
Use Bloomberg's generic endpoints for all data needs:

```javascript
// Reference data (spot, forwards, volatility, etc.)
const response = await fetch(`${apiUrl}/api/bloomberg/reference`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    securities: ['EURUSD Curncy', 'EURUSD1M Curncy'],
    fields: ['PX_LAST', 'PX_BID', 'PX_ASK']
  })
})

// Historical data
const histResponse = await fetch(`${apiUrl}/api/bloomberg/historical`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    security: 'EURUSD Curncy',
    fields: ['PX_LAST'],
    start_date: '20250101',  // YYYYMMDD format
    end_date: '20250131'
  })
})
```

## FX Forward Curves Implementation

### Standard Forward Tickers
Most currency pairs use standard format:
```
{PAIR}{TENOR} Curncy
Examples: EURUSD1M Curncy, GBPUSD3M Curncy, USDJPY1Y Curncy
```

### NDF (Non-Deliverable Forward) Tickers
Restricted currencies require special NDF ticker formats:

```javascript
// From ndfMappings.ts
USDINR → IRN format (IRN1M Curncy)
USDTWD → NTN format (NTN1M Curncy)
USDKRW → KWN format (KWN1M Curncy)
// ... see ndfMappings.ts for complete list
```

### Forward Rate Calculation
Bloomberg returns forward POINTS, not outright rates:

```javascript
// Calculate pip factor
const pipFactor = pair.includes('JPY') ? 100 : 10000

// Calculate forward rate
const forwardRate = spotRate + (forwardPoints / pipFactor)

// Example for EURUSD:
// Spot: 1.0850
// 1M Points: -10.5
// Forward: 1.0850 + (-10.5 / 10000) = 1.08395
```

### Implementation Checklist
When adding forward curve support:
1. Check if currency needs NDF tickers (`usesNDF(pair)`)
2. Build appropriate ticker list (standard or NDF)
3. Fetch data using generic reference endpoint
4. Parse response handling both ticker formats
5. Calculate forward rates from points
6. Display with proper error handling for missing data

## Volatility Surface Implementation

### Ticker Patterns
```javascript
// ATM volatility
const atmTicker = tenor === 'ON' 
  ? `${pair}VON Curncy`           // Overnight special case
  : `${pair}V${tenor} BGN Curncy`  // Standard ATM

// Risk Reversal
const rrTicker = `${pair}${delta}R${tenor} BGN Curncy`
// Example: EURUSD25R1M BGN Curncy

// Butterfly
const bfTicker = `${pair}${delta}B${tenor} BGN Curncy`
// Example: EURUSD25B1M BGN Curncy
```

### Data Validation
The `DataValidator.ts` handles validation without fallbacks:
- Returns null for missing data
- No synthetic data generation
- Shows empty states in UI

## Database Integration

### PostgreSQL Structure
```sql
-- Main ticker repository
bloomberg_tickers (
  id, ticker, category, currency_code, 
  tenor, instrument_type, is_active
)

-- Categories:
-- fx_spot, fx_forward, fx_vol_atm, fx_vol_rr, 
-- fx_vol_bf, ois_curve, irs_curve
```

### Ticker Discovery
Use the new ticker discovery endpoints:

```bash
# Discover OIS tickers for a currency
curl -X POST "http://20.172.249.92:8080/api/bloomberg/ticker-discovery" \
  -H "Authorization: Bearer test" \
  -H "Content-Type: application/json" \
  -d '{"search_type": "ois", "currency": "GBP"}'

# Validate discovered tickers
curl -X POST "http://20.172.249.92:8080/api/bloomberg/validate-tickers" \
  -H "Authorization: Bearer test" \
  -H "Content-Type: application/json" \
  -d '["BPSO1 Curncy", "BPSO2 Curncy"]'
```

## Common Pitfalls and Solutions

### 1. Substring Matching Bug
```javascript
// ❌ WRONG - "35D" matches "5D" substring
if (security.includes('5D'))

// ✅ CORRECT - Use precise regex
const match = security.match(/EURUSD(\d+)D1M\s+BGN/)
```

### 2. Missing ON Tenor Handling
```javascript
// ❌ WRONG - Creates invalid ticker
const ticker = `${pair}V${tenor} BGN Curncy`  // EURUSDVON BGN Curncy

// ✅ CORRECT - Special case for ON
const ticker = tenor === 'ON' 
  ? `${pair}VON Curncy` 
  : `${pair}V${tenor} BGN Curncy`
```

### 3. Forward Points vs Rates
```javascript
// ❌ WRONG - Treating points as rates
const forwardRate = forwardPoints  // Shows 10.5 instead of 1.08395

// ✅ CORRECT - Calculate from points
const forwardRate = spotRate + (forwardPoints / pipFactor)
```

### 4. NDF Ticker Detection
```javascript
// ❌ WRONG - Hardcoded list
if (pair === 'USDINR' || pair === 'USDTWD') {
  // use NDF
}

// ✅ CORRECT - Use mapping system
if (usesNDF(pair)) {
  const ndfTicker = getNDFTicker(pair, tenor)
}
```

## Testing Strategies

### 1. Console Logging
Add strategic console logs for debugging:

```javascript
console.log(`🔄 Using NDF tickers for ${pair} (${ndfMapping.format} format)`)
console.log(`📊 NDF Coverage: ${ndfMapping.coverage}`)
console.log(`✅ Matched ticker: ${ticker} -> tenor: ${tenor}`)
```

### 2. Manual API Verification
Verify tickers before implementing:

```bash
# Verify standard forward
curl -X POST http://localhost:8000/api/bloomberg/reference \
  -H "Content-Type: application/json" \
  -d '{"securities": ["EURUSD1M Curncy"], "fields": ["PX_LAST"]}'

# Verify NDF ticker
curl -X POST http://localhost:8000/api/bloomberg/reference \
  -H "Content-Type: application/json" \
  -d '{"securities": ["IRN1M Curncy"], "fields": ["PX_LAST", "NAME"]}'
```

### 3. Coverage Analysis
Run systematic analysis scripts:
- `currency_forward_coverage_analysis.py` - Analyze all pairs
- `check_ndf_tickers.py` - Validate NDF patterns

## Performance Optimization

### 1. Batch Requests
Fetch all data in one request:

```javascript
// ✅ Good - Single request
const securities = [spot, ...forwards, ...volatilities]
const response = await fetchBloombergData(securities)

// ❌ Bad - Multiple requests
const spotData = await fetchBloombergData([spot])
const forwardData = await fetchBloombergData(forwards)
```

### 2. Error Handling
Graceful degradation for missing data:

```javascript
try {
  const data = await fetchForwardCurves(pair)
  if (!data || data.length === 0) {
    setError('No forward data available')
  }
} catch (err) {
  console.error('Forward curve fetch failed:', err)
  setError('Failed to load forward curves')
}
```

## Deployment Considerations

### Development Mode
```bash
# No cache for fresh data
ENABLE_CACHE=false python bloomberg-gateway-enhanced.py
```

### Production Mode
```bash
# Enable Redis cache
ENABLE_CACHE=true REDIS_URL=redis://localhost:6379 python bloomberg-gateway-enhanced.py
```

### Azure VM Management
```bash
# Check API health
az vm run-command invoke -g bloomberg-terminal-rg -n bloomberg-vm-02 \
  --command-id RunPowerShellScript \
  --scripts "curl http://localhost:8080/health"

# Restart API if needed
az vm run-command invoke -g bloomberg-terminal-rg -n bloomberg-vm-02 \
  --command-id RunPowerShellScript \
  --scripts "Get-Process python* | Stop-Process -Force; cd C:\BloombergAPI; Start-Process python.exe -ArgumentList 'main.py'"
```

## Future Enhancements

### 1. Dynamic NDF Discovery
Instead of hardcoded mappings, discover NDF patterns:
```javascript
// Potential implementation
const discoverNDFPattern = async (pair: string) => {
  const patterns = ['IRN', 'NTN', 'KWN', ...]
  for (const pattern of patterns) {
    const result = await validateTicker(`${pattern}1M Curncy`)
    if (result.valid) return pattern
  }
  return null
}
```

### 2. Database-Driven Configuration
Move NDF mappings to PostgreSQL:
```sql
CREATE TABLE ndf_mappings (
  currency_pair VARCHAR(6) PRIMARY KEY,
  ndf_format VARCHAR(3),
  coverage_start VARCHAR(3),
  coverage_end VARCHAR(3),
  pip_factor INTEGER
);
```

### 3. Real-time Updates
Implement WebSocket for live data:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws')
ws.on('message', (data) => {
  updateForwardCurves(JSON.parse(data))
})
```

## Debugging Checklist

When something doesn't work:

1. **Check Gateway**: Is `bloomberg-gateway-enhanced.py` running?
2. **Check VM API**: `curl http://20.172.249.92:8080/health`
3. **Check Console**: Look for error messages and debug logs
4. **Check Network**: Browser DevTools → Network tab
5. **Check Tickers**: Validate ticker format with manual curl
6. **Check Coverage**: Some currencies have limited data (normal)
7. **Check Terminal**: Is Bloomberg Terminal logged in on VM?

Remember: Always show real data, even if it means showing "No data available".