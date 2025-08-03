/**
 * DATABASE API CLIENT
 * Provides access to PostgreSQL ticker repository
 */

const API_URL = import.meta.env.DEV ? 'http://localhost:8000' : 'http://20.172.249.92:8080'

export interface DatabaseTicker {
  ticker: string
  tenor?: string
  years?: number
  label?: string
  category: string
  subcategory?: string
  currency_code: string
}

export interface CurveInfo {
  curve_name: string
  ticker_count: number
}

/**
 * Get available yield curves from database
 */
export async function getAvailableCurves(): Promise<CurveInfo[]> {
  try {
    const response = await fetch(`${API_URL}/api/database/curves`, {
      headers: {
        'Authorization': 'Bearer test',
        'Content-Type': 'application/json'
      }
    })

    if (!response.ok) {
      console.error(`Failed to fetch curves: HTTP ${response.status}`)
      return []
    }

    const result = await response.json()
    return result.curves || []
  } catch (error) {
    console.error('Failed to fetch available curves:', error)
    return []
  }
}

/**
 * Get tickers for a specific curve
 */
export async function getCurveTickers(curveName: string): Promise<DatabaseTicker[]> {
  try {
    const response = await fetch(`${API_URL}/api/database/curve-tickers`, {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer test',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ curve_name: curveName })
    })

    if (!response.ok) {
      console.error(`Failed to fetch curve tickers: HTTP ${response.status}`)
      return []
    }

    const result = await response.json()
    return result.tickers || []
  } catch (error) {
    console.error('Failed to fetch curve tickers:', error)
    return []
  }
}

/**
 * Map currency to curve name (temporary until database has proper mapping)
 */
export function getCurveNameForCurrency(currency: string): string | null {
  const mapping: Record<string, string> = {
    'JPY': 'JPY_OIS',
    'CHF': 'CHF_IRS',
    'GBP': 'GBP_IRS',
    'EUR': 'EUR_IRS',
    'AUD': 'AUD_IRS',
    'CAD': 'CAD_IRS',
    'USD': 'USD_IRS', // Fallback since USD_SOFR_OIS not in DB yet
    'NZD': 'NZD_IRS',
    'SEK': 'SEK_IRS',
    'NOK': 'NOK_IRS',
    'DKK': 'DKK_IRS',
    'KRW': 'KRW_IRS',
    'MXN': 'MXN_IRS',
    'TRY': 'TRY_IRS',
    'BRL': 'BRL_IRS'
  }
  
  return mapping[currency] || null
}