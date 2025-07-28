/**
 * Data Validation Layer for Bloomberg Volatility Data
 * Addresses critical audit findings about null handling and data quality
 */

export interface DataQualityMetrics {
  score: number // 0-100
  completeness: number // 0-100
  warnings: string[]
  errors: string[]
  interpolatedFields: string[]
  timestamp: Date
  dataAge: number // milliseconds since last update
}

export interface ValidatedVolatilityData {
  tenor: string
  // Guaranteed non-null core data
  atm_mid: number
  atm_spread: number
  
  // Original nullable fields for transparency
  raw: {
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
  
  // Computed valid values with fallbacks
  computed: {
    rr_5d_mid: number
    rr_10d_mid: number
    rr_15d_mid: number
    rr_25d_mid: number
    rr_35d_mid: number
    bf_5d_mid: number
    bf_10d_mid: number
    bf_15d_mid: number
    bf_25d_mid: number
    bf_35d_mid: number
  }
  
  quality: DataQualityMetrics
}

export interface DataQualitySummary {
  totalRecords: number
  completeRecords: number
  overallScore: number
  criticalWarnings: string[]
  interpolatedRecords: number
  lastUpdate: Date
}

export class DataValidator {
  private static readonly VOLATILITY_MIN = 0.1 // 0.1% minimum vol
  private static readonly VOLATILITY_MAX = 200.0 // 200% maximum vol
  private static readonly SPREAD_MAX = 50.0 // 50% maximum spread
  private static readonly STALE_DATA_THRESHOLD = 5 * 60 * 1000 // 5 minutes
  
  static validateVolatilityData(
    rawData: any, 
    timestamp: Date
  ): ValidatedVolatilityData | null {
    const warnings: string[] = []
    const errors: string[] = []
    const interpolatedFields: string[] = []
    
    // Validate core ATM data first
    const { atm_mid, atm_spread, atmValid } = this.validateATMData(
      rawData.atm_bid, 
      rawData.atm_ask,
      warnings,
      errors
    )
    
    if (!atmValid) {
      // Don't skip - just note the issue and continue
      console.warn(`Tenor ${rawData.tenor} has invalid ATM data but continuing`)
      warnings.push('ATM data invalid or missing')
    }
    
    // Validate and compute Risk Reversals and Butterflies
    const computed = this.computeValidatedValues(rawData, warnings, interpolatedFields)
    
    // Calculate quality score
    const completeness = this.calculateCompleteness(rawData)
    const score = this.calculateQualityScore(completeness, warnings.length, errors.length)
    
    const quality: DataQualityMetrics = {
      score,
      completeness,
      warnings,
      errors,
      interpolatedFields,
      timestamp,
      dataAge: Date.now() - timestamp.getTime()
    }
    
    return {
      tenor: rawData.tenor,
      atm_mid: atm_mid,
      atm_spread: atm_spread,
      raw: { ...rawData },
      computed,
      quality
    }
  }
  
  private static validateATMData(
    bid: number | null, 
    ask: number | null,
    warnings: string[],
    errors: string[]
  ): { atm_mid: number, atm_spread: number, atmValid: boolean } {
    
    if (bid === null || ask === null) {
      errors.push('ATM bid or ask is null')
      return { atm_mid: 0, atm_spread: 0, atmValid: false }
    }
    
    if (bid <= 0 || ask <= 0) {
      errors.push('ATM bid or ask is non-positive')
      return { atm_mid: 0, atm_spread: 0, atmValid: false }
    }
    
    if (bid > ask) {
      errors.push('ATM bid > ask (crossed market)')
      return { atm_mid: 0, atm_spread: 0, atmValid: false }
    }
    
    const mid = (bid + ask) / 2
    const spread = ask - bid
    
    if (mid < this.VOLATILITY_MIN || mid > this.VOLATILITY_MAX) {
      warnings.push(`ATM volatility ${mid}% outside normal range`)
    }
    
    if (spread > this.SPREAD_MAX) {
      warnings.push(`ATM spread ${spread}% unusually wide`)
    }
    
    return { atm_mid: mid, atm_spread: spread, atmValid: true }
  }
  
  private static computeValidatedValues(
    rawData: any,
    warnings: string[],
    interpolatedFields: string[]
  ) {
    const computed = {
      rr_5d_mid: this.computeMidOrFallback('rr_5d', rawData.rr_5d_bid, rawData.rr_5d_ask, warnings, interpolatedFields),
      rr_10d_mid: this.computeMidOrFallback('rr_10d', rawData.rr_10d_bid, rawData.rr_10d_ask, warnings, interpolatedFields),
      rr_15d_mid: this.computeMidOrFallback('rr_15d', rawData.rr_15d_bid, rawData.rr_15d_ask, warnings, interpolatedFields),
      rr_25d_mid: this.computeMidOrFallback('rr_25d', rawData.rr_25d_bid, rawData.rr_25d_ask, warnings, interpolatedFields),
      rr_35d_mid: this.computeMidOrFallback('rr_35d', rawData.rr_35d_bid, rawData.rr_35d_ask, warnings, interpolatedFields),
      bf_5d_mid: this.computeMidOrFallback('bf_5d', rawData.bf_5d_bid, rawData.bf_5d_ask, warnings, interpolatedFields),
      bf_10d_mid: this.computeMidOrFallback('bf_10d', rawData.bf_10d_bid, rawData.bf_10d_ask, warnings, interpolatedFields),
      bf_15d_mid: this.computeMidOrFallback('bf_15d', rawData.bf_15d_bid, rawData.bf_15d_ask, warnings, interpolatedFields),
      bf_25d_mid: this.computeMidOrFallback('bf_25d', rawData.bf_25d_bid, rawData.bf_25d_ask, warnings, interpolatedFields),
      bf_35d_mid: this.computeMidOrFallback('bf_35d', rawData.bf_35d_bid, rawData.bf_35d_ask, warnings, interpolatedFields)
    }
    
    return computed
  }
  
  private static computeMidOrFallback(
    fieldName: string,
    bid: number | null,
    ask: number | null,
    warnings: string[],
    interpolatedFields: string[]
  ): number {
    if (bid !== null && ask !== null && bid <= ask) {
      return (bid + ask) / 2
    }
    
    // NO FALLBACKS - just return 0 for missing data
    warnings.push(`${fieldName} missing data (bid: ${bid}, ask: ${ask})`)
    return 0
  }
  
  private static calculateCompleteness(rawData: any): number {
    const fields = [
      'atm_bid', 'atm_ask',
      'rr_5d_bid', 'rr_5d_ask', 'bf_5d_bid', 'bf_5d_ask',
      'rr_10d_bid', 'rr_10d_ask', 'bf_10d_bid', 'bf_10d_ask',
      'rr_15d_bid', 'rr_15d_ask', 'bf_15d_bid', 'bf_15d_ask',
      'rr_25d_bid', 'rr_25d_ask', 'bf_25d_bid', 'bf_25d_ask',
      'rr_35d_bid', 'rr_35d_ask', 'bf_35d_bid', 'bf_35d_ask'
    ]
    
    const nonNullFields = fields.filter(field => rawData[field] !== null).length
    return Math.round((nonNullFields / fields.length) * 100)
  }
  
  private static calculateQualityScore(
    completeness: number, 
    warningCount: number, 
    errorCount: number
  ): number {
    let score = completeness
    
    // Penalize warnings (minor issues)
    score -= warningCount * 5
    
    // Heavily penalize errors (major issues)
    score -= errorCount * 20
    
    return Math.max(0, Math.min(100, score))
  }
  
  private static createATMFallback(tenor: string): { atm_mid: number } {
    // Use reasonable volatility estimates by tenor
    const fallbackVols: Record<string, number> = {
      'ON': 8.0,   // Overnight usually lower
      '1W': 10.0,  // Short term
      '2W': 12.0,
      '1M': 15.0,
      '2M': 16.0,
      '3M': 18.0,  // Standard benchmark
      '6M': 20.0,
      '9M': 22.0,
      '1Y': 25.0,  // Longer term higher
      '18M': 28.0,
      '2Y': 30.0
    }
    
    return { atm_mid: fallbackVols[tenor] || 18.0 }
  }
  
  static interpolateMissingData(data: ValidatedVolatilityData[]): ValidatedVolatilityData[] {
    // For now, return as-is. Advanced interpolation could be added later
    // (linear interpolation across tenors, volatility surface smoothing, etc.)
    return data
  }
  
  static getDataQualitySummary(data: ValidatedVolatilityData[]): DataQualitySummary {
    const completeRecords = data.filter(d => d.quality.completeness === 100).length
    const averageScore = data.reduce((sum, d) => sum + d.quality.score, 0) / data.length
    const interpolatedRecords = data.filter(d => d.quality.interpolatedFields.length > 0).length
    
    // Collect critical warnings (errors or major issues)
    const criticalWarnings: string[] = []
    data.forEach(d => {
      d.quality.errors.forEach(error => criticalWarnings.push(`${d.tenor}: ${error}`))
      d.quality.warnings.forEach(warning => {
        if (warning.includes('invalid') || warning.includes('fallback')) {
          criticalWarnings.push(`${d.tenor}: ${warning}`)
        }
      })
    })
    
    return {
      totalRecords: data.length,
      completeRecords,
      overallScore: Math.round(averageScore),
      criticalWarnings: [...new Set(criticalWarnings)], // deduplicate
      interpolatedRecords,
      lastUpdate: new Date()
    }
  }
  
  static validateSecurityData(securities: any[]): { valid: any[], summary: any } {
    const valid = securities.filter(sec => sec && (sec.success || sec.fields))
    const failed = securities.length - valid.length
    
    return {
      valid,
      summary: {
        totalRequested: securities.length,
        successful: valid.length,
        failed
      }
    }
  }
}