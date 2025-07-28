import { useState, useEffect, useCallback } from 'react'
import { useTheme } from '../contexts/ThemeContext'
import { bloombergAPI, VolatilityData } from '../api/bloomberg'

// Individual Section Components
import { VolatilitySmileSection } from './VolatilitySmileSection'
import { TermStructureSection } from './TermStructureSection' 
import { VolatilitySurfaceSection } from './VolatilitySurfaceSection'
import { MetricsAnalyticsSection } from './MetricsAnalyticsSection'

export function VolatilityDashboard() {
  const { currentTheme } = useTheme()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedPair, setSelectedPair] = useState('EURUSD')
  const [selectedTenor, setSelectedTenor] = useState('1M')
  const [surfaceData, setSurfaceData] = useState<VolatilityData[]>([])
  const [currentData, setCurrentData] = useState<VolatilityData | null>(null)
  
  const currencyPairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD']
  const tenors = ['ON', '1W', '2W', '1M', '2M', '3M', '6M', '9M', '1Y', '18M']

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)
    
    try {
      // Fetch full surface data for all tenors
      const allData = await bloombergAPI.getVolatilitySurface(selectedPair, tenors)
      setSurfaceData(allData)
      
      // Find current tenor data
      const tenorIndex = tenors.indexOf(selectedTenor)
      if (tenorIndex >= 0 && allData[tenorIndex]) {
        setCurrentData(allData[tenorIndex])
      }
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch data')
    } finally {
      setLoading(false)
    }
  }, [selectedPair, selectedTenor])

  useEffect(() => {
    fetchData()
  }, [selectedPair, selectedTenor, fetchData])

  return (
    <div style={{
      backgroundColor: currentTheme.background,
      minHeight: '100vh',
      color: currentTheme.text
    }}>
      {/* Header Controls */}
      <div style={{
        backgroundColor: currentTheme.surface,
        borderBottom: `1px solid ${currentTheme.border}`,
        padding: '16px 20px',
        display: 'flex',
        gap: '20px',
        alignItems: 'center',
        flexWrap: 'wrap'
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
              padding: '6px 12px',
              fontSize: '14px'
            }}
          >
            {currencyPairs.map(pair => (
              <option key={pair} value={pair}>{pair}</option>
            ))}
          </select>
        </div>
        
        <div>
          <label style={{ fontSize: '12px', color: currentTheme.textSecondary, marginRight: '8px' }}>
            Primary Tenor:
          </label>
          <select
            value={selectedTenor}
            onChange={(e) => setSelectedTenor(e.target.value)}
            style={{
              backgroundColor: currentTheme.background,
              color: currentTheme.text,
              border: `1px solid ${currentTheme.border}`,
              borderRadius: '4px',
              padding: '6px 12px',
              fontSize: '14px'
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
            padding: '8px 16px',
            fontSize: '14px',
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading ? 0.7 : 1
          }}
        >
          {loading ? 'Loading...' : 'Refresh'}
        </button>
        
        <div style={{ 
          marginLeft: 'auto',
          display: 'flex',
          gap: '16px',
          fontSize: '12px',
          color: currentTheme.textSecondary 
        }}>
          <span>Live Bloomberg Data</span>
          <span>Updated: <strong>{new Date().toLocaleTimeString()}</strong></span>
        </div>
      </div>

      {error && (
        <div style={{
          padding: '16px 20px',
          backgroundColor: currentTheme.danger + '20',
          borderBottom: `1px solid ${currentTheme.danger}40`,
          color: currentTheme.danger,
          fontSize: '14px'
        }}>
          Error: {error}
        </div>
      )}

      {/* 4-Section Dashboard Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gridTemplateRows: '1fr 1fr',
        gap: '2px',
        backgroundColor: currentTheme.border,
        height: 'calc(100vh - 100px)',
        margin: '8px',
        borderRadius: '12px',
        overflow: 'hidden',
        boxShadow: `0 4px 12px ${currentTheme.border}80`
      }}>
        
        {/* Section 1: Volatility Smile with Selectable Tenors */}
        <div style={{
          backgroundColor: currentTheme.background,
          padding: '12px 16px',
          borderTopLeftRadius: '12px',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden'
        }}>
          <VolatilitySmileSection 
            selectedPair={selectedPair}
            selectedTenor={selectedTenor}
            surfaceData={surfaceData}
            tenors={tenors}
            onTenorChange={setSelectedTenor}
            loading={loading}
          />
        </div>
        
        {/* Section 2: Term Structure */}
        <div style={{
          backgroundColor: currentTheme.background,
          padding: '12px 16px',
          borderTopRightRadius: '12px',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden'
        }}>
          <TermStructureSection 
            selectedPair={selectedPair}
            surfaceData={surfaceData}
            selectedTenor={selectedTenor}
            tenors={tenors}
            loading={loading}
          />
        </div>
        
        {/* Section 3: Full Volatility Surface */}
        <div style={{
          backgroundColor: currentTheme.background,
          padding: '12px 16px',
          borderBottomLeftRadius: '12px',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden'
        }}>
          <VolatilitySurfaceSection 
            selectedPair={selectedPair}
            surfaceData={surfaceData}
            tenors={tenors}
            loading={loading}
          />
        </div>
        
        {/* Section 4: Key Metrics & Analytics */}
        <div style={{
          backgroundColor: currentTheme.background,
          padding: '12px 16px',
          borderBottomRightRadius: '12px',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden'
        }}>
          <MetricsAnalyticsSection 
            selectedPair={selectedPair}
            selectedTenor={selectedTenor}
            currentData={currentData}
            surfaceData={surfaceData}
            loading={loading}
          />
        </div>
        
      </div>
    </div>
  )
}