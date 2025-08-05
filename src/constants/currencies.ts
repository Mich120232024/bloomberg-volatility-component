// Comprehensive currency list following Bloomberg conventions
// Bloomberg convention: USD as base for EM and metals, quote for G10

export const G10_CURRENCIES = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'AUD', 'CAD', 'NOK', 'SEK', 'NZD'] as const

export const EMERGING_MARKET_CURRENCIES = [
  'BRL', 'CNH', 'CZK', 'HUF', 'ILS', 'INR', 'KRW', 'MXN', 'PLN', 'RUB', 'SGD', 'THB', 'TRY', 'TWD', 'ZAR',
  'PHP', 'HKD', 'DKK'
] as const

export const PRECIOUS_METALS = ['XAU', 'XAG'] as const

// All currencies combined
export const ALL_CURRENCIES = [...G10_CURRENCIES, ...EMERGING_MARKET_CURRENCIES, ...PRECIOUS_METALS] as const

// All G10 USD pairs following Bloomberg convention
export const G10_USD_PAIRS = [
  'EURUSD', 'GBPUSD', 'AUDUSD', 'NZDUSD',  // USD as quote
  'USDJPY', 'USDCHF', 'USDCAD', 'USDSEK', 'USDNOK'  // USD as base
] as const

// All EM USD pairs (USD always base)
export const EM_USD_PAIRS = [
  'USDBRL', 'USDCNH', 'USDCZK', 'USDHUF', 'USDILS', 
  'USDINR', 'USDKRW', 'USDMXN', 'USDPLN', 'USDRUB', 
  'USDSGD', 'USDTHB', 'USDTRY', 'USDTWD', 'USDZAR',
  'USDPHP', 'USDHKD', 'USDDKK'
] as const

// Precious metal pairs (USD as quote)
export const METAL_PAIRS = ['XAUUSD', 'XAGUSD'] as const

// Major EUR crosses
export const EUR_CROSSES = [
  'EURGBP', 'EURJPY', 'EURCHF', 'EURAUD', 'EURCAD', 'EURNZD',
  'EURSEK', 'EURNOK', 'EURPLN', 'EURCZK', 'EURHUF', 'EURTRY'
] as const

// Major GBP crosses
export const GBP_CROSSES = [
  'GBPJPY', 'GBPCHF', 'GBPAUD', 'GBPCAD', 'GBPNZD', 'GBPSEK', 'GBPNOK'
] as const

// Major JPY crosses
export const JPY_CROSSES = [
  'EURJPY', 'GBPJPY', 'AUDJPY', 'NZDJPY', 'CADJPY', 'CHFJPY'
] as const

// Other important crosses
export const OTHER_CROSSES = [
  'AUDCAD', 'AUDCHF', 'AUDNZD', 'NZDCAD', 'NZDCHF', 'CADCHF',
  'NOKJPY', 'SEKJPY', 'ZARJPY', 'MXNJPY', 'TRYJPY'
] as const

// All FX pairs combined
export const ALL_FX_PAIRS = [
  ...G10_USD_PAIRS,
  ...EM_USD_PAIRS,
  ...METAL_PAIRS,
  ...EUR_CROSSES,
  ...GBP_CROSSES,
  ...JPY_CROSSES,
  ...OTHER_CROSSES
] as const

// Type exports
export type G10Currency = typeof G10_CURRENCIES[number]
export type EMCurrency = typeof EMERGING_MARKET_CURRENCIES[number]
export type PreciousMetal = typeof PRECIOUS_METALS[number]
export type Currency = G10Currency | EMCurrency | PreciousMetal
export type FXPair = typeof ALL_FX_PAIRS[number]

// Helper functions
export function isG10Currency(currency: string): currency is G10Currency {
  return G10_CURRENCIES.includes(currency as G10Currency)
}

export function isEMCurrency(currency: string): currency is EMCurrency {
  return EMERGING_MARKET_CURRENCIES.includes(currency as EMCurrency)
}

export function isPreciousMetal(currency: string): currency is PreciousMetal {
  return PRECIOUS_METALS.includes(currency as PreciousMetal)
}

// Bloomberg ticker helpers
export function getSpotTicker(pair: string): string {
  return `${pair} Curncy`
}

export function getVolatilityTicker(pair: string, tenor: string, strikeType?: 'ATM' | 'RR' | 'BF', delta?: number): string {
  if (strikeType === 'ATM' || !strikeType) {
    return tenor === 'ON' ? `${pair}VON Curncy` : `${pair}V${tenor} BGN Curncy`
  }
  const deltaStr = delta ? delta.toString() : '25'
  const typeStr = strikeType === 'RR' ? 'R' : 'B'
  return `${pair}${deltaStr}${typeStr}${tenor} BGN Curncy`
}

export function getForwardTicker(pair: string, tenor: string): string {
  return `${pair}${tenor} Curncy`
}