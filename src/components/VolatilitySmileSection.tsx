import { useState, useMemo } from 'react'
import { useTheme } from '../contexts/ThemeContext'
import { VolatilityData } from '../api/bloomberg'

interface VolatilitySmileSectionProps {
  selectedPair: string
  selectedTenor: string
  surfaceData: VolatilityData[]
  tenors: string[]
  onTenorChange: (tenor: string) => void
  loading: boolean
}

interface SmilePoint {
  delta: number
  vol: number
  label: string
  strike?: number
}

export function VolatilitySmileSection({ 
  selectedPair, 
  selectedTenor, 
  surfaceData, 
  tenors, 
  onTenorChange,
  loading 
}: VolatilitySmileSectionProps) {
  const { currentTheme } = useTheme()
  const [hoverPoint, setHoverPoint] = useState<SmilePoint | null>(null)
  
  // Get data for selected tenor
  const currentTenorData = useMemo(() => {
    const tenorIndex = tenors.indexOf(selectedTenor)
    return tenorIndex >= 0 ? surfaceData[tenorIndex] : null
  }, [surfaceData, selectedTenor, tenors])
  
  // Construct smile points from Bloomberg RR/BF data
  const smilePoints = useMemo(() => {
    if (!currentTenorData) return []
    
    const points: SmilePoint[] = []
    const atmVol = currentTenorData.atm_bid && currentTenorData.atm_ask 
      ? (currentTenorData.atm_bid + currentTenorData.atm_ask) / 2 
      : null
    
    if (!atmVol) return []
    
    // ATM point
    points.push({
      delta: 50,
      vol: atmVol,
      label: 'ATM'
    })
    
    // Calculate smile points for different deltas
    const deltas = [
      { delta: 25, rrBid: currentTenorData.rr_25d_bid, rrAsk: currentTenorData.rr_25d_ask, bfBid: currentTenorData.bf_25d_bid, bfAsk: currentTenorData.bf_25d_ask },
      { delta: 10, rrBid: currentTenorData.rr_10d_bid, rrAsk: currentTenorData.rr_10d_ask, bfBid: currentTenorData.bf_10d_bid, bfAsk: currentTenorData.bf_10d_ask }
    ]
    
    deltas.forEach(({ delta, rrBid, rrAsk, bfBid, bfAsk }) => {
      if (rrBid !== null && rrAsk !== null && bfBid !== null && bfAsk !== null) {
        const rrMid = (rrBid + rrAsk) / 2
        const bfMid = (bfBid + bfAsk) / 2
        
        // FX smile construction: RR = vol(call) - vol(put), BF = (vol(call) + vol(put))/2 - ATM
        const putVol = atmVol - rrMid/2 + bfMid
        const callVol = atmVol + rrMid/2 + bfMid
        
        points.push({
          delta: delta,
          vol: putVol,
          label: `${delta}Δ Put`
        })
        
        points.push({
          delta: 100 - delta,
          vol: callVol,
          label: `${delta}Δ Call`
        })
      }
    })
    
    return points.filter(p => p.vol > 0).sort((a, b) => a.delta - b.delta)
  }, [currentTenorData])
  
  // SVG dimensions - responsive to container
  const width = '100%'
  const height = '100%'
  const margin = { top: 20, right: 20, bottom: 40, left: 50 }
  // Use viewBox for responsive scaling
  const viewBoxWidth = 400
  const viewBoxHeight = 300
  const chartWidth = viewBoxWidth - margin.left - margin.right
  const chartHeight = viewBoxHeight - margin.top - margin.bottom
  
  // Scales
  const xScale = (delta: number) => (delta / 100) * chartWidth
  const yScale = (vol: number) => {
    if (smilePoints.length === 0) return chartHeight / 2
    const minVol = Math.min(...smilePoints.map(p => p.vol)) * 0.95
    const maxVol = Math.max(...smilePoints.map(p => p.vol)) * 1.05
    return chartHeight - ((vol - minVol) / (maxVol - minVol)) * chartHeight
  }
  
  // Generate curve path
  const curvePath = useMemo(() => {
    if (smilePoints.length < 2) return ''
    
    let path = `M ${xScale(smilePoints[0].delta)} ${yScale(smilePoints[0].vol)}`
    
    for (let i = 1; i < smilePoints.length; i++) {
      const point = smilePoints[i]
      path += ` L ${xScale(point.delta)} ${yScale(point.vol)}`
    }
    
    return path
  }, [smilePoints])
  
  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '16px'
      }}>
        <h3 style={{ 
          fontSize: '16px', 
          fontWeight: '600', 
          margin: 0,
          color: currentTheme.text 
        }}>
          Volatility Smile - {selectedPair}
        </h3>
        
        {/* Tenor Selector */}
        <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
          {tenors.map(tenor => (
            <button
              key={tenor}
              onClick={() => onTenorChange(tenor)}
              style={{
                backgroundColor: tenor === selectedTenor ? currentTheme.primary : currentTheme.surface,
                color: tenor === selectedTenor ? currentTheme.background : currentTheme.text,
                border: `1px solid ${currentTheme.border}`,
                borderRadius: '4px',
                padding: '4px 8px',
                fontSize: '11px',
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
            >
              {tenor}
            </button>
          ))}
        </div>
      </div>
      
      {loading ? (
        <div style={{ 
          flex: 1, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          color: currentTheme.textSecondary 
        }}>
          Loading smile data...
        </div>
      ) : smilePoints.length === 0 ? (
        <div style={{ 
          flex: 1, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          color: currentTheme.textSecondary 
        }}>
          No data available for {selectedTenor}
        </div>
      ) : (
        <div style={{ flex: 1, position: 'relative', minHeight: '250px' }}>
          <svg 
            width={width} 
            height={height} 
            viewBox={`0 0 ${viewBoxWidth} ${viewBoxHeight}`}
            preserveAspectRatio="xMidYMid meet"
            style={{ overflow: 'visible', width: '100%', height: '100%' }}
          >
            <g transform={`translate(${margin.left}, ${margin.top})`}>
              
              {/* Grid lines */}
              <defs>
                <pattern id="grid" width={chartWidth/10} height={chartHeight/5} patternUnits="userSpaceOnUse">
                  <path 
                    d={`M ${chartWidth/10} 0 L 0 0 0 ${chartHeight/5}`} 
                    fill="none" 
                    stroke={currentTheme.border} 
                    strokeWidth="0.5"
                    opacity="0.3"
                  />
                </pattern>
              </defs>
              <rect width={chartWidth} height={chartHeight} fill="url(#grid)" />
              
              {/* X-axis */}
              <line 
                x1={0} y1={chartHeight} 
                x2={chartWidth} y2={chartHeight} 
                stroke={currentTheme.textSecondary} 
                strokeWidth={1}
              />
              
              {/* Y-axis */}
              <line 
                x1={0} y1={0} 
                x2={0} y2={chartHeight} 
                stroke={currentTheme.textSecondary} 
                strokeWidth={1}
              />
              
              {/* X-axis labels (Delta) */}
              {[10, 25, 50, 75, 90].map(delta => (
                <g key={delta}>
                  <line 
                    x1={xScale(delta)} y1={chartHeight-3}
                    x2={xScale(delta)} y2={chartHeight+3}
                    stroke={currentTheme.textSecondary}
                  />
                  <text 
                    x={xScale(delta)} 
                    y={chartHeight + 15}
                    textAnchor="middle"
                    fontSize="10"
                    fill={currentTheme.textSecondary}
                  >
                    {delta < 50 ? `${delta}P` : delta === 50 ? 'ATM' : `${100-delta}C`}
                  </text>
                </g>
              ))}
              
              {/* Smile curve */}
              <path 
                d={curvePath}
                fill="none"
                stroke={currentTheme.primary}
                strokeWidth={2}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              
              {/* Data points */}
              {smilePoints.map((point, index) => (
                <circle
                  key={index}
                  cx={xScale(point.delta)}
                  cy={yScale(point.vol)}
                  r={point.delta === 50 ? 5 : 3}
                  fill={point.delta === 50 ? '#E6D690' : currentTheme.primary}
                  stroke={currentTheme.background}
                  strokeWidth={1}
                  style={{ cursor: 'pointer' }}
                  onMouseEnter={() => setHoverPoint(point)}
                  onMouseLeave={() => setHoverPoint(null)}
                />
              ))}
              
              {/* Axis labels */}
              <text 
                x={chartWidth / 2} 
                y={chartHeight + 35}
                textAnchor="middle"
                fontSize="12"
                fill={currentTheme.textSecondary}
              >
                Delta
              </text>
              
              <text 
                x={-35} 
                y={chartHeight / 2}
                textAnchor="middle"
                fontSize="12"
                fill={currentTheme.textSecondary}
                transform={`rotate(-90, -35, ${chartHeight / 2})`}
              >
                Implied Vol (%)
              </text>
              
            </g>
          </svg>
          
          {/* Hover tooltip */}
          {hoverPoint && (
            <div style={{
              position: 'absolute',
              top: '10px',
              right: '10px',
              backgroundColor: currentTheme.surface,
              border: `1px solid ${currentTheme.border}`,
              borderRadius: '4px',
              padding: '8px',
              fontSize: '11px',
              color: currentTheme.text,
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
            }}>
              <div><strong>{hoverPoint.label}</strong></div>
              <div>Vol: {hoverPoint.vol.toFixed(3)}%</div>
              <div>Delta: {hoverPoint.delta}Δ</div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}