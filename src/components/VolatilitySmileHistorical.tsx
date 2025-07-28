import { useState, useEffect } from 'react'
import { useTheme } from '../contexts/ThemeContext'
import { bloombergAPI, STANDARD_TENORS } from '../api/bloomberg'
import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions
} from 'chart.js'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
)

// Major FX pairs for volatility trading
const CURRENCY_PAIRS = [
  'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD',
  'EURGBP', 'EURJPY', 'EURCHF', 'EURAUD', 'EURCAD', 'EURNZD',
  'GBPJPY', 'GBPCHF', 'GBPAUD', 'GBPCAD', 'GBPNZD',
  'AUDJPY', 'CADJPY', 'NZDJPY', 'CHFJPY',
  'AUDCAD', 'AUDCHF', 'AUDNZD', 'CADCHF', 'NZDCAD', 'NZDCHF'
]

interface SmileData {
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

export function VolatilitySmileHistorical() {
  const { currentTheme } = useTheme()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedCurrency, setSelectedCurrency] = useState('EURUSD')
  const [selectedTenor, setSelectedTenor] = useState('1M')
  const [dayRange, setDayRange] = useState(30)
  const [smileData, setSmileData] = useState<SmileData[]>([])
  
  useEffect(() => {
    loadHistoricalSmile()
  }, [selectedCurrency, selectedTenor, dayRange])
  
  const loadHistoricalSmile = async () => {
    setLoading(true)
    setError(null)
    
    try {
      // Calculate date range
      const endDate = new Date()
      const startDate = new Date()
      startDate.setDate(endDate.getDate() - dayRange)
      
      const startStr = startDate.toISOString().split('T')[0].replace(/-/g, '')
      const endStr = endDate.toISOString().split('T')[0].replace(/-/g, '')
      
      console.log(`Fetching smile data for ${selectedCurrency} ${selectedTenor} from ${startStr} to ${endStr}`)
      
      // Fetch all smile components
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
      const dataByDate = new Map<string, SmileData>()
      
      responses.forEach(({ security, result, error }) => {
        if (!error && result?.success && result.data?.data) {
          result.data.data.forEach((point: any) => {
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
            if (security.includes(`V${selectedTenor}`)) {
              data.atm = value
            } else {
              const match = security.match(new RegExp(`${selectedCurrency}(\\d+)(R|B)${selectedTenor}`))
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
      
      // Convert to array and sort by date
      const sortedData = Array.from(dataByDate.values())
        .sort((a, b) => a.date.localeCompare(b.date))
      
      setSmileData(sortedData)
      console.log(`Loaded ${sortedData.length} days of smile data`)
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load historical smile data')
      console.error('Historical smile error:', err)
    } finally {
      setLoading(false)
    }
  }
  
  // Calculate smile from ATM + RR + BF
  const calculateSmilePoints = (data: SmileData) => {
    if (!data.atm) return null
    
    return {
      '5D Put': data.atm - (data.rr_5d || 0) / 2 + (data.bf_5d || 0),
      '10D Put': data.atm - (data.rr_10d || 0) / 2 + (data.bf_10d || 0),
      '15D Put': data.atm - (data.rr_15d || 0) / 2 + (data.bf_15d || 0),
      '25D Put': data.atm - (data.rr_25d || 0) / 2 + (data.bf_25d || 0),
      '35D Put': data.atm - (data.rr_35d || 0) / 2 + (data.bf_35d || 0),
      'ATM': data.atm,
      '35D Call': data.atm + (data.rr_35d || 0) / 2 + (data.bf_35d || 0),
      '25D Call': data.atm + (data.rr_25d || 0) / 2 + (data.bf_25d || 0),
      '15D Call': data.atm + (data.rr_15d || 0) / 2 + (data.bf_15d || 0),
      '10D Call': data.atm + (data.rr_10d || 0) / 2 + (data.bf_10d || 0),
      '5D Call': data.atm + (data.rr_5d || 0) / 2 + (data.bf_5d || 0)
    }
  }
  
  // Prepare chart data
  const chartData = {
    labels: ['5D Put', '10D Put', '15D Put', '25D Put', '35D Put', 'ATM', '35D Call', '25D Call', '15D Call', '10D Call', '5D Call'],
    datasets: smileData.slice(-5).map((dayData, index) => {
      const smilePoints = calculateSmilePoints(dayData)
      const opacity = 0.3 + (index * 0.15) // Fade older dates
      
      return {
        label: dayData.date,
        data: smilePoints ? Object.values(smilePoints) : [],
        borderColor: index === smileData.slice(-5).length - 1 
          ? currentTheme.primary 
          : `rgba(128, 128, 128, ${opacity})`,
        backgroundColor: 'transparent',
        borderWidth: index === smileData.slice(-5).length - 1 ? 3 : 1,
        tension: 0.4,
        pointRadius: index === smileData.slice(-5).length - 1 ? 4 : 2
      }
    })
  }
  
  const chartOptions: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          color: currentTheme.text,
          font: { size: 11 }
        }
      },
      title: {
        display: true,
        text: `${selectedCurrency} ${selectedTenor} Volatility Smile - Last ${dayRange} Days`,
        color: currentTheme.text,
        font: { size: 14, weight: '600' }
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: currentTheme.surface,
        titleColor: currentTheme.text,
        bodyColor: currentTheme.textSecondary,
        borderColor: currentTheme.border,
        borderWidth: 1
      }
    },
    scales: {
      y: {
        title: {
          display: true,
          text: 'Implied Volatility (%)',
          color: currentTheme.textSecondary
        },
        grid: {
          color: currentTheme.border,
          drawBorder: false
        },
        ticks: {
          color: currentTheme.textSecondary
        }
      },
      x: {
        grid: {
          color: currentTheme.border,
          drawBorder: false
        },
        ticks: {
          color: currentTheme.textSecondary
        }
      }
    }
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
            Fetching historical smile data
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
            Historical Volatility Smile Analysis
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
              onClick={loadHistoricalSmile}
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
      
      <div style={{ padding: '20px', height: '500px' }}>
        {error ? (
          <div style={{
            color: currentTheme.danger,
            textAlign: 'center',
            padding: '40px'
          }}>
            {error}
          </div>
        ) : smileData.length > 0 ? (
          <Line data={chartData} options={chartOptions} />
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