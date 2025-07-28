# FX Options Volatility Surface Dashboard

A professional-grade React application for visualizing and analyzing FX options volatility surfaces using real-time Bloomberg Terminal data.

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

### 3. Rate Curves (NEW)
- **Yield Curves**: Government bond yields for 8 major currencies
  - USD: Treasury Bills + Treasury Bonds
  - EUR: German Bunds + EURIBOR rates
  - GBP: UK Gilts
  - JPY: Japanese Government Bonds
  - CHF: Swiss Government Bonds
  - AUD/CAD/NZD: Government bonds
- **FX Forward Curves**: OTC forward rates for 10+ currency pairs
  - Major pairs: EURUSD, GBPUSD, USDJPY, USDCHF, AUDUSD
  - Cross pairs: EURGBP, EURJPY, GBPJPY
  - 2-year maximum tenor for forwards
- **Bloomberg Integration**: Real ticker transparency in tooltips
- **Realistic Scaling**: Proper time-to-maturity representation

### 4. Historical Analysis
- **Time Series Charts**: Historical volatility trends
- **Date Range Selection**: Flexible historical data queries
- **Comparative Analysis**: Multi-currency comparison capabilities

### 5. Options Pricing
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
- **Spot rates**: `EURUSD Curncy`
- **Forward points**: `EUR1M Curncy`, `EUR3M Curncy`
- **Calculation**: Forward Rate = Spot + (Points / Pip Divisor)

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
│   ├── RateCurvesTabD3.tsx      # Rate curves with D3.js
│   ├── VolatilityAnalysisTab.tsx # Volatility analysis
│   └── MainAppContainer.tsx      # Main app navigation
├── api/
│   ├── bloomberg.ts             # API client
│   └── DataValidator.ts         # Data validation
└── contexts/
    └── ThemeContext.tsx         # Theme management
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

### Data Quality
- Invalid ATM values are handled gracefully
- Missing forward tenors are filtered out
- Swiss rates corrected (was showing 4% instead of 0.4%)

## License

Private project - Bloomberg Terminal license required for data access.

---
Last updated: 2025-01-25