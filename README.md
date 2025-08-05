# Bloomberg Volatility Surface Component

A professional-grade React application for visualizing FX options volatility surfaces, forward curves, and rate curves using real-time Bloomberg Terminal data.

## Overview

This application provides comprehensive tools for analyzing FX options volatility, interest rate curves, and forward rates across multiple currency pairs, featuring real-time data integration with Bloomberg Terminal through an Azure-hosted API.

## Features

### 1. Volatility Surface Visualization
- **3D Surface Plot**: Interactive visualization of implied volatility across strikes and tenors
- **Real-time Data**: Direct integration with Bloomberg Terminal
- **Multiple Currency Pairs**: Support for major FX pairs (EURUSD, GBPUSD, USDJPY, etc.)
- **Strike Types**: At-the-money (ATM), Risk Reversals (RR), and Butterflies (BF)

### 2. Volatility Analysis Tools
- **Smile Analysis**: 2D visualization of volatility smile by tenor
- **Term Structure**: Volatility term structure analysis with realistic time scaling
- **Interactive Tooltips**: Detailed information including Bloomberg tickers
- **Data Quality Indicators**: Real-time data validation metrics

### 3. FX Forward Curves (ENHANCED - August 2025)
- **Extended Coverage**: Now supports forwards up to 5Y (previously 2Y)
- **45 Currency Pairs**: All major, EM, and cross pairs
- **NDF Support**: Automatic detection and usage of Non-Deliverable Forward tickers
  - USDINR: IRN format (1W-6M coverage)
  - USDTWD: NTN format (1W-5Y coverage)
  - USDKRW: KWN format (1W-5Y coverage)
  - And 6 more restricted currencies
- **Forward Points Calculation**: Spot + (Points / Pip Factor)
- **Interactive Hover Cards**: Shows spot, forward rate, FX net %, points, bid/ask
- **Real Bloomberg Tickers**: Full transparency in tooltips

### 4. Rate Curves
- **OIS Yield Curves**: 25+ currencies with database-driven configurations
- **Money Market to Long-term**: Seamless curve from O/N to 30Y
- **Dynamic Data Source**: PostgreSQL database for ticker management

### 5. Historical Analysis
- **Time Series Charts**: Historical volatility trends
- **Date Range Selection**: Flexible historical data queries
- **Comparative Analysis**: Multi-currency comparison capabilities

### 6. Options Pricing
- **Black-Scholes Calculator**: Real-time options pricing
- **Greeks Calculation**: Delta, Gamma, Vega, Theta, Rho
- **Payoff Diagrams**: Visual representation of option strategies

## Quick Start

### Prerequisites
- Node.js 18+
- Access to Bloomberg Terminal API (Azure VM)
- Python 3.9+ for gateway

### Installation
```bash
git clone <repository>
cd gzc-volatility-surface
npm install
```

### Development Setup
```bash
# Terminal 1: Start Bloomberg Gateway
cd tools
python bloomberg-gateway-enhanced.py

# Terminal 2: Start Frontend
npm run dev

# App available at: http://localhost:3501
```

## Technical Architecture

### Frontend
- **React 18** with TypeScript
- **Vite** for development and building
- **D3.js** for 2D charts (yield curves, forward curves)
- **Plotly.js** for 3D volatility surfaces
- **Tailwind CSS** for styling

### Backend
- **FastAPI** gateway (`bloomberg-gateway-enhanced.py`)
- **Bloomberg Terminal API** on Azure VM
- **Redis** caching (optional, disabled in dev)

### Data Flow
```
Bloomberg Terminal → Azure VM API → Local Gateway → React App
```

## Bloomberg Data Sources

### FX Options
- Volatility surfaces: `{PAIR}V{TENOR} BGN Curncy`
- ATM volatility: `{PAIR}V{TENOR} BGN Curncy`
- Risk reversals: `{PAIR}{DELTA}R{TENOR} BGN Curncy`
- Butterflies: `{PAIR}{DELTA}B{TENOR} BGN Curncy`

### Yield Curves
- **US Treasuries**: `USGG10YR Index`, `GB3 Govt`
- **German Bunds**: `GDBR10 Index`
- **Swiss Bonds**: `GSWISS10 Index`
- **UK Gilts**: `GUKG10 Index`
- **Japanese Bonds**: `GJGB10 Index`

### FX Forwards
- **Standard Forwards**: `{PAIR}{TENOR} Curncy` (e.g., `EURUSD1M Curncy`)
- **NDF Tickers**: Special format for restricted currencies
  - India: `IRN{TENOR} Curncy` (e.g., `IRN1M Curncy`)
  - Taiwan: `NTN{TENOR} Curncy` (e.g., `NTN1M Curncy`)
  - Korea: `KWN{TENOR} Curncy` (e.g., `KWN1M Curncy`)
- **Forward Points Calculation**: 
  ```javascript
  const pipFactor = pair.includes('JPY') ? 100 : 10000
  const forwardRate = spotRate + (forwardPoints / pipFactor)
  ```

## Configuration

### Gateway Settings
```python
# bloomberg-gateway-enhanced.py
ENABLE_CACHE = os.getenv('ENABLE_CACHE', 'false').lower() == 'true'
BLOOMBERG_API_URL = "http://20.172.249.92:8080"
```

### Environment Variables
- `ENABLE_CACHE`: Set to 'true' for production caching
- `REDIS_URL`: Redis connection string (optional)

## API Endpoints

### Bloomberg Gateway
- `GET /health` - Health check
- `GET /api/volatility/{pair}` - Volatility surface data
- `POST /api/bloomberg/reference` - Reference data
- `POST /api/bloomberg/historical` - Historical data

## Development

### Project Structure
```
src/
├── components/
│   ├── FXForwardCurvesTab.tsx    # FX forwards with NDF support
│   ├── RateCurvesTabD3.tsx       # OIS yield curves
│   ├── VolatilityAnalysisTab.tsx # Volatility analysis
│   └── MainAppContainer.tsx      # Main app navigation
├── api/
│   ├── bloomberg.ts              # API client with retry logic
│   └── DataValidator.ts          # Data validation (no fallbacks!)
├── constants/
│   ├── currencies.ts             # All 45 currency pairs
│   └── ndfMappings.ts           # NDF ticker mappings
└── contexts/
    └── ThemeContext.tsx          # Theme management
```

### Key Components
- **RateCurvesTabD3**: Yield curves and FX forwards using D3.js
- **VolatilityAnalysisTab**: 2D volatility smile and term structure
- **VolatilitySurfaceContainer**: 3D surface visualization

### Testing
```bash
# Test Bloomberg connection
curl http://localhost:8000/health

# Test specific ticker
curl -X POST http://localhost:8000/api/bloomberg/reference \
  -H "Content-Type: application/json" \
  -d '{"securities": ["EURUSD Curncy"], "fields": ["PX_LAST"]}'
```

## Troubleshooting

### Common Issues
1. **Connection refused**: Check if gateway is running on port 8000
2. **No data**: Verify Bloomberg Terminal is logged in
3. **Cache issues**: Set `ENABLE_CACHE=false` for development
4. **ERR_NETWORK_CHANGED**: Use localhost:8000 gateway, not direct VM connection

### FX Forward Curves Issues
1. **No forward data for restricted currencies (INR, TWD, etc.)**
   - Component now uses NDF tickers automatically
   - Check console for: "🔄 Using NDF tickers for USDINR (IRN format)"
   - Verify NDF mapping exists in `ndfMappings.ts`

2. **Incomplete forward curves**
   - USDINR: Only 5 points (1W, 1M, 2M, 3M, 6M) - this is normal
   - USDKRW: Should show full 5Y with NDF tickers
   - Check coverage limits in NDF mappings

3. **Wrong forward rates (e.g., 11.0 for EURUSD)**
   - Bloomberg returns forward POINTS not rates
   - Calculation: Forward = Spot + (Points / PipFactor)
   - PipFactor: 100 for JPY pairs, 10,000 for others

4. **CLN ticker confusion**
   - CLN format returns "COP NDF POINTS" - it's Colombian Peso (COP), not Chilean (CLP)
   - Chilean Peso uses CHN format
   - Always check the NAME field from Bloomberg to confirm currency

### Debugging Console Logs
```javascript
// NDF ticker detection
"🔄 Using NDF tickers for USDINR (IRN format)"
"📊 NDF Coverage: 1W-6M"

// Ticker requests
"📡 Fetching data for USDINR:"
"   Forward tickers (first 5): ['IRN1W Curncy', 'IRN1M Curncy', ...]"

// NDF parsing confirmation
"✅ Matched NDF ticker: IRN1M Curncy -> tenor: 1M"
```

### Data Quality Notes
- Bloomberg API sessions persist when Terminal UI is logged off
- Some currencies have no forward market (USDPEN, USDARS)
- NDF markets have limited liquidity - sparse curves are normal
- Always verify with Bloomberg Terminal for reference

### NDF Currency Coverage Summary
- **Full NDF support (9 currencies)**: USDINR, USDTWD, USDKRW, USDIDR, USDPHP, USDMYR, USDBRL, USDCLP, USDCOP
- **No forward market (2 currencies)**: USDPEN, USDARS
- **Standard forwards only (34 currencies)**: All other pairs use standard ticker format
- **Coverage achieved**: 95.6% (43 out of 45 currency pairs have forward data)

## License

Private project - Bloomberg Terminal license required for data access.

---
Last updated: 2025-08-05