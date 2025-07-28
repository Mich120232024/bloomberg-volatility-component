import { useState, useEffect } from 'react'
import { useTheme } from '../contexts/ThemeContext'

// Direct API call without the bloomberg client to isolate issues
async function fetchDirectly(endpoint: string, body: any) {
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

export function TradingAnalyticsWorking() {
  const { currentTheme } = useTheme()
  const [data, setData] = useState<any>({})
  const [status, setStatus] = useState('Starting...')
  
  useEffect(() => {
    async function loadData() {
      setStatus('Fetching spot rates...')
      
      try {
        // Fetch spot rates
        const spotResult = await fetchDirectly('/api/bloomberg/reference', {
          securities: ['EURUSD Curncy', 'GBPUSD Curncy', 'USDJPY Curncy'],
          fields: ['PX_LAST']
        })
        
        setData(prev => ({ ...prev, spot: spotResult }))
        setStatus('Fetching volatility data...')
        
        // Fetch volatility for EURUSD 1M
        const volResult = await fetchDirectly('/api/bloomberg/reference', {
          securities: [
            'EURUSDV1M BGN Curncy',  // ATM
            'EURUSD25R1M BGN Curncy', // 25D RR
            'EURUSD25B1M BGN Curncy'  // 25D BF
          ],
          fields: ['PX_LAST', 'PX_BID', 'PX_ASK']
        })
        
        setData(prev => ({ ...prev, vol: volResult }))
        setStatus('Data loaded!')
        
      } catch (err) {
        setStatus(`Error: ${err}`)
        console.error('Direct fetch error:', err)
      }
    }
    
    loadData()
  }, [])
  
  // Extract values for display
  const getSpotRate = (pair: string) => {
    const sec = data.spot?.data?.securities_data?.find((s: any) => 
      s.security.startsWith(pair)
    )
    return sec?.fields?.PX_LAST || 'N/A'
  }
  
  const getVolData = () => {
    if (!data.vol?.data?.securities_data) return null
    
    const atm = data.vol.data.securities_data.find((s: any) => s.security.includes('V1M'))
    const rr = data.vol.data.securities_data.find((s: any) => s.security.includes('25R1M'))
    const bf = data.vol.data.securities_data.find((s: any) => s.security.includes('25B1M'))
    
    return {
      atm: atm?.fields?.PX_LAST || 'N/A',
      rr: rr?.fields?.PX_LAST || 'N/A',
      bf: bf?.fields?.PX_LAST || 'N/A'
    }
  }
  
  const volData = getVolData()
  
  return (
    <div style={{
      padding: '20px',
      backgroundColor: currentTheme.background
    }}>
      <h2 style={{ color: currentTheme.text, marginBottom: '20px' }}>
        Trading Analytics (Working Version)
      </h2>
      
      <div style={{
        padding: '16px',
        backgroundColor: currentTheme.surface,
        borderRadius: '8px',
        marginBottom: '16px'
      }}>
        <div style={{ color: currentTheme.textSecondary, marginBottom: '8px' }}>
          Status: {status}
        </div>
      </div>
      
      {/* Spot Rates */}
      <div style={{
        padding: '16px',
        backgroundColor: currentTheme.surface,
        borderRadius: '8px',
        marginBottom: '16px'
      }}>
        <h3 style={{ color: currentTheme.text, marginBottom: '12px' }}>Spot Rates</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
          <div>
            <div style={{ color: currentTheme.textSecondary, fontSize: '12px' }}>EURUSD</div>
            <div style={{ color: currentTheme.text, fontSize: '18px', fontWeight: '600' }}>
              {getSpotRate('EURUSD')}
            </div>
          </div>
          <div>
            <div style={{ color: currentTheme.textSecondary, fontSize: '12px' }}>GBPUSD</div>
            <div style={{ color: currentTheme.text, fontSize: '18px', fontWeight: '600' }}>
              {getSpotRate('GBPUSD')}
            </div>
          </div>
          <div>
            <div style={{ color: currentTheme.textSecondary, fontSize: '12px' }}>USDJPY</div>
            <div style={{ color: currentTheme.text, fontSize: '18px', fontWeight: '600' }}>
              {getSpotRate('USDJPY')}
            </div>
          </div>
        </div>
      </div>
      
      {/* EURUSD Volatility */}
      {volData && (
        <div style={{
          padding: '16px',
          backgroundColor: currentTheme.surface,
          borderRadius: '8px',
          marginBottom: '16px'
        }}>
          <h3 style={{ color: currentTheme.text, marginBottom: '12px' }}>
            EURUSD 1M Volatility
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
            <div>
              <div style={{ color: currentTheme.textSecondary, fontSize: '12px' }}>ATM Vol</div>
              <div style={{ color: currentTheme.text, fontSize: '18px', fontWeight: '600' }}>
                {volData.atm}%
              </div>
            </div>
            <div>
              <div style={{ color: currentTheme.textSecondary, fontSize: '12px' }}>25D RR</div>
              <div style={{ 
                color: Number(volData.rr) > 0 ? currentTheme.success : currentTheme.danger, 
                fontSize: '18px', 
                fontWeight: '600' 
              }}>
                {Number(volData.rr) > 0 ? '+' : ''}{volData.rr}
              </div>
            </div>
            <div>
              <div style={{ color: currentTheme.textSecondary, fontSize: '12px' }}>25D BF</div>
              <div style={{ color: currentTheme.text, fontSize: '18px', fontWeight: '600' }}>
                {volData.bf}
              </div>
            </div>
          </div>
          
          {/* Simple Signal */}
          <div style={{
            marginTop: '16px',
            padding: '12px',
            backgroundColor: currentTheme.background,
            borderRadius: '4px'
          }}>
            <div style={{ color: currentTheme.text, fontSize: '14px', fontWeight: '600' }}>
              Market Signal
            </div>
            <div style={{ color: currentTheme.textSecondary, fontSize: '13px', marginTop: '4px' }}>
              {Number(volData.rr) > 0.5 ? 
                '📈 Call skew detected - Market favoring upside' :
                Number(volData.rr) < -0.5 ?
                '📉 Put skew detected - Market favoring downside' :
                '➡️ Neutral skew - Balanced market'
              }
            </div>
          </div>
        </div>
      )}
      
      {/* Raw Data Display */}
      <details style={{ marginTop: '16px' }}>
        <summary style={{ cursor: 'pointer', color: currentTheme.textSecondary }}>
          View Raw Data
        </summary>
        <pre style={{ 
          marginTop: '8px',
          padding: '12px',
          backgroundColor: currentTheme.surface,
          borderRadius: '4px',
          fontSize: '11px',
          color: currentTheme.text,
          overflow: 'auto'
        }}>
          {JSON.stringify(data, null, 2)}
        </pre>
      </details>
    </div>
  )
}