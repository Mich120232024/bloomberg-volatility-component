/**
 * Yield Curve Ticker Service
 * Maps currencies to their proper Bloomberg yield curve tickers from the central repository
 */

export interface YieldCurveTicker {
  ticker: string
  tenor: number  // Days to maturity
  label: string  // Display label
  type: 'money_market' | 'ois' | 'government_bond' | 'swap'
}

export interface YieldCurveConfig {
  title: string
  currency: string
  instruments: YieldCurveTicker[]
}

// Real ticker mappings from central_bloomberg_ticker_repository_v3.json
const YIELD_CURVE_CONFIGS: Record<string, YieldCurveConfig> = {
  USD: {
    title: 'USD OIS/SOFR Yield Curve',
    currency: 'USD',
    instruments: [
      // Money Market (short end)
      { ticker: 'SOFRRATE Index', tenor: 1, label: 'ON', type: 'money_market' },
      { ticker: 'US0001M Index', tenor: 30, label: '1M', type: 'money_market' },
      { ticker: 'US0003M Index', tenor: 90, label: '3M', type: 'money_market' },
      { ticker: 'US0006M Index', tenor: 180, label: '6M', type: 'money_market' },
      { ticker: 'US0012M Index', tenor: 365, label: '1Y', type: 'money_market' },
      
      // SOFR OIS (medium term)
      { ticker: 'USOSFR2 Curncy', tenor: 730, label: '2Y', type: 'ois' },
      { ticker: 'USOSFR3 Curncy', tenor: 1095, label: '3Y', type: 'ois' },
      { ticker: 'USOSFR5 Curncy', tenor: 1825, label: '5Y', type: 'ois' },
      { ticker: 'USOSFR7 Curncy', tenor: 2555, label: '7Y', type: 'ois' },
      { ticker: 'USOSFR10 Curncy', tenor: 3650, label: '10Y', type: 'ois' },
      
      // Government Bonds (long end)
      { ticker: 'USGG20Y Index', tenor: 7300, label: '20Y', type: 'government_bond' },
      { ticker: 'USGG30Y Index', tenor: 10950, label: '30Y', type: 'government_bond' }
    ]
  },
  
  EUR: {
    title: 'EUR OIS/ESTR Yield Curve',
    currency: 'EUR',
    instruments: [
      // Money Market
      { ticker: 'ESTR Index', tenor: 1, label: 'ON', type: 'money_market' },
      { ticker: 'EUR001M Index', tenor: 30, label: '1M', type: 'money_market' },
      { ticker: 'EUR003M Index', tenor: 90, label: '3M', type: 'money_market' },
      { ticker: 'EUR006M Index', tenor: 180, label: '6M', type: 'money_market' },
      { ticker: 'EUR012M Index', tenor: 365, label: '1Y', type: 'money_market' },
      
      // ESTR OIS
      { ticker: 'EESWE2 Curncy', tenor: 730, label: '2Y', type: 'ois' },
      { ticker: 'EESWE3 Curncy', tenor: 1095, label: '3Y', type: 'ois' },
      { ticker: 'EESWE5 Curncy', tenor: 1825, label: '5Y', type: 'ois' },
      { ticker: 'EESWE10 Curncy', tenor: 3650, label: '10Y', type: 'ois' },
      
      // German Government Bonds
      { ticker: 'GDBR30 Index', tenor: 10950, label: '30Y', type: 'government_bond' }
    ]
  },
  
  GBP: {
    title: 'GBP Money Market Curve',
    currency: 'GBP',
    instruments: [
      // Only money market rates available according to repository
      { ticker: 'BP0003M Index', tenor: 90, label: '3M', type: 'money_market' },
      { ticker: 'BP0006M Index', tenor: 180, label: '6M', type: 'money_market' },
      { ticker: 'BP0012M Index', tenor: 365, label: '1Y', type: 'money_market' }
    ]
  },
  
  JPY: {
    title: 'JPY Money Market Curve',
    currency: 'JPY',
    instruments: [
      { ticker: 'JY0003M Index', tenor: 90, label: '3M', type: 'money_market' },
      { ticker: 'JY0006M Index', tenor: 180, label: '6M', type: 'money_market' }
    ]
  },
  
  CHF: {
    title: 'CHF Money Market Curve',
    currency: 'CHF',
    instruments: [
      { ticker: 'SF0003M Index', tenor: 90, label: '3M', type: 'money_market' },
      { ticker: 'SF0006M Index', tenor: 180, label: '6M', type: 'money_market' }
    ]
  },
  
  // Emerging Markets from the repository
  AED: {
    title: 'AED Money Market & Swaps',
    currency: 'AED',
    instruments: [
      { ticker: 'AEDON Index', tenor: 1, label: 'ON', type: 'money_market' },
      { ticker: 'AED1M Index', tenor: 30, label: '1M', type: 'money_market' },
      { ticker: 'AED3M Index', tenor: 90, label: '3M', type: 'money_market' },
      { ticker: 'AED6M Index', tenor: 180, label: '6M', type: 'money_market' },
      { ticker: 'AESO3 Curncy', tenor: 1095, label: '3Y', type: 'swap' }
    ]
  },
  
  SAR: {
    title: 'SAR Money Market & Swaps',
    currency: 'SAR',
    instruments: [
      { ticker: 'SARON Index', tenor: 1, label: 'ON', type: 'money_market' },
      { ticker: 'SAR1M Index', tenor: 30, label: '1M', type: 'money_market' },
      { ticker: 'SAR3M Index', tenor: 90, label: '3M', type: 'money_market' },
      { ticker: 'SAR6M Index', tenor: 180, label: '6M', type: 'money_market' },
      { ticker: 'SASO1 Curncy', tenor: 365, label: '1Y', type: 'swap' },
      { ticker: 'SASO2 Curncy', tenor: 730, label: '2Y', type: 'swap' },
      { ticker: 'SASO5 Curncy', tenor: 1825, label: '5Y', type: 'swap' }
    ]
  },
  
  ISK: {
    title: 'ISK Money Market, Swaps & Bonds',
    currency: 'ISK',
    instruments: [
      // Money Market
      { ticker: 'ISKON Index', tenor: 1, label: 'ON', type: 'money_market' },
      { ticker: 'ISK1M Index', tenor: 30, label: '1M', type: 'money_market' },
      { ticker: 'ISK3M Index', tenor: 90, label: '3M', type: 'money_market' },
      
      // Swaps
      { ticker: 'ISSO1 Curncy', tenor: 365, label: '1Y', type: 'swap' },
      { ticker: 'ISSO2 Curncy', tenor: 730, label: '2Y', type: 'swap' },
      { ticker: 'ISSO3 Curncy', tenor: 1095, label: '3Y', type: 'swap' },
      
      // Government Bonds
      { ticker: 'GISK5Y Index', tenor: 1825, label: '5Y', type: 'government_bond' },
      { ticker: 'GISK10Y Index', tenor: 3650, label: '10Y', type: 'government_bond' }
    ]
  }
}

export function getYieldCurveConfig(currency: string): YieldCurveConfig | null {
  return YIELD_CURVE_CONFIGS[currency] || null
}

export function getAvailableCurrencies(): string[] {
  return Object.keys(YIELD_CURVE_CONFIGS).sort()
}

export function getAllTickers(): string[] {
  const allTickers: string[] = []
  Object.values(YIELD_CURVE_CONFIGS).forEach(config => {
    config.instruments.forEach(instrument => {
      allTickers.push(instrument.ticker)
    })
  })
  return [...new Set(allTickers)].sort()
}

export function getCurrencyTitle(currency: string): string {
  const config = YIELD_CURVE_CONFIGS[currency]
  return config ? config.title : `${currency} Yield Curve`
}