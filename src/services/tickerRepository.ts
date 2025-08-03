// Central Bloomberg Ticker Repository Service
import tickerData from '../../tools/central_bloomberg_ticker_repository_v3.json'

export interface TickerRepository {
  metadata: {
    version: string
    api: {
      endpoint: string
      methods: {
        reference: string
        historical: string
      }
      auth: string
    }
  }
  yield_curve_construction: {
    [currency: string]: {
      money_market?: {
        overnight?: string[]
        term?: string[]
        reference_rate?: string
      }
      swaps?: {
        sofr?: string[]
        ois?: string[]
      }
      government_bonds?: {
        short?: string[]
        medium?: string[]
        long?: string[]
        germany?: string[]
        france?: string[]
      }
    }
  }
  fx_volatility_surfaces: {
    major_pairs: {
      [pair: string]: {
        atm?: string[]
        '25d_rr'?: string[]
        '25d_bf'?: string[]
        forwards?: string[]
      }
    }
    emerging_pairs: {
      [pair: string]: {
        atm?: string[]
        options?: string[]
        forwards?: string[]
      }
    }
  }
}

class TickerRepositoryService {
  private data: TickerRepository
  
  constructor() {
    this.data = tickerData as TickerRepository
  }
  
  // Get yield curve tickers for a currency
  getYieldCurveTickers(currency: string): string[] {
    const curveData = this.data.yield_curve_construction[currency]
    if (!curveData) {
      console.warn(`No curve data found for ${currency}`)
      return []
    }
    
    const tickers: string[] = []
    
    // Collect all tickers from different categories
    if (curveData.money_market) {
      if (curveData.money_market.overnight) tickers.push(...curveData.money_market.overnight)
      if (curveData.money_market.term) tickers.push(...curveData.money_market.term)
    }
    
    if (curveData.swaps) {
      if (curveData.swaps.sofr) tickers.push(...curveData.swaps.sofr)
      if (curveData.swaps.ois) tickers.push(...curveData.swaps.ois)
    }
    
    if (curveData.government_bonds) {
      if (curveData.government_bonds.short) tickers.push(...curveData.government_bonds.short)
      if (curveData.government_bonds.medium) tickers.push(...curveData.government_bonds.medium)
      if (curveData.government_bonds.long) tickers.push(...curveData.government_bonds.long)
      if (curveData.government_bonds.germany) tickers.push(...curveData.government_bonds.germany)
      if (curveData.government_bonds.france) tickers.push(...curveData.government_bonds.france)
    }
    
    return tickers
  }
  
  // Get FX forward tickers for a pair
  getFXForwardTickers(pair: string): string[] {
    // Check major pairs first
    const majorPair = this.data.fx_volatility_surfaces.major_pairs[pair]
    if (majorPair?.forwards) {
      return majorPair.forwards
    }
    
    // Check emerging pairs
    const emergingPair = this.data.fx_volatility_surfaces.emerging_pairs[pair]
    if (emergingPair?.forwards) {
      return emergingPair.forwards
    }
    
    console.warn(`No forward tickers found for ${pair}`)
    return []
  }
  
  // Get volatility surface tickers
  getVolatilitySurfaceTickers(pair: string): {
    atm: string[]
    rr: string[]
    bf: string[]
  } {
    const result = {
      atm: [] as string[],
      rr: [] as string[],
      bf: [] as string[]
    }
    
    // Check major pairs
    const majorPair = this.data.fx_volatility_surfaces.major_pairs[pair]
    if (majorPair) {
      if (majorPair.atm) result.atm = majorPair.atm
      if (majorPair['25d_rr']) result.rr = majorPair['25d_rr']
      if (majorPair['25d_bf']) result.bf = majorPair['25d_bf']
    }
    
    // Check emerging pairs
    const emergingPair = this.data.fx_volatility_surfaces.emerging_pairs[pair]
    if (emergingPair) {
      if (emergingPair.atm) result.atm.push(...emergingPair.atm)
      // Some emerging pairs have combined options tickers
      if (emergingPair.options) {
        emergingPair.options.forEach(ticker => {
          if (ticker.includes('R')) result.rr.push(ticker)
          if (ticker.includes('B')) result.bf.push(ticker)
        })
      }
    }
    
    return result
  }
  
  // Get API configuration
  getAPIConfig() {
    return this.data.metadata.api
  }
  
  // Get reference rate for a currency
  getReferenceRate(currency: string): string | null {
    const curveData = this.data.yield_curve_construction[currency]
    return curveData?.money_market?.reference_rate || null
  }
}

// Export singleton instance
export const tickerRepository = new TickerRepositoryService()