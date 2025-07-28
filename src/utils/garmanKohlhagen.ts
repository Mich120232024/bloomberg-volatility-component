// Correct Garman-Kohlhagen implementation for FX options

export interface FXOptionResult {
  premium: number          // Option premium in quote currency (notional adjusted)
  premiumPercent: number   // Premium as % of spot
  delta: number            // Option delta percentage (-100% to 100%)
  deltaNotional: number    // Delta in base currency amount
  gamma: number            // Option gamma per 1% spot move
  gammaNotional: number    // Gamma in base currency amount
  vega: number             // Option vega per 1% vol move
  vegaNotional: number     // Vega in quote currency amount
  theta: number            // Option theta per day
  thetaNotional: number    // Theta in quote currency amount
  rho: number              // Option rho per 1% rate move
  rhoNotional: number      // Rho in quote currency amount
}

// Accurate normal CDF approximation
function normCDF(x: number): number {
  const a1 =  0.254829592
  const a2 = -0.284496736
  const a3 =  1.421413741
  const a4 = -1.453152027
  const a5 =  1.061405429
  const p  =  0.3275911
  
  const sign = x >= 0 ? 1 : -1
  x = Math.abs(x) / Math.sqrt(2)
  
  const t = 1.0 / (1.0 + p * x)
  const y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * Math.exp(-x * x)
  
  return 0.5 * (1.0 + sign * y)
}

// Normal PDF
function normPDF(x: number): number {
  return Math.exp(-0.5 * x * x) / Math.sqrt(2 * Math.PI)
}

/**
 * Calculate FX option price using Garman-Kohlhagen model
 * @param S - Spot price (e.g., 1.1742 for EURUSD)
 * @param K - Strike price
 * @param T - Time to expiry in years (e.g., 0.0833 for 1 month)
 * @param rd - Domestic (quote currency) interest rate in % (e.g., 4.96 for USD)
 * @param rf - Foreign (base currency) interest rate in % (e.g., 1.90 for EUR)
 * @param vol - Implied volatility in % (e.g., 7.34)
 * @param optType - 'call' or 'put'
 * @param notional - Notional amount in base currency (optional, default 1)
 */
export function garmanKohlhagen(
  S: number,
  K: number,
  T: number,
  rd: number,   // Quote currency rate
  rf: number,   // Base currency rate
  vol: number,
  optType: 'call' | 'put',
  notional: number = 1
): FXOptionResult {
  // Convert percentages to decimals
  const r_d = rd / 100
  const r_f = rf / 100
  const sigma = vol / 100
  
  // Calculate d1 and d2
  const d1 = (Math.log(S / K) + (r_d - r_f + 0.5 * sigma * sigma) * T) / (sigma * Math.sqrt(T))
  const d2 = d1 - sigma * Math.sqrt(T)
  
  // CDFs and PDFs
  const Nd1 = normCDF(d1)
  const Nd2 = normCDF(d2)
  const nd1 = normPDF(d1)
  const nd2 = normPDF(d2)
  
  // Option value
  let premium: number
  let delta: number
  
  if (optType === 'call') {
    // European call
    premium = S * Math.exp(-r_f * T) * Nd1 - K * Math.exp(-r_d * T) * Nd2
    // FX delta (premium adjusted)
    delta = Math.exp(-r_f * T) * Nd1
  } else {
    // European put
    premium = K * Math.exp(-r_d * T) * (1 - Nd2) - S * Math.exp(-r_f * T) * (1 - Nd1)
    // FX delta (premium adjusted)
    delta = Math.exp(-r_f * T) * (Nd1 - 1)
  }
  
  // Greeks
  const gamma = Math.exp(-r_f * T) * nd1 / (S * sigma * Math.sqrt(T))
  const vega = S * Math.exp(-r_f * T) * nd1 * Math.sqrt(T) / 100  // Per 1% vol
  
  // Theta (per day, not per year)
  let theta: number
  if (optType === 'call') {
    theta = (-S * nd1 * sigma * Math.exp(-r_f * T) / (2 * Math.sqrt(T)) 
             - r_d * K * Math.exp(-r_d * T) * Nd2
             + r_f * S * Math.exp(-r_f * T) * Nd1) / 365
  } else {
    theta = (-S * nd1 * sigma * Math.exp(-r_f * T) / (2 * Math.sqrt(T))
             + r_d * K * Math.exp(-r_d * T) * (1 - Nd2)
             - r_f * S * Math.exp(-r_f * T) * (1 - Nd1)) / 365
  }
  
  // Rho (per 1% move in domestic rate)
  const rho = optType === 'call' 
    ? K * T * Math.exp(-r_d * T) * Nd2 / 100
    : -K * T * Math.exp(-r_d * T) * (1 - Nd2) / 100
  
  return {
    premium: premium * notional,
    premiumPercent: (premium / S) * 100,
    delta: delta * 100,  // Delta as percentage
    deltaNotional: delta * notional,
    gamma: gamma * 100,  // Gamma per 1% spot move
    gammaNotional: gamma * notional,
    vega: vega,  // Already per 1% vol move
    vegaNotional: vega * notional,
    theta: theta,  // Already per day
    thetaNotional: theta * notional,
    rho: rho,  // Already per 1% rate move
    rhoNotional: rho * notional
  }
}

// Helper to calculate forward rate
export function calculateForward(S: number, T: number, rd: number, rf: number): number {
  return S * Math.exp((rd - rf) * T / 100)
}