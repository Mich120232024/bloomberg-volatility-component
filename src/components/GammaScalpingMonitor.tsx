import { useState, useEffect } from 'react'
import { useTheme } from '../contexts/ThemeContext'

interface GammaPosition {
  pair: string
  spotPrice: number
  strikePrice: number
  optionType: 'CALL' | 'PUT'
  quantity: number
  tenor: string
  impliedVol: number
  delta: number
  gamma: number
  vega: number
  theta: number
  daysToExpiry: number
}

interface ScalpingMetrics {
  pair: string
  realizedVol30D: number
  impliedVol: number
  volSpread: number
  gammaExposure: number
  deltaExposure: number
  breakevenVol: number
  currentPnL: number
  rebalanceSignal: 'REBALANCE_NOW' | 'WAIT' | 'CLOSE_POSITION'
  lastRebalance: Date
  rebalanceCount: number
}

// Black-Scholes Greeks calculation
function calculateGreeks(spot: number, strike: number, vol: number, r: number, t: number, isCall: boolean) {
  const d1 = (Math.log(spot / strike) + (r + 0.5 * vol * vol) * t) / (vol * Math.sqrt(t))
  const d2 = d1 - vol * Math.sqrt(t)
  
  // Standard normal CDF
  const N = (x: number) => {
    const a1 = 0.254829592
    const a2 = -0.284496736
    const a3 = 1.421413741
    const a4 = -1.453152027
    const a5 = 1.061405429
    const p = 0.3275911
    const sign = x < 0 ? -1 : 1
    x = Math.abs(x) / Math.sqrt(2.0)
    const t = 1.0 / (1.0 + p * x)
    const y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * Math.exp(-x * x)
    return 0.5 * (1.0 + sign * y)
  }
  
  // Standard normal PDF
  const n = (x: number) => Math.exp(-0.5 * x * x) / Math.sqrt(2 * Math.PI)
  
  const delta = isCall ? N(d1) : N(d1) - 1
  const gamma = n(d1) / (spot * vol * Math.sqrt(t))
  const vega = spot * n(d1) * Math.sqrt(t) / 100 // Per 1% vol move
  const theta = isCall ? 
    -(spot * n(d1) * vol) / (2 * Math.sqrt(t)) - r * strike * Math.exp(-r * t) * N(d2) :
    -(spot * n(d1) * vol) / (2 * Math.sqrt(t)) + r * strike * Math.exp(-r * t) * (1 - N(d2))
  
  return { delta, gamma, vega, theta: theta / 365 } // Daily theta
}

export function GammaScalpingMonitor() {
  const { currentTheme } = useTheme()
  const [loading, setLoading] = useState(true)
  const [positions, setPositions] = useState<GammaPosition[]>([])
  const [metrics, setMetrics] = useState<ScalpingMetrics[]>([])
  const [spotPrices, setSpotPrices] = useState<Map<string, number>>(new Map())
  const [historicalVols, setHistoricalVols] = useState<Map<string, number>>(new Map())
  
  useEffect(() => {
    async function loadData() {
      try {
        // Fetch spot prices
        const spotResponse = await fetch('/api/bloomberg/reference', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test'
          },
          body: JSON.stringify({
            securities: ['EURUSD Curncy', 'GBPUSD Curncy', 'USDJPY Curncy'],
            fields: ['PX_LAST', 'VOLATILITY_30D']
          })
        })
        
        if (spotResponse.ok) {
          const spotData = await spotResponse.json()
          const newSpotPrices = new Map<string, number>()
          const newHistVols = new Map<string, number>()
          
          spotData.data?.securities_data.forEach((sec: any) => {
            if (sec.success) {
              const pair = sec.security.replace(' Curncy', '')
              if (sec.fields.PX_LAST) newSpotPrices.set(pair, sec.fields.PX_LAST)
              if (sec.fields.VOLATILITY_30D) newHistVols.set(pair, sec.fields.VOLATILITY_30D)
            }
          })
          
          setSpotPrices(newSpotPrices)
          setHistoricalVols(newHistVols)
        }
        
        // Simulate some gamma positions (in real app, load from portfolio)
        const samplePositions: GammaPosition[] = [
          {
            pair: 'EURUSD',
            spotPrice: spotPrices.get('EURUSD') || (() => { throw new Error('EURUSD spot price missing - no fallback allowed') })(),
            strikePrice: 1.1000,
            optionType: 'CALL',
            quantity: 1000000, // 1M EUR notional
            tenor: '1M',
            impliedVol: 7.5,
            delta: 0.45,
            gamma: 0.032,
            vega: 0.18,
            theta: -85,
            daysToExpiry: 30
          },
          {
            pair: 'GBPUSD',
            spotPrice: spotPrices.get('GBPUSD') || (() => { throw new Error('GBPUSD spot price missing - no fallback allowed') })(),
            strikePrice: 1.2650,
            optionType: 'PUT',
            quantity: 500000, // 500K GBP notional
            tenor: '2W',
            impliedVol: 8.2,
            delta: -0.38,
            gamma: 0.045,
            vega: 0.12,
            theta: -120,
            daysToExpiry: 14
          }
        ]
        
        setPositions(samplePositions)
        
        // Calculate gamma scalping metrics
        const newMetrics = samplePositions.map(pos => {
          const histVol = historicalVols.get(pos.pair) || pos.impliedVol
          const volSpread = pos.impliedVol - histVol
          const gammaExposure = pos.gamma * pos.quantity * pos.spotPrice
          const deltaExposure = pos.delta * pos.quantity
          
          // Breakeven vol = implied vol - theta decay / gamma P&L
          const dailyThetaInVol = Math.abs(pos.theta) / (pos.vega * 100)
          const breakevenVol = pos.impliedVol - dailyThetaInVol
          
          // Simulate P&L (in real app, calculate from actual trades)
          const daysSinceStart = 5
          const thetaLoss = pos.theta * daysSinceStart
          const gammaGain = 0.5 * gammaExposure * Math.pow(histVol / 100 * Math.sqrt(daysSinceStart / 365), 2) * 10000
          const currentPnL = thetaLoss + gammaGain
          
          // Rebalance signal based on delta drift
          const deltaDrift = Math.abs(deltaExposure) / pos.quantity
          let rebalanceSignal: 'REBALANCE_NOW' | 'WAIT' | 'CLOSE_POSITION' = 'WAIT'
          if (deltaDrift > 0.1) rebalanceSignal = 'REBALANCE_NOW'
          if (volSpread < -1 && currentPnL < 0) rebalanceSignal = 'CLOSE_POSITION'
          
          return {
            pair: pos.pair,
            realizedVol30D: histVol,
            impliedVol: pos.impliedVol,
            volSpread,
            gammaExposure,
            deltaExposure,
            breakevenVol,
            currentPnL,
            rebalanceSignal,
            lastRebalance: new Date(Date.now() - 2 * 60 * 60 * 1000), // 2 hours ago
            rebalanceCount: 3
          }
        })
        
        setMetrics(newMetrics)
        
      } catch (err) {
        console.error('Error loading gamma scalping data:', err)
      } finally {
        setLoading(false)
      }
    }
    
    loadData()
    // Refresh every 30 seconds
    const interval = setInterval(loadData, 30000)
    return () => clearInterval(interval)
  }, [])
  
  const getSignalColor = (signal: string) => {
    switch (signal) {
      case 'REBALANCE_NOW': return currentTheme.warning
      case 'CLOSE_POSITION': return currentTheme.danger
      default: return currentTheme.success
    }
  }
  
  const formatPnL = (pnl: number) => {
    const sign = pnl >= 0 ? '+' : ''
    return `${sign}$${Math.abs(pnl).toLocaleString('en-US', { maximumFractionDigits: 0 })}`
  }
  
  return (
    <div style={{ padding: '20px', backgroundColor: currentTheme.background }}>
      <h2 style={{ color: currentTheme.text, marginBottom: '20px' }}>
        Gamma Scalping Monitor
      </h2>
      
      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px', color: currentTheme.textSecondary }}>
          Loading gamma positions...
        </div>
      ) : (
        <>
          {/* Position Summary */}
          <div style={{ marginBottom: '24px' }}>
            <h3 style={{ color: currentTheme.text, fontSize: '16px', marginBottom: '12px' }}>
              Active Gamma Positions
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {positions.map((pos, idx) => (
                <div key={idx} style={{
                  backgroundColor: currentTheme.surface,
                  borderRadius: '8px',
                  padding: '16px',
                  border: `1px solid ${currentTheme.border}`
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                    <div>
                      <span style={{ fontSize: '18px', fontWeight: '700', color: currentTheme.text }}>
                        {pos.pair}
                      </span>
                      <span style={{
                        marginLeft: '12px',
                        padding: '4px 8px',
                        borderRadius: '4px',
                        fontSize: '12px',
                        backgroundColor: pos.optionType === 'CALL' ? currentTheme.success + '20' : currentTheme.danger + '20',
                        color: pos.optionType === 'CALL' ? currentTheme.success : currentTheme.danger
                      }}>
                        {pos.optionType} {pos.strikePrice}
                      </span>
                    </div>
                    <span style={{ fontSize: '14px', color: currentTheme.textSecondary }}>
                      {pos.tenor} ({pos.daysToExpiry}d)
                    </span>
                  </div>
                  
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '8px' }}>
                    <div>
                      <div style={{ fontSize: '11px', color: currentTheme.textSecondary }}>Delta</div>
                      <div style={{ fontSize: '14px', fontWeight: '600', color: currentTheme.text }}>
                        {pos.delta.toFixed(3)}
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: '11px', color: currentTheme.textSecondary }}>Gamma</div>
                      <div style={{ fontSize: '14px', fontWeight: '600', color: currentTheme.text }}>
                        {pos.gamma.toFixed(3)}
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: '11px', color: currentTheme.textSecondary }}>Vega</div>
                      <div style={{ fontSize: '14px', fontWeight: '600', color: currentTheme.text }}>
                        {pos.vega.toFixed(2)}
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: '11px', color: currentTheme.textSecondary }}>Theta</div>
                      <div style={{ fontSize: '14px', fontWeight: '600', color: currentTheme.danger }}>
                        ${pos.theta.toFixed(0)}
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: '11px', color: currentTheme.textSecondary }}>IV</div>
                      <div style={{ fontSize: '14px', fontWeight: '600', color: currentTheme.text }}>
                        {pos.impliedVol.toFixed(1)}%
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          {/* Scalping Metrics */}
          <div style={{ marginBottom: '24px' }}>
            <h3 style={{ color: currentTheme.text, fontSize: '16px', marginBottom: '12px' }}>
              Gamma Scalping Analysis
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {metrics.map((metric, idx) => (
                <div key={idx} style={{
                  backgroundColor: currentTheme.surface,
                  borderRadius: '8px',
                  padding: '16px',
                  border: `2px solid ${getSignalColor(metric.rebalanceSignal)}40`,
                  borderLeft: `6px solid ${getSignalColor(metric.rebalanceSignal)}`
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <span style={{ fontSize: '18px', fontWeight: '700', color: currentTheme.text }}>
                        {metric.pair}
                      </span>
                      <span style={{
                        padding: '4px 12px',
                        borderRadius: '4px',
                        fontSize: '13px',
                        fontWeight: '600',
                        backgroundColor: getSignalColor(metric.rebalanceSignal) + '20',
                        color: getSignalColor(metric.rebalanceSignal)
                      }}>
                        {metric.rebalanceSignal.replace('_', ' ')}
                      </span>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: '20px', fontWeight: '700', color: metric.currentPnL >= 0 ? currentTheme.success : currentTheme.danger }}>
                        {formatPnL(metric.currentPnL)}
                      </div>
                      <div style={{ fontSize: '11px', color: currentTheme.textSecondary }}>
                        Current P&L
                      </div>
                    </div>
                  </div>
                  
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', marginBottom: '12px' }}>
                    <div style={{
                      padding: '8px',
                      backgroundColor: currentTheme.background,
                      borderRadius: '4px',
                      textAlign: 'center'
                    }}>
                      <div style={{ fontSize: '11px', color: currentTheme.textSecondary }}>IV vs RV Spread</div>
                      <div style={{ 
                        fontSize: '16px', 
                        fontWeight: '600', 
                        color: metric.volSpread > 0 ? currentTheme.success : currentTheme.danger 
                      }}>
                        {metric.volSpread > 0 ? '+' : ''}{metric.volSpread.toFixed(2)}%
                      </div>
                    </div>
                    <div style={{
                      padding: '8px',
                      backgroundColor: currentTheme.background,
                      borderRadius: '4px',
                      textAlign: 'center'
                    }}>
                      <div style={{ fontSize: '11px', color: currentTheme.textSecondary }}>Breakeven Vol</div>
                      <div style={{ fontSize: '16px', fontWeight: '600', color: currentTheme.text }}>
                        {metric.breakevenVol.toFixed(2)}%
                      </div>
                    </div>
                    <div style={{
                      padding: '8px',
                      backgroundColor: currentTheme.background,
                      borderRadius: '4px',
                      textAlign: 'center'
                    }}>
                      <div style={{ fontSize: '11px', color: currentTheme.textSecondary }}>30D Realized</div>
                      <div style={{ fontSize: '16px', fontWeight: '600', color: currentTheme.text }}>
                        {metric.realizedVol30D.toFixed(2)}%
                      </div>
                    </div>
                  </div>
                  
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
                    <div>
                      <span style={{ color: currentTheme.textSecondary }}>Gamma $:</span>
                      <span style={{ marginLeft: '6px', color: currentTheme.text, fontWeight: '600' }}>
                        ${Math.abs(metric.gammaExposure).toLocaleString('en-US', { maximumFractionDigits: 0 })}
                      </span>
                    </div>
                    <div>
                      <span style={{ color: currentTheme.textSecondary }}>Delta $:</span>
                      <span style={{ marginLeft: '6px', color: currentTheme.text, fontWeight: '600' }}>
                        ${Math.abs(metric.deltaExposure).toLocaleString('en-US', { maximumFractionDigits: 0 })}
                      </span>
                    </div>
                    <div>
                      <span style={{ color: currentTheme.textSecondary }}>Rebalances:</span>
                      <span style={{ marginLeft: '6px', color: currentTheme.text, fontWeight: '600' }}>
                        {metric.rebalanceCount}
                      </span>
                    </div>
                    <div>
                      <span style={{ color: currentTheme.textSecondary }}>Last:</span>
                      <span style={{ marginLeft: '6px', color: currentTheme.text, fontWeight: '600' }}>
                        {new Date(metric.lastRebalance).toLocaleTimeString()}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          {/* Trading Guidelines */}
          <div style={{
            padding: '16px',
            backgroundColor: currentTheme.surface,
            borderRadius: '8px',
            borderLeft: `4px solid ${currentTheme.primary}`
          }}>
            <h4 style={{ color: currentTheme.text, marginBottom: '8px' }}>Gamma Scalping Guidelines:</h4>
            <ul style={{ 
              color: currentTheme.textSecondary, 
              fontSize: '13px',
              lineHeight: '1.8',
              paddingLeft: '20px'
            }}>
              <li><strong>REBALANCE NOW:</strong> Delta has drifted significantly - hedge by trading spot to restore delta neutrality</li>
              <li><strong>WAIT:</strong> Position is balanced - monitor for vol moves but no action needed</li>
              <li><strong>CLOSE POSITION:</strong> Realized vol consistently below breakeven - consider unwinding to limit theta bleed</li>
              <li><strong>Vol Spread:</strong> Positive = earning vol premium, Negative = paying for gamma insurance</li>
              <li><strong>Breakeven Vol:</strong> Minimum realized vol needed to cover theta decay through gamma gains</li>
            </ul>
          </div>
        </>
      )}
    </div>
  )
}