import { useState, useEffect, useCallback } from 'react'
import { useTheme } from '../contexts/ThemeContext'
import { bloombergAPI, VolatilityData } from '../api/bloomberg'

export function SmileDebugComponent() {
  const { currentTheme } = useTheme()
  const [loading, setLoading] = useState(false)
  const [selectedPair, setSelectedPair] = useState('EURUSD')
  const [selectedTenor, setSelectedTenor] = useState('1M')
  const [rawData, setRawData] = useState<VolatilityData | null>(null)
  const [calculations, setCalculations] = useState<any>(null)
  
  const currencyPairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD']
  const tenors = ['ON', '1W', '2W', '1M', '2M', '3M', '6M', '9M', '1Y', '18M']

  const fetchData = useCallback(async () => {
    setLoading(true)
    
    try {
      const data = await bloombergAPI.getVolatilitySurface(selectedPair, [selectedTenor])
      const tenorData = data[0]
      setRawData(tenorData)
      
      if (tenorData) {
        // Calculate smile points
        const atmBid = tenorData.atm_bid
        const atmAsk = tenorData.atm_ask
        const atmMid = atmBid && atmAsk ? (atmBid + atmAsk) / 2 : null
        
        const calculations: any = {
          atm: { bid: atmBid, ask: atmAsk, mid: atmMid },
          deltas: {}
        }
        
        // For each delta
        const deltas = [
          { delta: 25, rrBid: tenorData.rr_25d_bid, rrAsk: tenorData.rr_25d_ask, bfBid: tenorData.bf_25d_bid, bfAsk: tenorData.bf_25d_ask },
          { delta: 10, rrBid: tenorData.rr_10d_bid, rrAsk: tenorData.rr_10d_ask, bfBid: tenorData.bf_10d_bid, bfAsk: tenorData.bf_10d_ask }
        ]
        
        deltas.forEach(({ delta, rrBid, rrAsk, bfBid, bfAsk }) => {
          if (rrBid !== null && rrAsk !== null && bfBid !== null && bfAsk !== null && atmMid) {
            const rrMid = (rrBid + rrAsk) / 2
            const bfMid = (bfBid + bfAsk) / 2
            
            // Bloomberg formulas: RR = vol(call) - vol(put), BF = (vol(call) + vol(put))/2 - ATM
            const putVol = atmMid - rrMid/2 + bfMid
            const callVol = atmMid + rrMid/2 + bfMid
            
            calculations.deltas[delta] = {
              rr: { bid: rrBid, ask: rrAsk, mid: rrMid },
              bf: { bid: bfBid, ask: bfAsk, mid: bfMid },
              putVol,
              callVol,
              isProperSmile: putVol > atmMid && callVol > atmMid
            }
          }
        })
        
        setCalculations(calculations)
        
        // Console log for debugging
        console.log('=== SMILE DEBUG ===')
        console.log('Raw Bloomberg Data:', tenorData)
        console.log('Calculated Smile:', calculations)
      }
      
    } catch (err) {
      console.error('Data fetch error:', err)
    } finally {
      setLoading(false)
    }
  }, [selectedPair, selectedTenor])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  return (
    <div style={{
      backgroundColor: currentTheme.background,
      color: currentTheme.text,
      padding: '20px',
      height: '100%',
      overflow: 'auto'
    }}>
      <h2 style={{ marginBottom: '20px', color: currentTheme.text }}>
        Bloomberg Volatility Smile Debug - {selectedPair} {selectedTenor}
      </h2>
      
      {/* Controls */}
      <div style={{ 
        display: 'flex', 
        gap: '16px', 
        marginBottom: '20px',
        padding: '16px',
        backgroundColor: currentTheme.surface,
        borderRadius: '8px',
        border: `1px solid ${currentTheme.border}`
      }}>
        <div>
          <label style={{ fontSize: '12px', color: currentTheme.textSecondary, marginRight: '8px' }}>
            Currency Pair:
          </label>
          <select
            value={selectedPair}
            onChange={(e) => setSelectedPair(e.target.value)}
            style={{
              backgroundColor: currentTheme.background,
              color: currentTheme.text,
              border: `1px solid ${currentTheme.border}`,
              borderRadius: '4px',
              padding: '4px 8px',
              fontSize: '12px'
            }}
          >
            {currencyPairs.map(pair => (
              <option key={pair} value={pair}>{pair}</option>
            ))}
          </select>
        </div>
        
        <div>
          <label style={{ fontSize: '12px', color: currentTheme.textSecondary, marginRight: '8px' }}>
            Tenor:
          </label>
          <select
            value={selectedTenor}
            onChange={(e) => setSelectedTenor(e.target.value)}
            style={{
              backgroundColor: currentTheme.background,
              color: currentTheme.text,
              border: `1px solid ${currentTheme.border}`,
              borderRadius: '4px',
              padding: '4px 8px',
              fontSize: '12px'
            }}
          >
            {tenors.map(tenor => (
              <option key={tenor} value={tenor}>{tenor}</option>
            ))}
          </select>
        </div>
        
        <button
          onClick={fetchData}
          disabled={loading}
          style={{
            backgroundColor: currentTheme.primary,
            color: currentTheme.background,
            border: 'none',
            borderRadius: '4px',
            padding: '6px 12px',
            fontSize: '12px',
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading ? 0.7 : 1
          }}
        >
          {loading ? 'Loading...' : 'Refresh'}
        </button>
      </div>

      {/* Raw Data Display */}
      {rawData && (
        <div style={{ 
          marginBottom: '20px',
          padding: '16px',
          backgroundColor: currentTheme.surface,
          borderRadius: '8px',
          border: `1px solid ${currentTheme.border}`
        }}>
          <h3 style={{ marginBottom: '12px', color: currentTheme.text }}>Raw Bloomberg Data</h3>
          <div style={{ 
            fontFamily: 'monospace', 
            fontSize: '11px',
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: '8px'
          }}>
            <div>
              <strong>ATM:</strong><br/>
              Bid: {rawData.atm_bid?.toFixed(3) || 'null'}<br/>
              Ask: {rawData.atm_ask?.toFixed(3) || 'null'}
            </div>
            <div>
              <strong>25D RR:</strong><br/>
              Bid: {rawData.rr_25d_bid?.toFixed(3) || 'null'}<br/>
              Ask: {rawData.rr_25d_ask?.toFixed(3) || 'null'}
            </div>
            <div>
              <strong>25D BF:</strong><br/>
              Bid: {rawData.bf_25d_bid?.toFixed(3) || 'null'}<br/>
              Ask: {rawData.bf_25d_ask?.toFixed(3) || 'null'}
            </div>
            <div>
              <strong>10D RR:</strong><br/>
              Bid: {rawData.rr_10d_bid?.toFixed(3) || 'null'}<br/>
              Ask: {rawData.rr_10d_ask?.toFixed(3) || 'null'}
            </div>
          </div>
        </div>
      )}

      {/* Calculated Smile */}
      {calculations && (
        <div style={{ 
          padding: '16px',
          backgroundColor: currentTheme.surface,
          borderRadius: '8px',
          border: `1px solid ${currentTheme.border}`
        }}>
          <h3 style={{ marginBottom: '12px', color: currentTheme.text }}>Calculated Smile Points</h3>
          
          <div style={{ marginBottom: '16px' }}>
            <strong>ATM (50Δ):</strong> {calculations.atm.mid?.toFixed(3) || 'N/A'}%
          </div>
          
          {Object.entries(calculations.deltas).map(([delta, data]: [string, any]) => (
            <div key={delta} style={{ 
              marginBottom: '12px',
              padding: '12px',
              backgroundColor: currentTheme.background,
              borderRadius: '4px',
              border: data.isProperSmile ? `1px solid ${currentTheme.success}` : `1px solid ${currentTheme.danger}`
            }}>
              <div style={{ 
                fontWeight: '600', 
                marginBottom: '8px',
                color: data.isProperSmile ? currentTheme.success : currentTheme.danger
              }}>
                {delta}Δ Points {data.isProperSmile ? '✓ Valid Smile' : '✗ Invalid Shape'}
              </div>
              
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px', fontSize: '12px' }}>
                <div>
                  <strong>Put Vol ({delta}Δ):</strong> {data.putVol.toFixed(3)}%<br/>
                  <small>Formula: ATM - RR/2 + BF = {calculations.atm.mid?.toFixed(3)} - {data.rr.mid.toFixed(3)}/2 + {data.bf.mid.toFixed(3)}</small>
                </div>
                <div>
                  <strong>Call Vol ({100-parseInt(delta)}Δ):</strong> {data.callVol.toFixed(3)}%<br/>
                  <small>Formula: ATM + RR/2 + BF = {calculations.atm.mid?.toFixed(3)} + {data.rr.mid.toFixed(3)}/2 + {data.bf.mid.toFixed(3)}</small>
                </div>
              </div>
              
              <div style={{ marginTop: '8px', fontSize: '11px', color: currentTheme.textSecondary }}>
                RR Mid: {data.rr.mid.toFixed(3)} | BF Mid: {data.bf.mid.toFixed(3)}
              </div>
            </div>
          ))}
          
          {/* Analysis */}
          <div style={{ 
            marginTop: '16px',
            padding: '12px',
            backgroundColor: currentTheme.background,
            borderRadius: '4px',
            fontSize: '12px'
          }}>
            <strong>Analysis:</strong><br/>
            • A proper volatility smile should have higher volatility on the wings (puts/calls) than ATM<br/>
            • Risk Reversal (RR) = Call Vol - Put Vol (market skew)<br/>
            • Butterfly (BF) = (Call Vol + Put Vol)/2 - ATM Vol (smile curvature)<br/>
            • Check the console for detailed logging
          </div>
        </div>
      )}
    </div>
  )
}