import { useState, useEffect } from 'react'
import { useTheme } from '../contexts/ThemeContext'
import { garmanKohlhagen, calculateForward, type FXOptionResult } from '../utils/garmanKohlhagen'

interface OptionParameters {
  currencyPair: string
  tenor: string
  strike: number
  optionType: 'call' | 'put'
  notional: number
}

interface OptionPrice extends FXOptionResult {
  impliedVol: number
}

export function OptionsPricingTab() {
  const { currentTheme } = useTheme()
  
  // Option parameters
  const [params, setParams] = useState<OptionParameters>({
    currencyPair: 'EURUSD',
    tenor: '1M',
    strike: 1.0850, // Current spot + forward
    optionType: 'call',
    notional: 1000000
  })
  
  // Pricing results
  const [pricing, setPricing] = useState<OptionPrice | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // Market data - NO FALLBACKS, only real Bloomberg data
  const [spotRate, setSpotRate] = useState<number | null>(null)
  const [forwardRate, setForwardRate] = useState<number | null>(null)
  const [forwardPoints, setForwardPoints] = useState<number | null>(null)
  const [volatility, setVolatility] = useState<number | null>(null)
  const [riskFreeRate, setRiskFreeRate] = useState<number | null>(null)
  const [eurRate, setEurRate] = useState<number | null>(null)
  const [usdRate, setUsdRate] = useState<number | null>(null)
  
  
  // Fetch market data and calculate pricing
  const fetchMarketData = async () => {
    setLoading(true)
    setError(null)
    
    try {
      // Fetch spot rate
      const endpoint = 'http://localhost:8000/api/bloomberg/reference' // Always use local gateway
      const spotResponse = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Authorization': 'Bearer test',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          securities: [`${params.currencyPair} Curncy`],
          fields: ['PX_LAST']
        })
      })
      const spotData = await spotResponse.json()
      // STRICT: Only use real Bloomberg data, no fallbacks
      if (!spotData.success || !spotData.data?.securities_data?.[0]?.success) {
        throw new Error(`EURUSD spot rate failed: ${JSON.stringify(spotData)}`)
      }
      const currentSpot = spotData.data.securities_data[0].fields?.PX_LAST
      if (!currentSpot) {
        throw new Error(`EURUSD spot rate is null`)
      }
      
      // Fetch volatility (ATM) - NO FALLBACKS
      const volResponse = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Authorization': 'Bearer test',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          securities: [`${params.currencyPair}V${params.tenor} BGN Curncy`],
          fields: ['PX_LAST']
        })
      })
      const volData = await volResponse.json()
      
      if (!volData.success || !volData.data?.securities_data?.[0]?.success) {
        throw new Error(`${params.currencyPair} ${params.tenor} volatility failed: ${JSON.stringify(volData)}`)
      }
      const currentVol = volData.data.securities_data[0].fields?.PX_LAST
      if (!currentVol) {
        throw new Error(`${params.currencyPair} ${params.tenor} volatility is null`)
      }
      
      // Fetch EUR and USD interest rates
      const [baseCcy, quoteCcy] = params.currencyPair.slice(0, 3) === 'EUR' ? ['EUR', 'USD'] : ['USD', params.currencyPair.slice(3, 6)]
      
      // Get EUR rate (1M EURIBOR)
      const eurResponse = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Authorization': 'Bearer test',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          securities: ['EUR001M Index'],
          fields: ['PX_LAST']
        })
      })
      const eurData = await eurResponse.json()
      const eurDepoRate = eurData.data?.securities_data?.[0]?.fields?.PX_LAST
      if (!eurDepoRate) {
        throw new Error('EUR001M Index rate failed - no fallback allowed')
      }
      
      // Get USD rate (1M SOFR)
      const usdResponse = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Authorization': 'Bearer test',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          securities: ['US0001M Index'],
          fields: ['PX_LAST']
        })
      })
      const usdData = await usdResponse.json()
      const usdDepoRate = usdData.data?.securities_data?.[0]?.fields?.PX_LAST
      if (!usdDepoRate) {
        throw new Error('US0001M Index rate failed - no fallback allowed')
      }
      
      // Calculate tenor in years
      const tenorYears = params.tenor === '1W' ? 1/52 : 
                        params.tenor === '2W' ? 2/52 :
                        params.tenor === '1M' ? 1/12 : 
                        params.tenor === '2M' ? 2/12 :
                        params.tenor === '3M' ? 3/12 : 1/12
      
      // Calculate forward rate using interest rate parity
      const rBase = baseCcy === 'EUR' ? eurDepoRate : usdDepoRate
      const rQuote = quoteCcy === 'USD' ? usdDepoRate : eurDepoRate
      const calculatedForward = calculateForward(currentSpot, tenorYears, rQuote, rBase)
      const calculatedForwardPoints = (calculatedForward - currentSpot) * 10000
      
      // Update market data with REAL Bloomberg values
      setSpotRate(currentSpot)
      setVolatility(currentVol)
      setForwardRate(calculatedForward)
      setForwardPoints(calculatedForwardPoints)
      setEurRate(eurDepoRate)
      setUsdRate(usdDepoRate)
      setRiskFreeRate(rQuote) // Use quote currency rate
      
      // Only calculate if we have ALL real data
      if (currentSpot && currentVol && rQuote !== undefined && rBase !== undefined) {
        // DEBUG: Log professional pricing inputs
        console.log('=== PROFESSIONAL GARMAN-KOHLHAGEN PRICING ===')
        console.log('Spot (S):', currentSpot)
        console.log('Strike (K):', params.strike)
        console.log('Time (T):', tenorYears, 'years')
        console.log('Domestic rate (rd):', rQuote, '% (quote currency)')
        console.log('Foreign rate (rf):', rBase, '% (base currency)')
        console.log('Volatility:', currentVol, '%')
        console.log('Forward:', calculatedForward)
        console.log('Forward Points:', calculatedForwardPoints.toFixed(2))
        
        // Use professional Garman-Kohlhagen implementation
        const result = garmanKohlhagen(
          currentSpot,
          params.strike,
          tenorYears,
          rQuote,    // Quote currency rate (e.g., USD for EURUSD)
          rBase,     // Base currency rate (e.g., EUR for EURUSD)
          currentVol,
          params.optionType,
          params.notional
        )
        
        // Convert to component's OptionPrice interface
        setPricing({
          ...result,
          impliedVol: currentVol
        })
        
        console.log('Premium %:', result.premiumPercent.toFixed(4), '%')
        console.log('Premium amount:', result.premium.toFixed(2))
        console.log('Delta:', result.delta)
        console.log('Gamma:', result.gamma)
        console.log('Vega:', result.vega)
        console.log('Theta:', result.theta)
      } else {
        throw new Error('Incomplete market data - cannot calculate option price')
      }
      
    } catch (err) {
      setError(`Failed to fetch market data: ${err instanceof Error ? err.message : 'Unknown error'}`)
    } finally {
      setLoading(false)
    }
  }
  
  // Auto-update on parameter changes
  useEffect(() => {
    fetchMarketData()
  }, [params.currencyPair, params.tenor, params.strike, params.optionType])
  
  return (
    <div style={{ 
      backgroundColor: currentTheme.background,
      color: currentTheme.text,
      height: '100%'
    }}>
      <div style={{ display: 'flex', gap: '20px', height: '100%' }}>
        {/* Parameters Panel - Bloomberg Style */}
        <div style={{
          width: '240px',
          backgroundColor: currentTheme.surface,
          padding: '8px',
          borderRadius: '2px',
          border: `1px solid ${currentTheme.border}`,
          height: 'fit-content'
        }}>
          <div style={{ margin: '0 0 8px 0', fontSize: '11px', fontWeight: '600', textTransform: 'uppercase' }}>
            OPTION PARAMETERS
          </div>
          
          {/* Currency Pair */}
          <div style={{ marginBottom: '8px' }}>
            <label style={{ display: 'block', fontSize: '9px', fontWeight: '600', marginBottom: '2px', color: currentTheme.textSecondary, textTransform: 'uppercase' }}>
              CCY PAIR
            </label>
            <select
              value={params.currencyPair}
              onChange={(e) => setParams(prev => ({ ...prev, currencyPair: e.target.value }))}
              style={{
                width: '100%',
                padding: '4px',
                backgroundColor: currentTheme.background,
                color: currentTheme.text,
                border: `1px solid ${currentTheme.border}`,
                borderRadius: '2px',
                fontSize: '11px',
                fontFamily: 'monospace'
              }}
            >
              <option value="EURUSD">EUR/USD</option>
              <option value="GBPUSD">GBP/USD</option>
              <option value="USDJPY">USD/JPY</option>
              <option value="USDCHF">USD/CHF</option>
            </select>
          </div>
          
          {/* Tenor */}
          <div style={{ marginBottom: '8px' }}>
            <label style={{ display: 'block', fontSize: '9px', fontWeight: '600', marginBottom: '2px', color: currentTheme.textSecondary, textTransform: 'uppercase' }}>
              TENOR
            </label>
            <select
              value={params.tenor}
              onChange={(e) => setParams(prev => ({ ...prev, tenor: e.target.value }))}
              style={{
                width: '100%',
                padding: '4px',
                backgroundColor: currentTheme.background,
                color: currentTheme.text,
                border: `1px solid ${currentTheme.border}`,
                borderRadius: '2px',
                fontSize: '11px',
                fontFamily: 'monospace'
              }}
            >
              <option value="1W">1W</option>
              <option value="2W">2W</option>
              <option value="1M">1M</option>
              <option value="2M">2M</option>
              <option value="3M">3M</option>
            </select>
          </div>
          
          {/* Strike */}
          <div style={{ marginBottom: '8px' }}>
            <label style={{ display: 'block', fontSize: '9px', fontWeight: '600', marginBottom: '2px', color: currentTheme.textSecondary, textTransform: 'uppercase' }}>
              STRIKE
            </label>
            <div style={{ display: 'flex', gap: '4px', marginBottom: '4px' }}>
              <button
                onClick={() => {
                  if (forwardRate) {
                    // CRITICAL FIX: Use full precision for ATMF strike
                    setParams(prev => ({ ...prev, strike: forwardRate }))
                    console.log('ATMF: Setting strike to exact forward:', forwardRate)
                  }
                }}
                disabled={!forwardRate}
                style={{
                  padding: '2px 6px',
                  backgroundColor: forwardRate && Math.abs(params.strike - forwardRate) < 0.0001 ? currentTheme.primary : currentTheme.background,
                  color: forwardRate && Math.abs(params.strike - forwardRate) < 0.0001 ? 'white' : currentTheme.text,
                  border: `1px solid ${currentTheme.border}`,
                  borderRadius: '2px',
                  cursor: forwardRate ? 'pointer' : 'not-allowed',
                  fontSize: '9px',
                  fontWeight: '600',
                  fontFamily: 'monospace'
                }}
              >
                ATMF
              </button>
              <button
                onClick={() => {
                  if (spotRate) {
                    setParams(prev => ({ ...prev, strike: spotRate }))
                  }
                }}
                disabled={!spotRate}
                style={{
                  padding: '2px 6px',
                  backgroundColor: spotRate && Math.abs(params.strike - spotRate) < 0.0001 ? currentTheme.primary : currentTheme.background,
                  color: spotRate && Math.abs(params.strike - spotRate) < 0.0001 ? 'white' : currentTheme.text,
                  border: `1px solid ${currentTheme.border}`,
                  borderRadius: '2px',
                  cursor: spotRate ? 'pointer' : 'not-allowed',
                  fontSize: '9px',
                  fontWeight: '600',
                  fontFamily: 'monospace'
                }}
              >
                ATMS
              </button>
            </div>
            <input
              type="number"
              step="0.0001"
              value={params.strike}
              onChange={(e) => setParams(prev => ({ ...prev, strike: parseFloat(e.target.value) || 0 }))}
              style={{
                width: '100%',
                padding: '4px',
                backgroundColor: currentTheme.background,
                color: currentTheme.text,
                border: `1px solid ${currentTheme.border}`,
                borderRadius: '2px',
                fontSize: '11px',
                fontFamily: 'monospace'
              }}
            />
          </div>
          
          {/* Option Type */}
          <div style={{ marginBottom: '8px' }}>
            <label style={{ display: 'block', fontSize: '9px', fontWeight: '600', marginBottom: '2px', color: currentTheme.textSecondary, textTransform: 'uppercase' }}>
              TYPE
            </label>
            <div style={{ display: 'flex', gap: '4px' }}>
              <button
                onClick={() => setParams(prev => ({ ...prev, optionType: 'call' }))}
                style={{
                  flex: 1,
                  padding: '4px',
                  backgroundColor: params.optionType === 'call' ? currentTheme.primary : currentTheme.background,
                  color: params.optionType === 'call' ? 'white' : currentTheme.text,
                  border: `1px solid ${currentTheme.border}`,
                  borderRadius: '2px',
                  cursor: 'pointer',
                  fontSize: '10px',
                  fontWeight: '600',
                  fontFamily: 'monospace',
                  textTransform: 'uppercase'
                }}
              >
                CALL
              </button>
              <button
                onClick={() => setParams(prev => ({ ...prev, optionType: 'put' }))}
                style={{
                  flex: 1,
                  padding: '4px',
                  backgroundColor: params.optionType === 'put' ? currentTheme.primary : currentTheme.background,
                  color: params.optionType === 'put' ? 'white' : currentTheme.text,
                  border: `1px solid ${currentTheme.border}`,
                  borderRadius: '2px',
                  cursor: 'pointer',
                  fontSize: '10px',
                  fontWeight: '600',
                  fontFamily: 'monospace',
                  textTransform: 'uppercase'
                }}
              >
                PUT
              </button>
            </div>
          </div>
          
          {/* Notional */}
          <div style={{ marginBottom: '8px' }}>
            <label style={{ display: 'block', fontSize: '9px', fontWeight: '600', marginBottom: '2px', color: currentTheme.textSecondary, textTransform: 'uppercase' }}>
              NOTIONAL
            </label>
            <input
              type="number"
              step="10000"
              value={params.notional}
              onChange={(e) => setParams(prev => ({ ...prev, notional: parseFloat(e.target.value) || 0 }))}
              style={{
                width: '100%',
                padding: '4px',
                backgroundColor: currentTheme.background,
                color: currentTheme.text,
                border: `1px solid ${currentTheme.border}`,
                borderRadius: '2px',
                fontSize: '11px',
                fontFamily: 'monospace'
              }}
            />
          </div>
          
          <button
            onClick={fetchMarketData}
            disabled={loading}
            style={{
              width: '100%',
              padding: '6px',
              backgroundColor: currentTheme.primary,
              color: 'white',
              border: 'none',
              borderRadius: '2px',
              cursor: loading ? 'not-allowed' : 'pointer',
              fontSize: '10px',
              fontWeight: '700',
              fontFamily: 'monospace',
              textTransform: 'uppercase'
            }}
          >
            {loading ? 'CALCULATING...' : 'CALCULATE'}
          </button>
        </div>
        
        {/* Results Panel - Bloomberg Style */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {/* Compact Market Data Grid */}
          <div style={{
            backgroundColor: currentTheme.surface,
            padding: '8px',
            border: `1px solid ${currentTheme.border}`,
            borderRadius: '2px'
          }}>
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: 'repeat(2, 1fr)', 
              gap: '1px',
              backgroundColor: currentTheme.border
            }}>
              {/* Row 1 */}
              <div style={{ backgroundColor: currentTheme.surface, padding: '4px 6px', display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '10px', color: currentTheme.textSecondary }}>SPOT</span>
                <span style={{ fontSize: '11px', fontFamily: 'monospace', fontWeight: '600', color: currentTheme.primary }}>
                  {spotRate ? spotRate.toFixed(5) : '-.-----'}
                </span>
              </div>
              <div style={{ backgroundColor: currentTheme.surface, padding: '4px 6px', display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '10px', color: currentTheme.textSecondary }}>FWD</span>
                <span style={{ fontSize: '11px', fontFamily: 'monospace', fontWeight: '600', color: currentTheme.primary }}>
                  {forwardRate ? forwardRate.toFixed(5) : '-.-----'}
                </span>
              </div>
              
              {/* Row 2 */}
              <div style={{ backgroundColor: currentTheme.surface, padding: '4px 6px', display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '10px', color: currentTheme.textSecondary }}>PTS</span>
                <span style={{ fontSize: '11px', fontFamily: 'monospace', fontWeight: '600', color: forwardPoints && forwardPoints > 0 ? '#4ade80' : '#ef4444' }}>
                  {forwardPoints ? (forwardPoints > 0 ? '+' : '') + forwardPoints.toFixed(2) : '-.--'}
                </span>
              </div>
              <div style={{ backgroundColor: currentTheme.surface, padding: '4px 6px', display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '10px', color: currentTheme.textSecondary }}>VOL</span>
                <span style={{ fontSize: '11px', fontFamily: 'monospace', fontWeight: '600', color: currentTheme.primary }}>
                  {volatility ? volatility.toFixed(2) + '%' : '--.--'}
                </span>
              </div>
              
              {/* Row 3 */}
              <div style={{ backgroundColor: currentTheme.surface, padding: '4px 6px', display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '10px', color: currentTheme.textSecondary }}>EUR</span>
                <span style={{ fontSize: '11px', fontFamily: 'monospace', fontWeight: '600' }}>
                  {eurRate ? eurRate.toFixed(3) + '%' : '-.---'}
                </span>
              </div>
              <div style={{ backgroundColor: currentTheme.surface, padding: '4px 6px', display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '10px', color: currentTheme.textSecondary }}>USD</span>
                <span style={{ fontSize: '11px', fontFamily: 'monospace', fontWeight: '600' }}>
                  {usdRate ? usdRate.toFixed(3) + '%' : '-.---'}
                </span>
              </div>
            </div>
          </div>
          
          {/* Pricing Results - Bloomberg Style */}
          {pricing && (
            <>
              {/* Premium Section */}
              <div style={{
                backgroundColor: currentTheme.surface,
                padding: '8px',
                border: `1px solid ${currentTheme.border}`,
                borderRadius: '2px'
              }}>
                <div style={{ marginBottom: '6px' }}>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: '12px' }}>
                    <span style={{ fontSize: '10px', color: currentTheme.textSecondary }}>PREMIUM</span>
                    <span style={{ fontSize: '16px', fontFamily: 'monospace', fontWeight: '700', color: currentTheme.primary }}>
                      {pricing.premiumPercent.toFixed(4)}%
                    </span>
                    <span style={{ fontSize: '12px', fontFamily: 'monospace', fontWeight: '600' }}>
                      ${pricing.premium.toLocaleString()}
                    </span>
                    <span style={{ fontSize: '10px', fontFamily: 'monospace', color: currentTheme.textSecondary }}>
                      ({(pricing.premiumPercent * 100).toFixed(1)} pips)
                    </span>
                  </div>
                </div>
              </div>
              
              {/* Greeks Grid - Bloomberg Style */}
              <div style={{
                backgroundColor: currentTheme.surface,
                padding: '8px',
                border: `1px solid ${currentTheme.border}`,
                borderRadius: '2px'
              }}>
                <div style={{ 
                  display: 'grid', 
                  gridTemplateColumns: 'repeat(4, 1fr)', 
                  gap: '1px',
                  backgroundColor: currentTheme.border
                }}>
                  <div style={{ backgroundColor: currentTheme.surface, padding: '4px 6px' }}>
                    <div style={{ fontSize: '9px', color: currentTheme.textSecondary }}>DELTA</div>
                    <div style={{ fontSize: '11px', fontFamily: 'monospace', fontWeight: '600' }}>
                      {pricing.delta.toFixed(2)}%
                    </div>
                  </div>
                  <div style={{ backgroundColor: currentTheme.surface, padding: '4px 6px' }}>
                    <div style={{ fontSize: '9px', color: currentTheme.textSecondary }}>GAMMA</div>
                    <div style={{ fontSize: '11px', fontFamily: 'monospace', fontWeight: '600' }}>
                      {pricing.gamma.toFixed(5)}
                    </div>
                  </div>
                  <div style={{ backgroundColor: currentTheme.surface, padding: '4px 6px' }}>
                    <div style={{ fontSize: '9px', color: currentTheme.textSecondary }}>VEGA</div>
                    <div style={{ fontSize: '11px', fontFamily: 'monospace', fontWeight: '600' }}>
                      ${(pricing.vegaNotional || pricing.vega).toFixed(0)}
                    </div>
                  </div>
                  <div style={{ backgroundColor: currentTheme.surface, padding: '4px 6px' }}>
                    <div style={{ fontSize: '9px', color: currentTheme.textSecondary }}>THETA</div>
                    <div style={{ fontSize: '11px', fontFamily: 'monospace', fontWeight: '600' }}>
                      ${(pricing.thetaNotional || pricing.theta).toFixed(0)}
                    </div>
                  </div>
                </div>
                
                {/* Second row of Greeks */}
                <div style={{ 
                  display: 'grid', 
                  gridTemplateColumns: 'repeat(2, 1fr)', 
                  gap: '1px',
                  backgroundColor: currentTheme.border,
                  marginTop: '1px'
                }}>
                  <div style={{ backgroundColor: currentTheme.surface, padding: '4px 6px' }}>
                    <div style={{ fontSize: '9px', color: currentTheme.textSecondary }}>RHO (USD)</div>
                    <div style={{ fontSize: '11px', fontFamily: 'monospace', fontWeight: '600' }}>
                      ${pricing.rhoNotional ? pricing.rhoNotional.toFixed(0) : pricing.rho ? pricing.rho.toFixed(0) : '0'}
                    </div>
                  </div>
                  <div style={{ backgroundColor: currentTheme.surface, padding: '4px 6px' }}>
                    <div style={{ fontSize: '9px', color: currentTheme.textSecondary }}>IV</div>
                    <div style={{ fontSize: '11px', fontFamily: 'monospace', fontWeight: '600' }}>
                      {pricing.impliedVol.toFixed(2)}%
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Delta Hedge - Bloomberg Style */}
              <div style={{
                backgroundColor: currentTheme.surface,
                padding: '8px',
                border: `1px solid ${currentTheme.border}`,
                borderRadius: '2px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div>
                    <span style={{ fontSize: '10px', color: currentTheme.textSecondary }}>DELTA HEDGE</span>
                    <span style={{ fontSize: '11px', color: currentTheme.textSecondary, marginLeft: '8px' }}>
                      ({params.optionType === 'call' ? 'Sell' : 'Buy'} {params.currencyPair.slice(0, 3)})
                    </span>
                  </div>
                  <span style={{ 
                    fontSize: '14px', 
                    fontFamily: 'monospace', 
                    fontWeight: '700', 
                    color: pricing.delta < 0 ? '#ef4444' : '#4ade80' 
                  }}>
                    {params.currencyPair.slice(0, 3)} {(pricing.deltaNotional ? -pricing.deltaNotional : 0).toLocaleString(undefined, { 
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2 
                    })}
                  </span>
                </div>
              </div>
            </>
          )}
          
          {error && (
            <div style={{
              backgroundColor: '#ff4444',
              color: 'white',
              padding: '16px',
              borderRadius: '8px',
              marginTop: '20px'
            }}>
              {error}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}