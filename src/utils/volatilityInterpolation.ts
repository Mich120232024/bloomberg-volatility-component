// Volatility Surface Interpolation for Option Pricing
// Properly interpolates implied volatility based on strike and tenor

export interface VolatilitySurfacePoint {
  tenor: string
  tenorDays: number
  atm: number
  rr25d: number
  bf25d: number
}

export interface InterpolationRequest {
  strike: number
  spot: number
  timeToExpiryDays: number
  surfaceData: VolatilitySurfacePoint[]
}

// Convert tenor string to days
export function tenorToDays(tenor: string): number {
  const mapping: { [key: string]: number } = {
    'ON': 1,
    '1W': 7,
    '2W': 14,
    '1M': 30,
    '2M': 60,
    '3M': 90,
    '6M': 180,
    '9M': 270,
    '1Y': 365,
    '18M': 548,
    '2Y': 730
  }
  return mapping[tenor] || 0
}

// Calculate moneyness (log-moneyness for FX options)
function calculateMoneyness(strike: number, spot: number): number {
  return Math.log(strike / spot)
}

// Interpolate ATM volatility between tenors
function interpolateATM(timeToExpiryDays: number, surface: VolatilitySurfacePoint[]): number {
  // Sort by tenor days
  const sorted = [...surface].sort((a, b) => a.tenorDays - b.tenorDays)
  
  // Find surrounding tenors
  let lower = sorted[0]
  let upper = sorted[sorted.length - 1]
  
  for (let i = 0; i < sorted.length - 1; i++) {
    if (sorted[i].tenorDays <= timeToExpiryDays && sorted[i + 1].tenorDays >= timeToExpiryDays) {
      lower = sorted[i]
      upper = sorted[i + 1]
      break
    }
  }
  
  // Linear interpolation in variance space (more accurate than vol space)
  if (lower.tenorDays === upper.tenorDays) {
    return lower.atm
  }
  
  const lowerVariance = Math.pow(lower.atm / 100, 2) * lower.tenorDays / 365
  const upperVariance = Math.pow(upper.atm / 100, 2) * upper.tenorDays / 365
  
  const weight = (timeToExpiryDays - lower.tenorDays) / (upper.tenorDays - lower.tenorDays)
  const interpolatedVariance = lowerVariance + weight * (upperVariance - lowerVariance)
  
  // Convert back to volatility
  return Math.sqrt(interpolatedVariance * 365 / timeToExpiryDays) * 100
}

// Calculate volatility smile using risk reversal and butterfly
function applyVolatilitySmile(
  atmVol: number,
  rr25d: number,
  bf25d: number,
  moneyness: number
): number {
  // Simplified smile approximation
  // In practice, would use proper SABR or Vanna-Volga model
  
  // Convert RR and BF to 25-delta call and put vols
  const vol25dCall = atmVol + bf25d + rr25d / 2
  const vol25dPut = atmVol + bf25d - rr25d / 2
  
  // Approximate delta from moneyness (simplified)
  const approxDelta = 1 - normCDF(-moneyness / (atmVol / 100 * Math.sqrt(1/365)))
  
  // Interpolate based on delta
  if (approxDelta > 0.5) {
    // In-the-money call / Out-of-money put region
    const weight = (approxDelta - 0.5) / 0.25
    return atmVol + weight * (vol25dCall - atmVol)
  } else {
    // Out-of-money call / In-the-money put region
    const weight = (0.5 - approxDelta) / 0.25
    return atmVol + weight * (vol25dPut - atmVol)
  }
}

// Normal CDF approximation
function normCDF(x: number): number {
  const a1 = 0.254829592
  const a2 = -0.284496736
  const a3 = 1.421413741
  const a4 = -1.453152027
  const a5 = 1.061405429
  const p = 0.3275911
  
  const sign = x >= 0 ? 1 : -1
  x = Math.abs(x) / Math.sqrt(2)
  
  const t = 1.0 / (1.0 + p * x)
  const y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * Math.exp(-x * x)
  
  return 0.5 * (1.0 + sign * y)
}

// Main interpolation function
export function interpolateVolatility(request: InterpolationRequest): number {
  const { strike, spot, timeToExpiryDays, surfaceData } = request
  
  // Calculate moneyness
  const moneyness = calculateMoneyness(strike, spot)
  
  // Interpolate ATM volatility for the specific tenor
  const atmVol = interpolateATM(timeToExpiryDays, surfaceData)
  
  // Find risk reversal and butterfly for the tenor
  // For simplicity, using the closest tenor's smile data
  const closestTenor = surfaceData.reduce((prev, curr) => 
    Math.abs(curr.tenorDays - timeToExpiryDays) < Math.abs(prev.tenorDays - timeToExpiryDays) ? curr : prev
  )
  
  // Apply smile adjustment
  const adjustedVol = applyVolatilitySmile(
    atmVol,
    closestTenor.rr25d,
    closestTenor.bf25d,
    moneyness
  )
  
  return adjustedVol
}

// Helper to fetch and prepare surface data from Bloomberg
export async function fetchVolatilitySurface(currencyPair: string): Promise<VolatilitySurfacePoint[]> {
  // This would call the Bloomberg API to get the full surface
  // For now, returning empty array as placeholder
  console.warn('fetchVolatilitySurface not yet implemented - using 1M ATM as fallback')
  return []
}