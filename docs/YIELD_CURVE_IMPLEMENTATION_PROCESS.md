# Yield Curve Implementation Process

## Complete 4-Step Process for Currency Yield Curves

This document outlines the systematic process used to implement USD OIS curve, which can be replicated for other currencies.

### Step 1: Ticker Discovery

Use Bloomberg API ticker discovery to find all relevant OIS/swap tickers for the currency:

```bash
# Discover OIS tickers for a currency
curl -X POST "http://localhost:8000/api/bloomberg/ticker-discovery" \
  -H "Authorization: Bearer test" \
  -H "Content-Type: application/json" \
  -d '{"search_type": "ois", "currency": "USD", "max_results": 50}'
```

Key tickers to look for:
- **Overnight rate**: SOFRRATE Index (USD), ESTR Index (EUR), SONIA Index (GBP)
- **Short-term OIS**: 1W, 2W, 1M, 2M, 3M (e.g., USSOA, USSOB, USSOC)
- **Medium-term OIS**: 6M, 9M, 1Y, 2Y, 3Y, 5Y
- **Long-term OIS**: 7Y, 10Y, 15Y, 20Y, 30Y

### Step 2: Ticker Verification

Verify discovered tickers work with Bloomberg API:

```bash
# Validate tickers return live prices
curl -X POST "http://localhost:8000/api/bloomberg/validate-tickers" \
  -H "Authorization: Bearer test" \
  -H "Content-Type: application/json" \
  -d '["SOFRRATE Index", "USSOA Curncy", "USSOB Curncy", "USSOC Curncy"]'
```

### Step 3: Database Population

Add tickers to PostgreSQL database with proper tenor values:

```python
# Key fields for bloomberg_tickers table:
- bloomberg_ticker: The exact Bloomberg ticker
- currency_code: USD, EUR, GBP, etc.
- category: 'RATE' for OIS
- tenor: Display label (O/N, 1M, 2M, etc.)
- tenor_numeric: Days to maturity
- curve_name: 'USD_OIS', 'EUR_OIS', etc.

# Tenor_numeric mapping:
- O/N (overnight): 1 day
- 1W: 7 days
- 1M: 30 days
- 3M: 90 days
- 6M: 180 days
- 1Y: 365 days
- 2Y+: Store as years (gateway converts to days)
```

### Step 4: Frontend Visualization

The frontend automatically picks up curves from the gateway `/api/curves/{currency}` endpoint.

Key features implemented:
- **Dynamic zoom**: Range slider 1-30 years
- **Three-segment scale**: Equal visual weight to 0-1Y, 1-5Y, 5-30Y segments
- **Background shading**: Visual separation of segments
- **Logarithmic scale option**: Better short-end visibility

## USD OIS Implementation Details

### Tickers Added
```
SOFRRATE Index    O/N    1 day      # Overnight SOFR rate
USSOA Curncy      1M     30 days    # 1-month OIS
USSOB Curncy      2M     60 days    # 2-month OIS  
USSOC Curncy      3M     90 days    # 3-month OIS
USSOD Curncy      4M     120 days   # 4-month OIS
... continuing to ...
USSO30 Curncy     30Y    30 years   # 30-year OIS
```

### Gateway Logic for Tenor Conversion

The gateway has special handling for tenor_days calculation:

```python
# Special cases:
if ticker == 'SOFRRATE Index':
    tenor_days = 1  # Overnight = 1 day
elif ticker in ['USSOA Curncy', 'USSOB Curncy', 'USSOC Curncy']:
    tenor_days = tenor_numeric  # Already in days
elif ticker in ['USSO15 Curncy', 'USSO20 Curncy', 'USSO30 Curncy']:
    tenor_days = tenor_numeric * 365  # Convert years to days
elif tenor_numeric < 100:
    tenor_days = tenor_numeric * 365  # Years for other long-term
else:
    tenor_days = tenor_numeric  # Already in days
```

### Frontend Three-Segment Scale

Custom x-axis scale divides chart into three equal segments:

```javascript
if (zoomRange === 30 && !useLogScale) {
    return (value: number) => {
        if (value <= 1) {
            // 0-1Y maps to first third
            return (value / 1) * (width / 3)
        } else if (value <= 5) {
            // 1-5Y maps to second third  
            return (width / 3) + ((value - 1) / 4) * (width / 3)
        } else {
            // 5-30Y maps to final third
            return (2 * width / 3) + ((value - 5) / 25) * (width / 3)
        }
    }
}
```

## Replication Process for Other Currencies

### EUR OIS Curve
1. Discover: Search for ESTR-based OIS tickers
2. Key overnight: ESTR Index
3. OIS pattern: EESWE* (e.g., EESWE1M, EESWE3M, EESWE1Y)
4. Curve name: EUR_OIS

### GBP OIS Curve  
1. Discover: Search for SONIA-based OIS tickers
2. Key overnight: SONIA Index
3. OIS pattern: SONIO* (e.g., SONIOA, SONIOB for months)
4. Curve name: GBP_OIS

### JPY OIS Curve
1. Discover: Search for TONAR/TONA-based OIS tickers
2. Key overnight: MUTKCALM Index (TONAR)
3. OIS pattern: JYSO* (e.g., JYSOA BGN Curncy)
4. Curve name: JPY_OIS

## Common Issues and Solutions

1. **Missing short-term tickers**: Always check for 1M, 2M, 3M tickers
2. **Tenor conversion**: Ensure tenor_numeric is correctly set (days vs years)
3. **Ticker validation**: Some tickers may exist but not return data
4. **Database constraints**: Use minimal required columns when inserting

## Testing Commands

```bash
# Test curve endpoint
curl -s -X POST http://localhost:8000/api/curves/USD \
  -H "Authorization: Bearer test" \
  -H "Content-Type: application/json" | jq

# Check specific tenors
curl -s -X POST http://localhost:8000/api/curves/USD \
  -H "Authorization: Bearer test" \
  -H "Content-Type: application/json" | \
  jq '.points[] | select(.tenor == "O/N" or .tenor == "1M") | {ticker, tenor, tenor_days, rate}'
```

## Next Steps

Apply this process to implement curves for:
- [ ] EUR (ESTR OIS)
- [ ] GBP (SONIA OIS)  
- [ ] JPY (TONAR OIS)
- [ ] CHF (SARON OIS)
- [ ] Other G10 currencies