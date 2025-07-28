import { useState, useEffect } from 'react'
import { useTheme } from '../contexts/ThemeContext'

// Direct fetch to avoid client issues
async function fetchData(endpoint: string, body: any) {
  const response = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer test'
    },
    body: JSON.stringify(body)
  })
  return response.json()
}

interface TradingSignal {
  pair: string
  signal: string
  strength: number
  rationale: string
}

export function RealTradingSignals() {
  const { currentTheme } = useTheme()
  const [loading, setLoading] = useState(true)
  const [volData, setVolData] = useState<any>({})
  const [signals, setSignals] = useState<TradingSignal[]>([])
  
  useEffect(() => {
    async function analyzeMarkets() {
      const pairs = ['EURUSD', 'GBPUSD', 'USDJPY']
      const allData: any = {}
      
      for (const pair of pairs) {
        try {
          // Get multiple tenors to see term structure
          const securities = [
            `${pair}V1W BGN Curncy`,   // 1 week ATM
            `${pair}V1M BGN Curncy`,   // 1 month ATM
            `${pair}V3M BGN Curncy`,   // 3 month ATM
            `${pair}25R1M BGN Curncy`, // 1M 25D Risk Reversal
            `${pair}25B1M BGN Curncy`, // 1M 25D Butterfly
            `${pair}10R1M BGN Curncy`, // 1M 10D Risk Reversal
          ]
          
          const result = await fetchData('/api/bloomberg/reference', {
            securities,
            fields: ['PX_LAST', 'PX_BID', 'PX_ASK']
          })
          
          if (result.success) {
            const data: any = {}
            result.data.securities_data.forEach((sec: any) => {
              if (sec.success && sec.fields.PX_LAST !== undefined) {
                if (sec.security.includes('V1W')) data.atm1W = sec.fields.PX_LAST
                if (sec.security.includes('V1M')) data.atm1M = sec.fields.PX_LAST
                if (sec.security.includes('V3M')) data.atm3M = sec.fields.PX_LAST
                if (sec.security.includes('25R1M')) data.rr25 = sec.fields.PX_LAST
                if (sec.security.includes('25B1M')) data.bf25 = sec.fields.PX_LAST
                if (sec.security.includes('10R1M')) data.rr10 = sec.fields.PX_LAST
              }
            })
            allData[pair] = data
          }
        } catch (err) {
          console.error(`Error fetching ${pair}:`, err)
        }
      }
      
      setVolData(allData)
      generateTradingSignals(allData)
      setLoading(false)
    }
    
    analyzeMarkets()
  }, [])
  
  const generateTradingSignals = (data: any) => {
    const newSignals: TradingSignal[] = []
    
    Object.entries(data).forEach(([pair, metrics]: [string, any]) => {
      // 1. Term Structure Signal
      if (metrics.atm1W && metrics.atm1M && metrics.atm3M) {
        const termSlope = metrics.atm3M - metrics.atm1W
        if (metrics.atm1W > metrics.atm1M * 1.2) {
          newSignals.push({
            pair,
            signal: 'EVENT RISK',
            strength: 90,
            rationale: `Short-term vol (${metrics.atm1W.toFixed(1)}%) significantly above 1M (${metrics.atm1M.toFixed(1)}%) - Market pricing near-term event`
          })
        } else if (termSlope > 2) {
          newSignals.push({
            pair,
            signal: 'STEEPENING',
            strength: 70,
            rationale: `Term structure steepening: 3M-1W spread at ${termSlope.toFixed(1)} vols`
          })
        }
      }
      
      // 2. Risk Reversal Signal
      if (metrics.rr25 !== undefined) {
        const rrAbs = Math.abs(metrics.rr25)
        if (rrAbs > 1.0) {
          newSignals.push({
            pair,
            signal: metrics.rr25 > 0 ? 'CALL SKEW' : 'PUT SKEW',
            strength: rrAbs > 1.5 ? 85 : 65,
            rationale: `25D RR at ${metrics.rr25.toFixed(2)} - Strong ${metrics.rr25 > 0 ? 'topside' : 'downside'} demand`
          })
        }
      }
      
      // 3. Butterfly (Tail Risk) Signal
      if (metrics.bf25 !== undefined && metrics.bf25 > 0.5) {
        newSignals.push({
          pair,
          signal: 'TAIL RISK',
          strength: metrics.bf25 > 0.75 ? 80 : 60,
          rationale: `25D Butterfly elevated at ${metrics.bf25.toFixed(2)} - Market pricing fat tails`
        })
      }
      
      // 4. Skew Steepness (10D vs 25D RR)
      if (metrics.rr10 !== undefined && metrics.rr25 !== undefined) {
        const skewRatio = metrics.rr10 / metrics.rr25
        if (Math.abs(skewRatio) > 1.5 && Math.abs(metrics.rr25) > 0.3) {
          newSignals.push({
            pair,
            signal: 'SKEW CONVEXITY',
            strength: 75,
            rationale: `10D/25D RR ratio at ${skewRatio.toFixed(1)}x - Steep skew structure`
          })
        }
      }
    })
    
    // Sort by strength
    setSignals(newSignals.sort((a, b) => b.strength - a.strength))
  }
  
  const getSignalColor = (strength: number) => {
    if (strength >= 80) return currentTheme.danger
    if (strength >= 70) return currentTheme.warning
    if (strength >= 60) return currentTheme.success
    return currentTheme.text
  }
  
  return (
    <div style={{ padding: '20px', backgroundColor: currentTheme.background }}>
      <h2 style={{ color: currentTheme.text, marginBottom: '20px' }}>
        Real-Time FX Volatility Trading Signals
      </h2>
      
      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px', color: currentTheme.textSecondary }}>
          Analyzing volatility surfaces across currency pairs...
        </div>
      ) : (
        <>
          {/* Trading Signals */}
          <div style={{ marginBottom: '24px' }}>
            <h3 style={{ color: currentTheme.text, marginBottom: '16px', fontSize: '16px' }}>
              Active Trading Signals ({signals.length})
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {signals.map((signal, idx) => (
                <div key={idx} style={{
                  backgroundColor: currentTheme.surface,
                  border: `2px solid ${getSignalColor(signal.strength)}40`,
                  borderRadius: '8px',
                  padding: '16px',
                  borderLeft: `6px solid ${getSignalColor(signal.strength)}`
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                        <span style={{ 
                          fontSize: '18px', 
                          fontWeight: '700',
                          color: currentTheme.text 
                        }}>
                          {signal.pair}
                        </span>
                        <span style={{
                          backgroundColor: getSignalColor(signal.strength) + '20',
                          color: getSignalColor(signal.strength),
                          padding: '4px 12px',
                          borderRadius: '4px',
                          fontSize: '13px',
                          fontWeight: '600'
                        }}>
                          {signal.signal}
                        </span>
                      </div>
                      <div style={{ 
                        color: currentTheme.textSecondary,
                        fontSize: '14px'
                      }}>
                        {signal.rationale}
                      </div>
                    </div>
                    <div style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      padding: '8px'
                    }}>
                      <div style={{ 
                        fontSize: '24px',
                        fontWeight: '700',
                        color: getSignalColor(signal.strength)
                      }}>
                        {signal.strength}
                      </div>
                      <div style={{ 
                        fontSize: '10px',
                        color: currentTheme.textSecondary
                      }}>
                        STRENGTH
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          {/* Volatility Matrix */}
          <div>
            <h3 style={{ color: currentTheme.text, marginBottom: '16px', fontSize: '16px' }}>
              Volatility Surface Matrix
            </h3>
            <div style={{
              backgroundColor: currentTheme.surface,
              borderRadius: '8px',
              overflow: 'hidden'
            }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ backgroundColor: currentTheme.surfaceAlt }}>
                    <th style={{ padding: '12px', textAlign: 'left', color: currentTheme.text }}>Pair</th>
                    <th style={{ padding: '12px', textAlign: 'center', color: currentTheme.text }}>1W ATM</th>
                    <th style={{ padding: '12px', textAlign: 'center', color: currentTheme.text }}>1M ATM</th>
                    <th style={{ padding: '12px', textAlign: 'center', color: currentTheme.text }}>3M ATM</th>
                    <th style={{ padding: '12px', textAlign: 'center', color: currentTheme.text }}>Term Slope</th>
                    <th style={{ padding: '12px', textAlign: 'center', color: currentTheme.text }}>25D RR</th>
                    <th style={{ padding: '12px', textAlign: 'center', color: currentTheme.text }}>25D BF</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(volData).map(([pair, data]: [string, any]) => (
                    <tr key={pair} style={{ borderTop: `1px solid ${currentTheme.border}` }}>
                      <td style={{ padding: '12px', fontWeight: '600', color: currentTheme.text }}>{pair}</td>
                      <td style={{ padding: '12px', textAlign: 'center', color: currentTheme.text }}>
                        {data.atm1W?.toFixed(2) || '-'}%
                      </td>
                      <td style={{ padding: '12px', textAlign: 'center', color: currentTheme.text }}>
                        {data.atm1M?.toFixed(2) || '-'}%
                      </td>
                      <td style={{ padding: '12px', textAlign: 'center', color: currentTheme.text }}>
                        {data.atm3M?.toFixed(2) || '-'}%
                      </td>
                      <td style={{ 
                        padding: '12px', 
                        textAlign: 'center',
                        color: data.atm3M > data.atm1W ? currentTheme.success : currentTheme.danger,
                        fontWeight: '600'
                      }}>
                        {data.atm1W && data.atm3M ? (data.atm3M - data.atm1W).toFixed(2) : '-'}
                      </td>
                      <td style={{ 
                        padding: '12px', 
                        textAlign: 'center',
                        color: data.rr25 > 0 ? currentTheme.success : data.rr25 < 0 ? currentTheme.danger : currentTheme.text,
                        fontWeight: '600'
                      }}>
                        {data.rr25 !== undefined ? (data.rr25 > 0 ? '+' : '') + data.rr25.toFixed(2) : '-'}
                      </td>
                      <td style={{ 
                        padding: '12px', 
                        textAlign: 'center',
                        color: data.bf25 > 0.5 ? currentTheme.warning : currentTheme.text
                      }}>
                        {data.bf25?.toFixed(2) || '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          
          {/* Trading Implications */}
          <div style={{
            marginTop: '24px',
            padding: '16px',
            backgroundColor: currentTheme.surface,
            borderRadius: '8px',
            borderLeft: `4px solid ${currentTheme.primary}`
          }}>
            <h4 style={{ color: currentTheme.text, marginBottom: '8px' }}>How to Trade These Signals:</h4>
            <ul style={{ 
              color: currentTheme.textSecondary, 
              fontSize: '13px',
              lineHeight: '1.8',
              paddingLeft: '20px'
            }}>
              <li><strong>EVENT RISK:</strong> Short calendar spreads, long gamma, or avoid trading until event passes</li>
              <li><strong>CALL/PUT SKEW:</strong> Trade risk reversals in direction of skew or fade extreme levels</li>
              <li><strong>TAIL RISK:</strong> Sell butterflies if too expensive, or buy for hedging if cheap</li>
              <li><strong>STEEPENING:</strong> Long calendar spreads to capture term structure normalization</li>
              <li><strong>SKEW CONVEXITY:</strong> Trade 10D vs 25D structures for relative value</li>
            </ul>
          </div>
        </>
      )}
    </div>
  )
}