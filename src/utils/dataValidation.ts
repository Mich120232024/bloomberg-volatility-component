// Data validation and quality utilities for Bloomberg data
import { VolatilityData, SecurityData } from '../api/bloomberg'

export interface DataQualityMetrics {
  totalFields: number
  validFields: number
  nullFields: number
  timestamp: Date
  lastUpdate: Date | null
  completenessScore: number // 0-100
  isStale: boolean
  warnings: string[]
}

export interface ValidatedVolatilityData extends VolatilityData {
  quality: DataQualityMetrics
  isComplete: boolean
  missingFields: string[]
}

export class DataValidator {
  private static readonly STALE_DATA_THRESHOLD_MS = 5 * 60 * 1000 // 5 minutes
  private static readonly MIN_COMPLETENESS_SCORE = 70 // Minimum acceptable data completeness
  
  static validateVolatilityData(data: VolatilityData, timestamp: Date = new Date()): ValidatedVolatilityData {
    const fieldNames = Object.keys(data).filter(key => key !== 'tenor')
    const totalFields = fieldNames.length
    const nullFields = fieldNames.filter(key => data[key as keyof VolatilityData] === null).length
    const validFields = totalFields - nullFields
    const completenessScore = Math.round((validFields / totalFields) * 100)
    
    const warnings: string[] = []
    const missingFields: string[] = []
    
    // Check critical fields
    const criticalFields = ['atm_bid', 'atm_ask']
    for (const field of criticalFields) {
      if (data[field as keyof VolatilityData] === null) {
        warnings.push(`Critical field '${field}' is missing`)
        missingFields.push(field)
      }
    }
    
    // Check data consistency
    if (data.atm_bid !== null && data.atm_ask !== null) {
      if (data.atm_bid > data.atm_ask) {
        warnings.push('ATM bid > ask - possible data error')
      }
      
      const spread = data.atm_ask - data.atm_bid
      const midpoint = (data.atm_bid + data.atm_ask) / 2
      const spreadPercentage = (spread / midpoint) * 100
      
      if (spreadPercentage > 10) {
        warnings.push(`Wide bid-ask spread: ${spreadPercentage.toFixed(2)}%`)
      }
    }
    
    // Check for stale data (placeholder - would need actual timestamp from Bloomberg)
    const isStale = false // In production, compare against actual data timestamp
    
    const quality: DataQualityMetrics = {
      totalFields,
      validFields,
      nullFields,
      timestamp,
      lastUpdate: timestamp, // In production, get from Bloomberg
      completenessScore,
      isStale,
      warnings
    }
    
    const isComplete = completenessScore >= this.MIN_COMPLETENESS_SCORE && 
                      criticalFields.every(f => data[f as keyof VolatilityData] !== null)
    
    return {
      ...data,
      quality,
      isComplete,
      missingFields
    }
  }
  
  static validateSecurityData(data: SecurityData[]): {
    valid: SecurityData[]
    invalid: SecurityData[]
    summary: {
      totalRequested: number
      successful: number
      failed: number
      partialData: number
    }
  } {
    const valid: SecurityData[] = []
    const invalid: SecurityData[] = []
    let partialData = 0
    
    for (const item of data) {
      if (!item.success || item.error) {
        invalid.push(item)
      } else if (item.fields && Object.keys(item.fields).length > 0) {
        // Check if all requested fields are present
        const hasAllFields = item.fields.PX_LAST !== undefined || 
                           (item.fields.PX_BID !== undefined && item.fields.PX_ASK !== undefined)
        
        if (hasAllFields) {
          valid.push(item)
        } else {
          partialData++
          valid.push(item) // Still include partial data but track it
        }
      } else {
        invalid.push(item)
      }
    }
    
    return {
      valid,
      invalid,
      summary: {
        totalRequested: data.length,
        successful: valid.length,
        failed: invalid.length,
        partialData
      }
    }
  }
  
  static interpolateMissingData(data: ValidatedVolatilityData[]): ValidatedVolatilityData[] {
    // Sort by tenor for interpolation
    const sortedData = [...data].sort((a, b) => {
      const tenorOrder = ['ON', '1W', '2W', '3W', '1M', '2M', '3M', '4M', '6M', '9M', '1Y', '18M', '2Y']
      return tenorOrder.indexOf(a.tenor) - tenorOrder.indexOf(b.tenor)
    })
    
    // Interpolate missing ATM values
    for (let i = 1; i < sortedData.length - 1; i++) {
      const current = sortedData[i]
      
      if (current.atm_bid === null || current.atm_ask === null) {
        const prev = sortedData[i - 1]
        const next = sortedData[i + 1]
        
        if (prev.atm_bid !== null && next.atm_bid !== null) {
          current.atm_bid = (prev.atm_bid + next.atm_bid) / 2
          current.quality.warnings.push('ATM bid interpolated')
        }
        
        if (prev.atm_ask !== null && next.atm_ask !== null) {
          current.atm_ask = (prev.atm_ask + next.atm_ask) / 2
          current.quality.warnings.push('ATM ask interpolated')
        }
      }
    }
    
    return sortedData
  }
  
  static getDataQualitySummary(data: ValidatedVolatilityData[]): {
    overallScore: number
    completeRecords: number
    totalRecords: number
    averageCompleteness: number
    staleRecords: number
    criticalWarnings: string[]
  } {
    const completeRecords = data.filter(d => d.isComplete).length
    const totalRecords = data.length
    const averageCompleteness = data.reduce((sum, d) => sum + d.quality.completenessScore, 0) / totalRecords
    const staleRecords = data.filter(d => d.quality.isStale).length
    
    const allWarnings = data.flatMap(d => d.quality.warnings)
    const criticalWarnings = [...new Set(allWarnings)].filter(w => 
      w.includes('Critical') || w.includes('error')
    )
    
    // Calculate overall score (weighted average)
    const completeWeight = 0.4
    const freshnessWeight = 0.3
    const accuracyWeight = 0.3
    
    const completeScore = (completeRecords / totalRecords) * 100
    const freshnessScore = ((totalRecords - staleRecords) / totalRecords) * 100
    const accuracyScore = criticalWarnings.length === 0 ? 100 : Math.max(0, 100 - (criticalWarnings.length * 20))
    
    const overallScore = Math.round(
      completeScore * completeWeight +
      freshnessScore * freshnessWeight +
      accuracyScore * accuracyWeight
    )
    
    return {
      overallScore,
      completeRecords,
      totalRecords,
      averageCompleteness,
      staleRecords,
      criticalWarnings
    }
  }
}

// Helper to format data quality for display
export function formatDataQuality(quality: DataQualityMetrics): string {
  const parts = [`${quality.completenessScore}% complete`]
  
  if (quality.isStale) {
    parts.push('⚠️ STALE')
  }
  
  if (quality.warnings.length > 0) {
    parts.push(`${quality.warnings.length} warnings`)
  }
  
  return parts.join(' • ')
}

// Helper to get quality indicator color
export function getQualityColor(score: number): string {
  if (score >= 90) return '#22c55e' // green
  if (score >= 70) return '#eab308' // yellow
  if (score >= 50) return '#f97316' // orange
  return '#ef4444' // red
}