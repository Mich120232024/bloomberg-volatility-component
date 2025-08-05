# NDF (Non-Deliverable Forward) Implementation Guide

## Overview

This document details the implementation of Non-Deliverable Forward (NDF) support in the FX Forward Curves component, added in August 2025.

## Background

### What are NDFs?
Non-Deliverable Forwards are derivative instruments used for currencies with capital controls or restrictions. Unlike standard forwards, NDFs are cash-settled in a freely convertible currency (usually USD) rather than physical delivery of the restricted currency.

### Why Special Tickers?
Bloomberg uses different ticker formats for NDFs because:
1. They trade in different markets (offshore vs onshore)
2. Different settlement mechanisms
3. Regulatory restrictions on certain currencies
4. Different liquidity profiles

## Discovery Process

### Initial Problem
Several currencies showed no forward data despite being major trading pairs:
- USDINR (Indian Rupee)
- USDTWD (Taiwan Dollar)
- USDIDR (Indonesian Rupiah)
- USDBRL (Brazilian Real)
- Others...

### Analysis Performed
1. **Comprehensive Coverage Analysis** (`currency_forward_coverage_analysis.py`)
   - Tested all 45 currency pairs
   - Found 7 currencies with spot-only data
   - Found 3 currencies with limited forward coverage

2. **NDF Ticker Discovery** (`check_ndf_tickers.py`)
   - Tested known NDF patterns from Bloomberg documentation
   - Discovered working ticker formats for 9 currencies
   - Mapped coverage limits for each

### Results
- **32 pairs (71.1%)** have full 5Y standard forward coverage
- **9 pairs (20%)** require NDF tickers for any/extended coverage
- **2 pairs (4.4%)** have no forward market at all (USDPEN, USDARS)
- **Overall: 95.6% coverage** achieved with NDF support

## Implementation Details

### 1. NDF Mappings (`/src/constants/ndfMappings.ts`)

```typescript
export const NDF_MAPPINGS: Record<string, NDFMapping> = {
  USDINR: { format: 'IRN', coverage: '1W-6M', example: 'IRN1M Curncy' },
  USDTWD: { format: 'NTN', coverage: '1W-5Y', example: 'NTN1M Curncy' },
  // ... etc
}
```

### 2. Ticker Selection Logic

```typescript
// In FXForwardCurvesTab.tsx
if (usesNDF(pair) && ndfMapping?.format) {
  // Use NDF tickers
  for (const tenor of tenors) {
    const ndfTicker = getNDFTicker(pair, tenor)
    if (ndfTicker) securities.push(ndfTicker)
  }
} else {
  // Use standard forward tickers
  securities.push(...tenors.map(tenor => `${pair}${tenor} Curncy`))
}
```

### 3. Response Parsing

The component now handles both ticker formats:
```typescript
// Standard format: EURUSD1M Curncy
let tenorMatch = ticker.match(new RegExp(`${pair}(\\d+[WMY]) Curncy`))

// NDF format: IRN1M Curncy
if (!tenorMatch && needsNDF) {
  const ndfMatch = ticker.match(new RegExp(`${ndfMapping.format}(\\d+[WMY]) Curncy`))
  if (ndfMatch) tenor = ndfMatch[1]
}
```

## NDF Ticker Reference

### Complete Mapping Table

| Currency Pair | Standard Coverage | NDF Format | NDF Coverage | Notes |
|---------------|-------------------|------------|--------------|--------|
| USDINR | None | IRN | 1W-6M | Indian capital controls |
| USDTWD | None | NTN | 1W-5Y | Taiwan restrictions |
| USDKRW | Up to 9M | KWN | 1W-5Y | Extended coverage via NDF |
| USDIDR | None | IHN | 1W-9M | Indonesian restrictions |
| USDPHP | Up to 9M | PPN | 1W-9M | Standard + NDF available |
| USDMYR | Up to 9M | MRN | 1W-9M | Malaysian controls |
| USDBRL | None | BCN | 1W-9M | Brazilian restrictions |
| USDCLP | None | CHN | 1W-9M | Chilean peso NDF |
| USDCOP | Up to 3Y | CLN | 1W-3Y | Colombian peso |

### Important Notes

1. **CLN is COP not CLP**: Initial discovery showed CLN tickers returning "COP NDF POINTS" - these are Colombian Peso NDFs, not Chilean.

2. **Limited Liquidity**: NDF markets often have sparse tenor coverage:
   - USDINR: Only 5 data points (1W, 1M, 2M, 3M, 6M)
   - This creates "incomplete" looking curves but is normal

3. **No 2W Data**: Many NDFs skip the 2W tenor entirely

4. **USDPEN/USDARS**: No forward market exists (neither standard nor NDF)

## Forward Points Calculation

All NDF tickers return forward points, same as standard forwards:

```javascript
// Bloomberg returns points, not outright rates
const forwardPoints = value  // e.g., 15.3 for IRN1M

// Calculate outright forward rate
const pipFactor = pair.includes('JPY') ? 100 : 10000
const forwardRate = spotRate + (forwardPoints / pipFactor)

// For USDINR: 87.8038 + (15.3 / 10000) = 87.8191
```

## Testing & Verification

### Console Output
When selecting a currency with NDF support:
```
🔄 Using NDF tickers for USDINR (IRN format)
📊 NDF Coverage: 1W-6M
📡 Fetching data for USDINR:
   Spot ticker: USDINR Curncy
   Forward tickers (first 5): ['IRN1W Curncy', 'IRN1M Curncy', 'IRN2M Curncy', 'IRN3M Curncy', 'IRN6M Curncy']
✅ Matched NDF ticker: IRN1M Curncy -> tenor: 1M
```

### Manual Testing
```bash
# Test NDF ticker
curl -X POST http://localhost:8000/api/bloomberg/reference \
  -H "Authorization: Bearer test" \
  -H "Content-Type: application/json" \
  -d '{"securities": ["IRN1M Curncy", "NTN1M Curncy"], "fields": ["PX_LAST", "NAME"]}'
```

## Future Maintenance

1. **Market Convention Changes**: NDF ticker formats may change as markets evolve
2. **New Restricted Currencies**: May need to add new NDF mappings
3. **Coverage Extensions**: Some NDFs may extend coverage as liquidity improves
4. **Database Integration**: Consider storing NDF mappings in PostgreSQL for dynamic updates

## Lessons Learned

1. **Always Check Alternative Tickers**: When standard tickers show no data, investigate market conventions
2. **Sparse Data is Normal**: NDF markets have limited liquidity - don't expect smooth curves
3. **Documentation Matters**: This implementation would have been faster with prior knowledge of NDF conventions
4. **Real Data Only**: The previous approach of synthetic fallbacks masked these data gaps