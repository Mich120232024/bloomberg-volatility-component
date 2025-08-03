/**
 * YIELD CURVE SERVICE - Database-driven Bloomberg integration
 * Replaces hardcoded configurations with PostgreSQL ticker repository
 */

import { Currency } from '../constants/currencies'

interface CurvePoint {
  tenor: number     // Days to maturity
  years: number     // Years to maturity for proper scaling
  rate: number      // Rate in %
  label: string     // Display label
  ticker: string    // Bloomberg ticker
  instrumentType: 'money_market' | 'swap' | 'bond'
  isInterpolated?: boolean
}

interface DatabaseTicker {
  ticker: string
  tenor?: string
  years?: number
  label?: string
  category: string
  subcategory?: string
}

class YieldCurveService {
  private apiUrl: string

  constructor() {
    this.apiUrl = import.meta.env.DEV ? 'http://localhost:8000' : 'http://20.172.249.92:8080'
  }

  /**
   * Get available yield curves from database
   */
  async getAvailableCurves(): Promise<string[]> {
    try {
      const response = await fetch(`${this.apiUrl}/api/database/curves`, {
        headers: {
          'Authorization': 'Bearer test',
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const result = await response.json()
      return result.curves || []
    } catch (error) {
      console.error('Failed to fetch available curves:', error)
      return []
    }
  }

  /**
   * Get tickers for a specific curve from database
   */
  async getCurveTickersFromDatabase(curveName: string): Promise<DatabaseTicker[]> {
    try {
      const response = await fetch(`${this.apiUrl}/api/database/curve-tickers`, {
        method: 'POST',
        headers: {
          'Authorization': 'Bearer test',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ curve_name: curveName })
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const result = await response.json()
      return result.tickers || []
    } catch (error) {
      console.error('Failed to fetch curve tickers from database:', error)
      return []
    }
  }

  /**
   * Get yield curve data for a currency using database-driven approach
   */
  async getCurveData(currency: Currency): Promise<CurvePoint[]> {
    try {
      // Map currency to curve name (temporary until database has proper mapping)
      const curveMapping: Record<Currency, string> = {
        'JPY': 'JPY_OIS',
        'CHF': 'CHF_IRS', 
        'GBP': 'GBP_IRS',
        'EUR': 'EUR_IRS',
        'AUD': 'AUD_IRS',
        'CAD': 'CAD_IRS',
        // Add more mappings as needed
        'USD': 'USD_SOFR_OIS', // Will fall back to Bloomberg API if not in DB
        'NZD': 'NZD_IRS',
        'SEK': 'SEK_IRS',
        'NOK': 'NOK_IRS',
        'DKK': 'DKK_IRS',
        'ISK': 'ISK_IRS'
      }

      const curveName = curveMapping[currency]
      if (!curveName) {
        console.warn(`No curve mapping for currency ${currency}`)
        return []
      }

      // Get tickers from database
      const dbTickers = await this.getCurveTickersFromDatabase(curveName)
      if (dbTickers.length === 0) {
        console.warn(`No tickers found for curve ${curveName}`)
        return []
      }

      console.log(`📊 Found ${dbTickers.length} tickers for ${curveName}:`, dbTickers.map(t => t.ticker))

      // Get Bloomberg data for all tickers
      const bloombergTickers = dbTickers.map(t => t.ticker)
      const response = await fetch(`${this.apiUrl}/api/bloomberg/reference`, {
        method: 'POST',
        headers: {
          'Authorization': 'Bearer test',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          securities: bloombergTickers,
          fields: ['PX_LAST', 'YLD_YTM_MID', 'LAST_UPDATE']
        })
      })

      if (!response.ok) {
        throw new Error(`Bloomberg API error: HTTP ${response.status}`)
      }

      const result = await response.json()
      
      if (!result.success) {
        throw new Error(`Bloomberg API failed: ${result.error}`)
      }

      // Process results into curve points
      const curvePoints: CurvePoint[] = []
      const securitiesData = result.data?.securities_data || []

      securitiesData.forEach((secData: any, index: number) => {
        if (secData.success && index < dbTickers.length) {
          const dbTicker = dbTickers[index]
          const rate = secData.fields?.YLD_YTM_MID || secData.fields?.PX_LAST

          if (rate !== null && rate !== undefined) {
            // Generate approximate tenor info if missing from database
            const years = this.estimateYearsFromTicker(dbTicker.ticker)
            const label = this.generateLabel(years)
            
            curvePoints.push({
              tenor: Math.round(years * 365),
              years: years,
              rate: rate,
              label: dbTicker.label || label,
              ticker: dbTicker.ticker,
              instrumentType: this.mapCategoryToInstrumentType(dbTicker.category)
            })

            console.log(`✅ ${dbTicker.ticker}: ${rate}% (${label})`)
          }
        }
      })

      // Sort by years
      curvePoints.sort((a, b) => a.years - b.years)
      return curvePoints

    } catch (error) {
      console.error(`Failed to get curve data for ${currency}:`, error)
      return []
    }
  }

  /**
   * Estimate years from Bloomberg ticker pattern
   */
  private estimateYearsFromTicker(ticker: string): number {
    // Extract tenor from common Bloomberg patterns
    if (ticker.includes('A') && ticker.includes('BGN')) return 0.083  // 1M
    if (ticker.includes('B') && ticker.includes('BGN')) return 0.167  // 2M  
    if (ticker.includes('C') && ticker.includes('BGN')) return 0.25   // 3M
    if (ticker.includes('F') && ticker.includes('BGN')) return 0.5    // 6M
    if (ticker.includes('I') && ticker.includes('BGN')) return 0.75   // 9M
    if (ticker.includes('1') && ticker.includes('BGN')) return 1      // 1Y
    if (ticker.includes('2') && ticker.includes('BGN')) return 2      // 2Y
    if (ticker.includes('3') && ticker.includes('BGN')) return 3      // 3Y
    if (ticker.includes('5') && ticker.includes('BGN')) return 5      // 5Y
    if (ticker.includes('10') && ticker.includes('BGN')) return 10    // 10Y
    
    // Default fallback
    return 1
  }

  /**
   * Generate display label from years
   */
  private generateLabel(years: number): string {
    if (years < 0.08) return 'O/N'
    if (years < 0.17) return `${Math.round(years * 12)}M`
    if (years < 1) return `${Math.round(years * 12)}M`
    if (years === Math.floor(years)) return `${years}Y`
    return `${years.toFixed(1)}Y`
  }

  /**
   * Map database category to instrument type
   */
  private mapCategoryToInstrumentType(category: string): 'money_market' | 'swap' | 'bond' {
    switch (category.toLowerCase()) {
      case 'money_market': return 'money_market'
      case 'government_bond': return 'bond'
      case 'ois_swap':
      case 'irs':
      default: return 'swap'
    }
  }
}

export const yieldCurveService = new YieldCurveService()
export type { CurvePoint }