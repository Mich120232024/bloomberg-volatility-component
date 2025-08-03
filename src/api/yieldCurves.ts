// Yield Curves API Client
import axios from 'axios'

// @ts-ignore - Vite provides import.meta.env
const BLOOMBERG_API_URL = import.meta.env.DEV 
  ? 'http://localhost:8000'
  : 'http://20.172.249.92:8080'

export interface YieldCurvePoint {
  tenor: string
  tenorDays: number
  tenorYears: number
  rate: number | null
  ticker: string
  instrumentType: string
}

export interface YieldCurveData {
  currency: string
  curveType: string
  timestamp: Date
  points: YieldCurvePoint[]
  dataQuality: {
    totalPoints: number
    validPoints: number
    coverage: number
  }
}

// Map of currencies to their OIS tickers from our database
const OIS_CURVE_TICKERS: Record<string, string[]> = {
  USD: [
    'SOFRRATE Index',      // ON
    'USSOA Curncy',        // 1M
    'USSOB Curncy',        // 2M
    'USSOC Curncy',        // 3M
    'USSOD Curncy',        // 4M
    'USSOE Curncy',        // 5M
    'USSOF Curncy',        // 6M
    'USSOG Curncy',        // 7M
    'USSOH Curncy',        // 8M
    'USSOI Curncy',        // 9M
    'USSOJ Curncy',        // 10M
    'USSOK Curncy',        // 11M
    'USSO1 BGN Curncy',    // 1Y
    'USSO2 Curncy',        // 2Y
    'USSO3 Curncy',        // 3Y
    'USSO4 Curncy',        // 4Y
    'USSO5 Curncy',        // 5Y
    'USSO7 Curncy',        // 7Y
    'USSO10 Curncy',       // 10Y
    'USSO15 Curncy',       // 15Y
    'USSO20 Curncy',       // 20Y
    'USSO25 Curncy',       // 25Y
    'USSO30 Curncy'        // 30Y
  ],
  EUR: [
    'ESTRON Index',        // ON - €STR overnight
    'EUSWEA Curncy',       // 1M - €STR OIS
    'EUSWEB Curncy',       // 2M - €STR OIS
    'EUSWEC Curncy',       // 3M - €STR OIS
    'EUSWED Curncy',       // 4M - €STR OIS
    'EUSWEE Curncy',       // 5M - €STR OIS
    'EUSWEF Curncy',       // 6M - €STR OIS
    'EUSWEA BGN Curncy',   // 1Y - €STR OIS
    'EUSWE2 Curncy',       // 2Y - €STR OIS
    'EUSWE3 Curncy',       // 3Y - €STR OIS
    'EUSWE4 Curncy',       // 4Y - €STR OIS
    'EUSWE5 Curncy',       // 5Y - €STR OIS
    'EUSWE7 Curncy',       // 7Y - €STR OIS
    'EUSWE10 Curncy',      // 10Y - €STR OIS
    'EUSWE15 Curncy',      // 15Y - €STR OIS
    'EUSWE20 Curncy',      // 20Y - €STR OIS
    'EUSWE30 Curncy'       // 30Y - €STR OIS
  ],
  GBP: [
    'SONIA Index',         // ON
    'BPSOA Curncy',        // 1M
    'BPSOB Curncy',        // 2M
    'BPSOC Curncy',        // 3M
    'BPSOD Curncy',        // 4M
    'BPSOE Curncy',        // 5M
    'BPSOF Curncy',        // 6M
    'BPSOG Curncy',        // 7M
    'BPSOH Curncy',        // 8M
    'BPSOI Curncy',        // 9M
    'BPSOJ Curncy',        // 10M
    'BPSOK Curncy',        // 11M
    'BPSO1 Curncy',        // 1Y
    'BPSO2 Curncy',        // 2Y
    'BPSO3 Curncy',        // 3Y
    'BPSO4 Curncy',        // 4Y
    'BPSO5 Curncy',        // 5Y
    'BPSO7 Curncy',        // 7Y
    'BPSO10 Curncy',       // 10Y
    'BPSO15 Curncy',       // 15Y
    'BPSO20 Curncy',       // 20Y
    'BPSO25 Curncy',       // 25Y
    'BPSO30 Curncy'        // 30Y
  ],
  JPY: [
    'TONAR Index',         // ON
    'JYSOA Curncy',        // 1M
    'JYSOB Curncy',        // 2M
    'JYSOC Curncy',        // 3M
    'JYSOD Curncy',        // 4M
    'JYSOE Curncy',        // 5M
    'JYSOF Curncy',        // 6M
    'JYSOG Curncy',        // 7M
    'JYSOH Curncy',        // 8M
    'JYSOI Curncy',        // 9M
    'JYSOJ Curncy',        // 10M
    'JYSOK Curncy',        // 11M
    'JYSO1 BGN Curncy',    // 1Y
    'JYSO2 Curncy',        // 2Y
    'JYSO3 Curncy',        // 3Y
    'JYSO4 Curncy',        // 4Y
    'JYSO5 Curncy',        // 5Y
    'JYSO7 Curncy',        // 7Y
    'JYSO10 Curncy',       // 10Y
    'JYSO15 Curncy',       // 15Y
    'JYSO20 Curncy',       // 20Y
    'JYSO30 Curncy'        // 30Y
  ],
  CHF: [
    'SSARON Index',        // ON
    'SFSNT10 BGNL Curncy', // 12M
    'SFSO1 Curncy',        // 1Y
    'SFSO2 Curncy',        // 2Y
    'SFSO3 Curncy',        // 3Y
    'SFSO5 Curncy',        // 5Y
    'SFSO7 Curncy',        // 7Y
    'SFSO10 Curncy',       // 10Y
    'SFSO15 Curncy',       // 15Y
    'SFSO20 Curncy',       // 20Y
    'SFSO25 Curncy',       // 25Y
    'SFSO30 Curncy'        // 30Y
  ],
  CAD: [
    'CORRA Index',         // ON
    'CDSOA Curncy',        // 1M
    'CDSOB Curncy',        // 2M
    'CDSOC Curncy',        // 3M
    'CDSOD Curncy',        // 4M
    'CDSOE Curncy',        // 5M
    'CDSOF Curncy',        // 6M
    'CDSOG Curncy',        // 7M
    'CDSOH Curncy',        // 8M
    'CDSOI Curncy',        // 9M
    'CDSOJ Curncy',        // 10M
    'CDSOK Curncy',        // 11M
    'CDSO1 Curncy',        // 1Y
    'CDSO2 Curncy',        // 2Y
    'CDSO3 Curncy',        // 3Y
    'CDSO4 Curncy',        // 4Y
    'CDSO5 Curncy',        // 5Y
    'CDSO7 Curncy',        // 7Y
    'CDSO10 Curncy',       // 10Y
    'CDSO15 Curncy',       // 15Y
    'CDSO20 Curncy',       // 20Y
    'CDSO30 Curncy'        // 30Y
  ],
  AUD: [
    'AONIA Index',         // ON
    'ADSOA Curncy',        // 1M
    'ADSOB Curncy',        // 2M
    'ADSOC Curncy',        // 3M
    'ADSOD Curncy',        // 4M
    'ADSOE Curncy',        // 5M
    'ADSOF Curncy',        // 6M
    'ADSOG Curncy',        // 7M
    'ADSOH Curncy',        // 8M
    'ADSOI Curncy',        // 9M
    'ADSOJ Curncy',        // 10M
    'ADSOK Curncy',        // 11M
    'ADSO1 Curncy',        // 1Y
    'ADSO2 Curncy',        // 2Y
    'ADSO3 Curncy',        // 3Y
    'ADSO4 Curncy',        // 4Y
    'ADSO5 Curncy',        // 5Y
    'ADSO7 Curncy',        // 7Y
    'ADSO10 Curncy',       // 10Y
    'ADSO15 Curncy',       // 15Y
    'ADSO20 Curncy',       // 20Y
    'ADSO30 Curncy'        // 30Y
  ],
  NZD: [
    'NZIONA Index',        // ON
    'NDSOA Curncy',        // 1M
    'NDSOB Curncy',        // 2M
    'NDSOC Curncy',        // 3M
    'NDSOD Curncy',        // 4M
    'NDSOE Curncy',        // 5M
    'NDSOF Curncy',        // 6M
    'NDSOG Curncy',        // 7M
    'NDSOH Curncy',        // 8M
    'NDSOI Curncy',        // 9M
    'NDSOJ Curncy',        // 10M
    'NDSOK Curncy',        // 11M
    'NDSO1 Curncy',        // 1Y
    'NDSO2 Curncy',        // 2Y
    'NDSO3 Curncy',        // 3Y
    'NDSO4 Curncy',        // 4Y
    'NDSO5 Curncy',        // 5Y
    'NDSO7 Curncy',        // 7Y
    'NDSO10 Curncy',       // 10Y
    'NDSO15 Curncy',       // 15Y
    'NDSO20 Curncy',       // 20Y
    'NDSO25 Curncy',       // 25Y
    'NDSO30 Curncy'        // 30Y
  ],
  SEK: ['SWESTR Index'],      // ON only
  NOK: ['NOWA Index', 'NKS1M BGNL Curncy']  // ON + 1Y
}

// Tenor mappings
const TENOR_TO_DAYS: Record<string, number> = {
  'ON': 1,
  '1W': 7,
  '2W': 14,
  '3W': 21,
  '1M': 30,
  '2M': 60,
  '3M': 90,
  '4M': 120,
  '5M': 150,
  '6M': 180,
  '7M': 210,
  '8M': 240,
  '9M': 270,
  '10M': 300,
  '11M': 330,
  '12M': 360,
  '1Y': 365,
  '15M': 450,
  '18M': 540,
  '21M': 630,
  '2Y': 730,
  '3Y': 1095,
  '4Y': 1460,
  '5Y': 1825,
  '6Y': 2190,
  '7Y': 2555,
  '8Y': 2920,
  '9Y': 3285,
  '10Y': 3650,
  '12Y': 4380,
  '15Y': 5475,
  '20Y': 7300,
  '25Y': 9125,
  '30Y': 10950
}

function extractTenorFromTicker(ticker: string): string {
  // Handle overnight rates
  if (ticker.includes('Index')) return 'ON'
  
  // Handle monthly patterns (USSOA, USSOB, etc.)
  const monthMap: Record<string, string> = {
    'A': '1M', 'B': '2M', 'C': '3M', 'D': '4M', 'E': '5M', 'F': '6M',
    'G': '7M', 'H': '8M', 'I': '9M', 'J': '10M', 'K': '11M', 'L': '12M'
  }
  
  // Check for monthly pattern
  const monthMatch = ticker.match(/SO([A-L])\s+(Curncy|BGN)/)
  if (monthMatch && monthMap[monthMatch[1]]) {
    return monthMap[monthMatch[1]]
  }
  
  // Handle yearly patterns (USSO1, USSO10, etc.)
  const yearMatch = ticker.match(/SO(\d+[MC]?)\s+(Curncy|BGN|BGNL)/)
  if (yearMatch) {
    const yearPart = yearMatch[1]
    if (yearPart.includes('M')) return yearPart
    if (yearPart.includes('C')) return yearPart.replace('C', 'M')
    return `${yearPart}Y`
  }
  
  // Special cases
  if (ticker.includes('SFSNT10')) return '12M'
  if (ticker.includes('NKS1M')) return '12M'
  
  return ''
}

class YieldCurvesAPIClient {
  private headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer test'
  }

  async getYieldCurve(currency: string): Promise<YieldCurveData> {
    const tickers = OIS_CURVE_TICKERS[currency]
    if (!tickers || tickers.length === 0) {
      throw new Error(`No tickers configured for ${currency}`)
    }

    console.log(`🚀 Fetching ${currency} OIS curve with ${tickers.length} tickers`)
    
    try {
      // Fetch data from Bloomberg
      const response = await axios.post(
        `${BLOOMBERG_API_URL}/api/bloomberg/reference`,
        {
          securities: tickers,
          fields: ['PX_LAST', 'PX_BID', 'PX_ASK']
        },
        { 
          headers: this.headers,
          timeout: 30000
        }
      )

      if (!response.data.success) {
        throw new Error(response.data.error?.message || 'Bloomberg API error')
      }

      const points: YieldCurvePoint[] = []
      const securitiesData = response.data.data?.securities_data || []
      
      securitiesData.forEach((secData: any, index: number) => {
        if (secData.success && secData.fields?.PX_LAST !== undefined) {
          const ticker = tickers[index]
          const tenor = extractTenorFromTicker(ticker)
          const days = TENOR_TO_DAYS[tenor] || 0
          
          points.push({
            tenor,
            tenorDays: days,
            tenorYears: days / 365,
            rate: secData.fields.PX_LAST,
            ticker,
            instrumentType: ticker.includes('Index') ? 'overnight' : 'ois'
          })
        }
      })

      // Sort by tenor days
      points.sort((a, b) => a.tenorDays - b.tenorDays)

      const validPoints = points.filter(p => p.rate !== null).length
      
      return {
        currency,
        curveType: 'OIS',
        timestamp: new Date(),
        points,
        dataQuality: {
          totalPoints: tickers.length,
          validPoints,
          coverage: (validPoints / tickers.length) * 100
        }
      }
    } catch (error) {
      console.error(`Failed to fetch ${currency} yield curve:`, error)
      throw error
    }
  }

  async getMultipleCurves(currencies: string[]): Promise<YieldCurveData[]> {
    const promises = currencies.map(currency => 
      this.getYieldCurve(currency).catch(err => {
        console.error(`Failed to fetch ${currency} curve:`, err)
        return null
      })
    )
    
    const results = await Promise.all(promises)
    return results.filter((r): r is YieldCurveData => r !== null)
  }

  getAvailableCurrencies(): string[] {
    return Object.keys(OIS_CURVE_TICKERS)
  }
}

export const yieldCurvesAPI = new YieldCurvesAPIClient()