// Bloomberg API Client for Volatility Surface
import axios from 'axios'
import { DataValidator, ValidatedVolatilityData } from './DataValidator'
// BloombergErrorRecovery removed - no fallbacks allowed

// Bloomberg Gateway Configuration
// Development: Local gateway (no cache, always fresh data)
// Production: Can be deployed gateway with Redis cache
// @ts-ignore - Vite provides import.meta.env
const BLOOMBERG_API_URL = import.meta.env.DEV 
  ? 'http://localhost:8000'  // Local gateway for development
  : 'http://20.172.249.92:8080'  // Direct to VM for now, update when gateway deployed
const API_KEY = 'test'

export interface VolatilityData {
  tenor: string
  atm_bid: number | null
  atm_ask: number | null
  rr_5d_bid: number | null
  rr_5d_ask: number | null
  bf_5d_bid: number | null
  bf_5d_ask: number | null
  rr_10d_bid: number | null
  rr_10d_ask: number | null
  bf_10d_bid: number | null
  bf_10d_ask: number | null
  rr_15d_bid: number | null
  rr_15d_ask: number | null
  bf_15d_bid: number | null
  bf_15d_ask: number | null
  rr_25d_bid: number | null
  rr_25d_ask: number | null
  bf_25d_bid: number | null
  bf_25d_ask: number | null
  rr_35d_bid: number | null
  rr_35d_ask: number | null
  bf_35d_bid: number | null
  bf_35d_ask: number | null
}

export interface SecurityData {
  security: string
  fields: {
    PX_LAST?: number
    PX_BID?: number
    PX_ASK?: number
  }
  success: boolean
  error?: string
}

// Standard FX option tenors - only those with available Bloomberg data
export const STANDARD_TENORS = [
  "ON",   // Overnight (O/N)
  "1W",   // 1 week
  "2W",   // 2 weeks
  "3W",   // 3 weeks
  "1M",   // 1 month
  "2M",   // 2 months
  "3M",   // 3 months
  "4M",   // 4 months
  "6M",   // 6 months
  "9M",   // 9 months
  "1Y",   // 1 year
  "18M",  // 18 months
  "2Y"    // 2 years
]

class BloombergAPIClient {
  private headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${API_KEY}`,
    'X-API-Key': API_KEY
  }
  
  // Circuit breaker removed - fail fast approach
  private lastSuccessfulFetch: Date | null = null

  async healthCheck() {
    try {
      // In dev mode, need to call the API directly since /health isn't under /api path
      const url = import.meta.env.DEV 
        ? 'http://20.172.249.92:8080/health'
        : `${BLOOMBERG_API_URL}/health`
      
      // Add cache-busting to prevent stale status
      const response = await axios.get(url, {
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        },
        params: {
          _t: Date.now() // Cache buster
        }
      })
      return response.data
    } catch (error) {
      console.error('Health check failed:', error)
      throw error
    }
  }

  async getReferenceData(securities: string[], fields: string[]) {
      const result = await (async () => {
          console.log('Sending request to bloomberg/reference:', { securities, fields })
          const response = await axios.post(
            `${BLOOMBERG_API_URL}/api/bloomberg/reference`,
            { securities, fields },
            { 
              headers: this.headers,
              timeout: 30000 // 30 second timeout
            }
          )
          console.log('Raw API response:', JSON.stringify(response.data, null, 2))
          this.lastSuccessfulFetch = new Date()
          return response.data
        })()
      
      if (!result.success) {
        const errorMsg = result.error?.message || 'Unknown Bloomberg API error'
        console.error('Reference data request failed after retries:', errorMsg)
        throw new Error(errorMsg)
      }
      
      return result.data
  }

  async startBloombergService() {
    try {
      // Use Azure CLI to start the Bloomberg API service on the VM
      const response = await axios.post(
        `${BLOOMBERG_API_URL}/api/vm/service/start`,
        {},
        { headers: this.headers }
      )
      return response.data
    } catch (error) {
      console.error('Failed to start Bloomberg service:', error)
      throw error
    }
  }

  async stopBloombergService() {
    try {
      // Use Azure CLI to stop the Bloomberg API service on the VM
      const response = await axios.post(
        `${BLOOMBERG_API_URL}/api/vm/service/stop`,
        {},
        { headers: this.headers }
      )
      return response.data
    } catch (error) {
      console.error('Failed to stop Bloomberg service:', error)
      throw error
    }
  }

  async getServiceStatus() {
    try {
      // Check if the Bloomberg API service is running on the VM
      const response = await axios.get(
        `${BLOOMBERG_API_URL}/api/vm/service/status`,
        { headers: this.headers }
      )
      return response.data
    } catch (error) {
      console.error('Failed to get service status:', error)
      // If we can't reach the status endpoint, the service is probably down
      return { success: false, service_running: false, error: 'Service unreachable' }
    }
  }

  async getHistoricalData(security: string, fields: string[], startDate: string, endDate: string) {
    try {
      console.log('Fetching historical data:', { security, fields, startDate, endDate })
      const response = await axios.post(
        `${BLOOMBERG_API_URL}/api/bloomberg/historical`,
        { 
          security, 
          fields, 
          start_date: startDate,
          end_date: endDate,
          periodicity: 'DAILY'
        },
        { headers: this.headers }
      )
      console.log('Historical data response:', response.data)
      return response.data
    } catch (error) {
      console.error('Historical data request failed:', error)
      throw error
    }
  }

  async getVolatilitySurface(currencyPair: string = "EURUSD", tenors: string[] = STANDARD_TENORS, date?: string): Promise<ValidatedVolatilityData[]> {
    console.log('🔍 getVolatilitySurface called with:', { currencyPair, tenors: tenors.length, date })
    console.log('Tenors requested:', tenors)
    
    // If date is provided, we need to use historical data endpoint
    if (date) {
      // Get historical data for the specific date
      return this.getHistoricalVolatilitySurface(currencyPair, tenors, date)
    }

    // Process all tenors
    const tenorsToProcess = tenors
    console.log('Processing all tenors:', tenorsToProcess)
    
    // OPTIMIZATION: Batch ALL securities into smaller chunks to respect rate limits
    // Build all securities first
    const allSecurities: string[] = []
    const tenorMap = new Map<string, string>()
    
    for (const tenor of tenorsToProcess) {
      const isON = tenor === 'ON'
      
      // ATM
      const atmSecurity = isON ? `${currencyPair}V${tenor} Curncy` : `${currencyPair}V${tenor} BGN Curncy`
      allSecurities.push(atmSecurity)
      tenorMap.set(atmSecurity, tenor)
      
      // Risk Reversals and Butterflies for all deltas
      const deltas = [5, 10, 15, 25, 35]
      for (const delta of deltas) {
        const rrSecurity = `${currencyPair}${delta}R${tenor} BGN Curncy`
        const bfSecurity = `${currencyPair}${delta}B${tenor} BGN Curncy`
        allSecurities.push(rrSecurity, bfSecurity)
        tenorMap.set(rrSecurity, tenor)
        tenorMap.set(bfSecurity, tenor)
      }
    }
    
    console.log(`📊 Total securities to fetch for ${currencyPair}: ${allSecurities.length}`)
    console.log(`📈 Sample securities:`, allSecurities.slice(0, 3))
    
    // Process in chunks of 50 securities (well under Bloomberg's limit)
    const chunkSize = 50
    const chunks: string[][] = []
    for (let i = 0; i < allSecurities.length; i += chunkSize) {
      chunks.push(allSecurities.slice(i, i + chunkSize))
    }
    
    console.log(`Processing ${chunks.length} chunks...`)
    
    // Fetch all chunks with error recovery
    // Process chunks sequentially - NO ERROR RECOVERY, FAIL FAST
    const batchResult: any[] = []
    for (const chunk of chunks) {
      console.log(`Fetching chunk (${chunk.length} securities)`)
      const response = await this.getReferenceData(chunk, ["PX_LAST", "PX_BID", "PX_ASK"])
      
      // getReferenceData returns the data directly, not wrapped in success/data
      if (!response || !response.securities_data) {
        throw new Error('Invalid response from Bloomberg API - no fallback allowed')
      }
      
      batchResult.push(...response.securities_data)
    }
    
    // Use collected responses
    const allResponses: SecurityData[] = batchResult
    
    // Validate the security data
    const { valid: validSecurities, summary } = DataValidator.validateSecurityData(allResponses)
    
    if (summary.failed > 0) {
      console.warn(`Failed to fetch ${summary.failed} securities out of ${summary.totalRequested}`)
    }
    
    // Now organize the data by tenor
    const tenorDataMap = new Map<string, VolatilityData>()
    
    // Initialize tenor data
    for (const tenor of tenorsToProcess) {
      tenorDataMap.set(tenor, {
        tenor,
        atm_bid: null,
        atm_ask: null,
        rr_5d_bid: null,
        rr_5d_ask: null,
        bf_5d_bid: null,
        bf_5d_ask: null,
        rr_10d_bid: null,
        rr_10d_ask: null,
        bf_10d_bid: null,
        bf_10d_ask: null,
        rr_15d_bid: null,
        rr_15d_ask: null,
        bf_15d_bid: null,
        bf_15d_ask: null,
        rr_25d_bid: null,
        rr_25d_ask: null,
        bf_25d_bid: null,
        bf_25d_ask: null,
        rr_35d_bid: null,
        rr_35d_ask: null,
        bf_35d_bid: null,
        bf_35d_ask: null
      })
    }
    
    // Process all valid responses
    for (const sec of validSecurities) {
      if (!sec.success || !sec.fields) continue
      
      const tenor = tenorMap.get(sec.security)
      if (!tenor) continue
      
      const tenorData = tenorDataMap.get(tenor)
      if (!tenorData) continue
      
      const security = sec.security
      
      // Parse security type
      if (security.includes(`V${tenor}`)) {
        // ATM
        tenorData.atm_bid = sec.fields.PX_BID ?? null
        tenorData.atm_ask = sec.fields.PX_ASK ?? null
      } else {
        // Extract delta and type
        const match = security.match(new RegExp(`${currencyPair}(\\d+)(R|B)${tenor}`))
        if (match) {
          const delta = parseInt(match[1])
          const type = match[2]
          
          if (type === 'R') {
            // Risk Reversal
            switch(delta) {
              case 5: 
                tenorData.rr_5d_bid = sec.fields.PX_BID ?? null
                tenorData.rr_5d_ask = sec.fields.PX_ASK ?? null
                break
              case 10: 
                tenorData.rr_10d_bid = sec.fields.PX_BID ?? null
                tenorData.rr_10d_ask = sec.fields.PX_ASK ?? null
                break
              case 15: 
                tenorData.rr_15d_bid = sec.fields.PX_BID ?? null
                tenorData.rr_15d_ask = sec.fields.PX_ASK ?? null
                break
              case 25: 
                tenorData.rr_25d_bid = sec.fields.PX_BID ?? null
                tenorData.rr_25d_ask = sec.fields.PX_ASK ?? null
                break
              case 35: 
                tenorData.rr_35d_bid = sec.fields.PX_BID ?? null
                tenorData.rr_35d_ask = sec.fields.PX_ASK ?? null
                break
            }
          } else if (type === 'B') {
            // Butterfly
            switch(delta) {
              case 5: 
                tenorData.bf_5d_bid = sec.fields.PX_BID ?? null
                tenorData.bf_5d_ask = sec.fields.PX_ASK ?? null
                break
              case 10: 
                tenorData.bf_10d_bid = sec.fields.PX_BID ?? null
                tenorData.bf_10d_ask = sec.fields.PX_ASK ?? null
                break
              case 15: 
                tenorData.bf_15d_bid = sec.fields.PX_BID ?? null
                tenorData.bf_15d_ask = sec.fields.PX_ASK ?? null
                break
              case 25: 
                tenorData.bf_25d_bid = sec.fields.PX_BID ?? null
                tenorData.bf_25d_ask = sec.fields.PX_ASK ?? null
                break
              case 35: 
                tenorData.bf_35d_bid = sec.fields.PX_BID ?? null
                tenorData.bf_35d_ask = sec.fields.PX_ASK ?? null
                break
            }
          }
        }
      }
    }
    
    // Convert map to array in correct order and validate
    const validatedResults: ValidatedVolatilityData[] = []
    const timestamp = new Date()
    
    for (const tenor of tenorsToProcess) {
      const data = tenorDataMap.get(tenor)
      if (data) {
        console.log(`🔍 VALIDATING TENOR ${tenor}:`, JSON.stringify(data, null, 2))
        const validatedData = DataValidator.validateVolatilityData(data, timestamp)
        console.log(`✅ VALIDATED RESULT for ${tenor}:`, validatedData ? 'SUCCESS' : 'NULL')
        if (validatedData) {
          console.log(`✅ VALIDATED DATA:`, JSON.stringify(validatedData, null, 2))
          console.log(`✅ VALIDATED RAW ATM DATA:`, {
            atmBid: validatedData.raw?.atm_bid,
            atmAsk: validatedData.raw?.atm_ask,
            hasRaw: !!validatedData.raw
          })
          validatedResults.push(validatedData)
        } else {
          console.error(`❌ VALIDATION FAILED for ${tenor}`)
        }
      } else {
        // Skip tenors with no data - this is normal for some tenors
        console.warn(`No Bloomberg data for tenor ${tenor} - skipping`)
      }
    }
    
    // Apply interpolation for missing values if needed
    const interpolatedResults = DataValidator.interpolateMissingData(validatedResults)
    
    // Log data quality summary
    const qualitySummary = DataValidator.getDataQualitySummary(interpolatedResults)
    console.log(`Data quality: ${qualitySummary.overallScore}% (${qualitySummary.completeRecords}/${qualitySummary.totalRecords} complete)`)
    
    if (qualitySummary.criticalWarnings.length > 0) {
      console.warn('Critical warnings:', qualitySummary.criticalWarnings)
    }
    
    return interpolatedResults
  }

  async getHistoricalVolatilitySurface(currencyPair: string, tenors: string[], date: string): Promise<ValidatedVolatilityData[]> {
    // TODO: Implement historical data fetching
    // For now, return empty array
    console.log('getHistoricalVolatilitySurface called with:', { currencyPair, date, tenorCount: tenors.length })
    return []
  }
  
  getDataQualityStatus(): {
    lastSuccessfulFetch: Date | null
    circuitBreakerState: any
  } {
    return {
      lastSuccessfulFetch: this.lastSuccessfulFetch,
      circuitBreakerState: 'DISABLED'
    }
  }
}

export const bloombergAPI = new BloombergAPIClient()
