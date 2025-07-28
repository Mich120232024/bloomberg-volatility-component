import { useState, useEffect } from 'react'
import { useTheme } from '../contexts/ThemeContext'
import { bloombergAPI, STANDARD_TENORS } from '../api/bloomberg'

// Major FX pairs for volatility trading
const CURRENCY_PAIRS = [
  'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD',
  'EURGBP', 'EURJPY', 'EURCHF', 'EURAUD', 'EURCAD', 'EURNZD',
  'GBPJPY', 'GBPCHF', 'GBPAUD', 'GBPCAD', 'GBPNZD',
  'AUDJPY', 'CADJPY', 'NZDJPY', 'CHFJPY',
  'AUDCAD', 'AUDCHF', 'AUDNZD', 'CADCHF', 'NZDCAD', 'NZDCHF'
]

interface HistoricalVolData {
  date: string
  atm: number | null
  rr_5d: number | null
  rr_10d: number | null
  rr_15d: number | null
  rr_25d: number | null
  rr_35d: number | null
  bf_5d: number | null
  bf_10d: number | null
  bf_15d: number | null
  bf_25d: number | null
  bf_35d: number | null
}

export function VolatilityHistoricalTable() {
  const { currentTheme } = useTheme()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedCurrency, setSelectedCurrency] = useState('EURUSD')
  const [selectedTenor, setSelectedTenor] = useState('1M')
  const [dayRange, setDayRange] = useState(30)
  const [historicalData, setHistoricalData] = useState<HistoricalVolData[]>([])
  
  useEffect(() => {
    loadHistoricalData()
  }, [selectedCurrency, selectedTenor, dayRange])
  
  const loadHistoricalData = async () => {
    setLoading(true)
    setError(null)
    
    try {
      // Calculate date range
      const endDate = new Date()
      const startDate = new Date()
      startDate.setDate(endDate.getDate() - dayRange)
      
      const startStr = startDate.toISOString().split('T')[0].replace(/-/g, '')
      const endStr = endDate.toISOString().split('T')[0].replace(/-/g, '')
      
      console.log(`Fetching historical data for ${selectedCurrency} ${selectedTenor} from ${startStr} to ${endStr}`)
      
      // Fetch all volatility components for the tenor
      const securities = [
        // ATM Volatility
        selectedTenor === 'ON' 
          ? `${selectedCurrency}V${selectedTenor} Curncy` 
          : `${selectedCurrency}V${selectedTenor} BGN Curncy`,
        // Risk Reversals
        `${selectedCurrency}5R${selectedTenor} BGN Curncy`,
        `${selectedCurrency}10R${selectedTenor} BGN Curncy`,
        `${selectedCurrency}15R${selectedTenor} BGN Curncy`,
        `${selectedCurrency}25R${selectedTenor} BGN Curncy`,
        `${selectedCurrency}35R${selectedTenor} BGN Curncy`,
        // Butterflies
        `${selectedCurrency}5B${selectedTenor} BGN Curncy`,
        `${selectedCurrency}10B${selectedTenor} BGN Curncy`,
        `${selectedCurrency}15B${selectedTenor} BGN Curncy`,
        `${selectedCurrency}25B${selectedTenor} BGN Curncy`,
        `${selectedCurrency}35B${selectedTenor} BGN Curncy`
      ]
      
      // Fetch historical data for each security
      const promises = securities.map(security => 
        bloombergAPI.getHistoricalData(security, ['PX_LAST'], startStr, endStr)
          .then(result => ({ security, result }))
          .catch(err => ({ security, error: err }))
      )
      
      const responses = await Promise.all(promises)
      
      // Process and combine data by date
      const dataByDate = new Map<string, HistoricalVolData>()
      
      responses.forEach((response: any) => {
        if (!response.error && response.result?.success && response.result.data?.data) {
          response.result.data.data?.forEach((point: any) => {
            const dateStr = point.date
            if (!dataByDate.has(dateStr)) {
              dataByDate.set(dateStr, {
                date: dateStr,
                atm: null,
                rr_5d: null, rr_10d: null, rr_15d: null, rr_25d: null, rr_35d: null,
                bf_5d: null, bf_10d: null, bf_15d: null, bf_25d: null, bf_35d: null
              })
            }
            
            const data = dataByDate.get(dateStr)!
            const value = point.PX_LAST
            
            // Parse security type and delta
            if (response.security.includes(`V${selectedTenor}`)) {
              data.atm = value
            } else {
              const match = response.security.match(new RegExp(`${selectedCurrency}(\\d+)(R|B)${selectedTenor}`))
              if (match) {
                const delta = match[1]
                const type = match[2]
                
                if (type === 'R') {
                  switch(delta) {
                    case '5': data.rr_5d = value; break
                    case '10': data.rr_10d = value; break
                    case '15': data.rr_15d = value; break
                    case '25': data.rr_25d = value; break
                    case '35': data.rr_35d = value; break
                  }
                } else if (type === 'B') {
                  switch(delta) {
                    case '5': data.bf_5d = value; break
                    case '10': data.bf_10d = value; break
                    case '15': data.bf_15d = value; break
                    case '25': data.bf_25d = value; break
                    case '35': data.bf_35d = value; break
                  }
                }
              }
            }
          })
        }
      })
      
      // Convert to array and sort by date (most recent first)
      const sortedData = Array.from(dataByDate.values())
        .sort((a, b) => b.date.localeCompare(a.date))
      
      setHistoricalData(sortedData)
      console.log(`Loaded ${sortedData.length} days of historical data`)
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load historical data')
      console.error('Historical data error:', err)
    } finally {
      setLoading(false)
    }
  }
  
  const formatValue = (value: number | null, isRR: boolean = false): string => {
    if (value === null) return '-'
    const formatted = value.toFixed(3)
    return isRR && value !== 0 ? (value > 0 ? `+${formatted}` : formatted) : formatted
  }
  
  const getCellColor = (value: number | null, isRR: boolean = false): string => {
    if (value === null) return currentTheme.textTertiary
    if (isRR) {
      return value > 0 ? currentTheme.success : value < 0 ? currentTheme.danger : currentTheme.text
    }
    return currentTheme.text
  }
  
  const formatDate = (dateStr: string): string => {
    // Convert YYYY-MM-DD to more readable format
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  }
  
  if (loading) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '600px',
        color: currentTheme.primary
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '24px', marginBottom: '8px' }}>Loading...</div>
          <div style={{ fontSize: '12px', color: currentTheme.textSecondary }}>
            Fetching historical volatility data
          </div>
        </div>
      </div>
    )
  }
  
  return (
    <div style={{
      backgroundColor: currentTheme.surface,
      borderRadius: '8px',
      border: `1px solid ${currentTheme.border}`,
      overflow: 'hidden'
    }}>
      <div style={{
        padding: '16px',
        borderBottom: `1px solid ${currentTheme.border}`,
        backgroundColor: currentTheme.background
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '8px'
        }}>
          <h2 style={{ 
            margin: 0, 
            fontSize: '14px', 
            fontWeight: '600',
            color: currentTheme.text
          }}>
            Historical Volatility - {selectedCurrency} {selectedTenor}
          </h2>
          
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <select
              value={selectedCurrency}
              onChange={(e) => setSelectedCurrency(e.target.value)}
              style={{
                backgroundColor: currentTheme.surface,
                color: currentTheme.text,
                border: `1px solid ${currentTheme.border}`,
                borderRadius: '4px',
                padding: '6px 8px',
                fontSize: '12px',
                fontWeight: '500',
                cursor: 'pointer',
                outline: 'none'
              }}
            >
              {CURRENCY_PAIRS.map(pair => (
                <option key={pair} value={pair}>{pair}</option>
              ))}
            </select>
            
            <select
              value={selectedTenor}
              onChange={(e) => setSelectedTenor(e.target.value)}
              style={{
                backgroundColor: currentTheme.surface,
                color: currentTheme.text,
                border: `1px solid ${currentTheme.border}`,
                borderRadius: '4px',
                padding: '6px 8px',
                fontSize: '12px',
                fontWeight: '500',
                cursor: 'pointer',
                outline: 'none'
              }}
            >
              {STANDARD_TENORS.map(tenor => (
                <option key={tenor} value={tenor}>{tenor}</option>
              ))}
            </select>
            
            <select
              value={dayRange}
              onChange={(e) => setDayRange(Number(e.target.value))}
              style={{
                backgroundColor: currentTheme.surface,
                color: currentTheme.text,
                border: `1px solid ${currentTheme.border}`,
                borderRadius: '4px',
                padding: '6px 8px',
                fontSize: '12px',
                fontWeight: '500',
                cursor: 'pointer',
                outline: 'none'
              }}
            >
              <option value={7}>Last 7 days</option>
              <option value={30}>Last 30 days</option>
              <option value={60}>Last 60 days</option>
              <option value={90}>Last 90 days</option>
              <option value={180}>Last 180 days</option>
              <option value={365}>Last 1 year</option>
              <option value={730}>Last 2 years</option>
            </select>
            
            <button
              onClick={loadHistoricalData}
              disabled={loading}
              style={{
                backgroundColor: currentTheme.primary,
                color: currentTheme.background,
                border: 'none',
                borderRadius: '4px',
                padding: '6px 12px',
                fontSize: '11px',
                fontWeight: '500',
                cursor: loading ? 'not-allowed' : 'pointer',
                opacity: loading ? 0.6 : 1
              }}
            >
              {loading ? 'Loading...' : 'Refresh'}
            </button>
          </div>
        </div>
      </div>
      
      <div style={{ overflowX: 'auto', maxHeight: '600px', overflowY: 'auto' }}>
        {error ? (
          <div style={{
            color: currentTheme.danger,
            textAlign: 'center',
            padding: '40px'
          }}>
            {error}
          </div>
        ) : historicalData.length > 0 ? (
          <table style={{
            width: '100%',
            borderCollapse: 'collapse',
            fontSize: '11px',
            fontFamily: 'monospace'
          }}>
            <thead style={{ position: 'sticky', top: 0, zIndex: 10 }}>
              <tr>
                <th rowSpan={2} style={{
                  backgroundColor: currentTheme.primary,
                  color: currentTheme.background,
                  padding: '12px',
                  textAlign: 'left',
                  fontWeight: '600',
                  position: 'sticky',
                  left: 0,
                  zIndex: 11
                }}>
                  Date
                </th>
                <th style={{
                  backgroundColor: currentTheme.surfaceAlt,
                  color: currentTheme.text,
                  padding: '8px',
                  textAlign: 'center',
                  borderBottom: `1px solid ${currentTheme.border}`
                }}>
                  ATM
                </th>
                {['5D', '10D', '15D', '25D', '35D'].map(delta => (
                  <th key={delta} colSpan={2} style={{
                    backgroundColor: currentTheme.surfaceAlt,
                    color: currentTheme.text,
                    padding: '8px',
                    textAlign: 'center',
                    borderBottom: `1px solid ${currentTheme.border}`
                  }}>
                    {delta}
                  </th>
                ))}
              </tr>
              <tr>
                <th style={headerStyle(currentTheme)}>Vol</th>
                {['5D', '10D', '15D', '25D', '35D'].map(delta => (
                  <>
                    <th key={`${delta}-rr`} style={headerStyle(currentTheme)}>RR</th>
                    <th key={`${delta}-bf`} style={headerStyle(currentTheme)}>BF</th>
                  </>
                ))}
              </tr>
            </thead>
            <tbody>
              {historicalData.map((row, index) => (
                <tr key={row.date} style={{
                  backgroundColor: index % 2 === 0 ? currentTheme.surface : currentTheme.background
                }}>
                  <td style={{
                    backgroundColor: currentTheme.primary,
                    color: currentTheme.background,
                    padding: '8px',
                    fontWeight: '500',
                    position: 'sticky',
                    left: 0,
                    zIndex: 1
                  }}>
                    {formatDate(row.date)}
                  </td>
                  <td style={cellStyle(currentTheme, '#E6D690')}>{formatValue(row.atm)}</td>
                  <td style={cellStyle(currentTheme, getCellColor(row.rr_5d, true))}>{formatValue(row.rr_5d, true)}</td>
                  <td style={cellStyle(currentTheme)}>{formatValue(row.bf_5d)}</td>
                  <td style={cellStyle(currentTheme, getCellColor(row.rr_10d, true))}>{formatValue(row.rr_10d, true)}</td>
                  <td style={cellStyle(currentTheme)}>{formatValue(row.bf_10d)}</td>
                  <td style={cellStyle(currentTheme, getCellColor(row.rr_15d, true))}>{formatValue(row.rr_15d, true)}</td>
                  <td style={cellStyle(currentTheme)}>{formatValue(row.bf_15d)}</td>
                  <td style={cellStyle(currentTheme, getCellColor(row.rr_25d, true))}>{formatValue(row.rr_25d, true)}</td>
                  <td style={cellStyle(currentTheme)}>{formatValue(row.bf_25d)}</td>
                  <td style={cellStyle(currentTheme, getCellColor(row.rr_35d, true))}>{formatValue(row.rr_35d, true)}</td>
                  <td style={cellStyle(currentTheme)}>{formatValue(row.bf_35d)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div style={{
            color: currentTheme.textSecondary,
            textAlign: 'center',
            padding: '40px'
          }}>
            No data available for the selected period
          </div>
        )}
      </div>
    </div>
  )
}

const headerStyle = (theme: any) => ({
  backgroundColor: theme.surfaceAlt,
  color: theme.textSecondary,
  padding: '6px',
  textAlign: 'center' as const,
  fontWeight: '500',
  fontSize: '10px',
  borderBottom: `2px solid ${theme.border}`,
  position: 'sticky' as const,
  top: '37px',
  zIndex: 9
})

const cellStyle = (theme: any, color?: string) => ({
  padding: '6px 4px',
  textAlign: 'right' as const,
  borderRight: `1px solid ${theme.border}`,
  color: color || theme.text,
  fontSize: '10px'
})