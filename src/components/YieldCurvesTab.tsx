import { useState, useEffect, useRef } from 'react'
import { useTheme } from '../contexts/ThemeContext'
import * as d3 from 'd3'
import { yieldCurvesAPI, YieldCurveData } from '../api/yieldCurves'

// G10 currencies
const G10_CURRENCIES = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD', 'SEK', 'NOK']

// Color scheme for curves
const CURVE_COLORS: Record<string, string> = {
  USD: '#2563eb', // Blue
  EUR: '#dc2626', // Red
  GBP: '#16a34a', // Green
  JPY: '#ea580c', // Orange
  CHF: '#7c3aed', // Purple
  CAD: '#0891b2', // Cyan
  AUD: '#c026d3', // Fuchsia
  NZD: '#65a30d', // Lime
  SEK: '#f59e0b', // Amber
  NOK: '#6366f1'  // Indigo
}

export function YieldCurvesTab() {
  const { currentTheme } = useTheme()
  const chartContainerRef = useRef<HTMLDivElement>(null)
  
  const [selectedCurrencies, setSelectedCurrencies] = useState<string[]>(['USD', 'EUR', 'GBP'])
  const [curveData, setCurveData] = useState<YieldCurveData[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Fetch yield curves
  const fetchCurves = async () => {
    console.log('🚀 Fetching yield curves for:', selectedCurrencies)
    setLoading(true)
    setError(null)
    
    try {
      const curves = await yieldCurvesAPI.getMultipleCurves(selectedCurrencies)
      setCurveData(curves)
      console.log(`✅ Fetched ${curves.length} curves`)
    } catch (err) {
      console.error('❌ Failed to fetch curves:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch yield curves')
    } finally {
      setLoading(false)
    }
  }

  // Toggle currency selection
  const toggleCurrency = (currency: string) => {
    setSelectedCurrencies(prev => {
      if (prev.includes(currency)) {
        return prev.filter(c => c !== currency)
      } else {
        return [...prev, currency]
      }
    })
  }

  // Draw chart using D3
  const drawChart = () => {
    if (!chartContainerRef.current || curveData.length === 0) return

    // Clear previous chart
    d3.select(chartContainerRef.current).select('svg').remove()

    // Dimensions
    const margin = { top: 30, right: 120, bottom: 60, left: 70 }
    const width = chartContainerRef.current.clientWidth - margin.left - margin.right
    const height = 500 - margin.top - margin.bottom

    // Create SVG
    const svg = d3.select(chartContainerRef.current)
      .append('svg')
      .attr('width', width + margin.left + margin.right)
      .attr('height', height + margin.top + margin.bottom)

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`)

    // Find data ranges
    const allPoints = curveData.flatMap(curve => curve.points)
    const xExtent = [0, Math.max(...allPoints.map(p => p.tenorYears))]
    const yExtent = d3.extent(allPoints.filter(p => p.rate !== null), p => p.rate!) as [number, number]

    // Scales
    const xScale = d3.scaleLinear()
      .domain(xExtent)
      .range([0, width])

    const yScale = d3.scaleLinear()
      .domain(yExtent)
      .nice()
      .range([height, 0])

    // Line generator
    const line = d3.line<any>()
      .defined(d => d.rate !== null)
      .x(d => xScale(d.tenorYears))
      .y(d => yScale(d.rate))
      .curve(d3.curveCatmullRom.alpha(0.5))

    // Add grid lines
    g.append('g')
      .attr('class', 'grid')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(xScale)
        .tickSize(-height)
        .tickFormat(() => '')
      )
      .style('stroke-dasharray', '3,3')
      .style('opacity', 0.3)

    g.append('g')
      .attr('class', 'grid')
      .call(d3.axisLeft(yScale)
        .tickSize(-width)
        .tickFormat(() => '')
      )
      .style('stroke-dasharray', '3,3')
      .style('opacity', 0.3)

    // Draw curves
    curveData.forEach(curve => {
      const validPoints = curve.points.filter(p => p.rate !== null)
      
      // Draw line
      g.append('path')
        .datum(validPoints)
        .attr('fill', 'none')
        .attr('stroke', CURVE_COLORS[curve.currency])
        .attr('stroke-width', 2)
        .attr('d', line)
        .style('opacity', 0.8)

      // Add points with tooltips
      g.selectAll(`.point-${curve.currency}`)
        .data(validPoints)
        .enter().append('circle')
        .attr('class', `point-${curve.currency}`)
        .attr('cx', d => xScale(d.tenorYears))
        .attr('cy', d => yScale(d.rate!))
        .attr('r', 3)
        .attr('fill', CURVE_COLORS[curve.currency])
        .style('cursor', 'pointer')
        .on('mouseover', function(event, d) {
          // Show tooltip
          const tooltip = d3.select('body').append('div')
            .attr('class', 'tooltip')
            .style('position', 'absolute')
            .style('padding', '8px')
            .style('background', currentTheme.surface)
            .style('border', `1px solid ${currentTheme.border}`)
            .style('border-radius', '4px')
            .style('pointer-events', 'none')
            .style('opacity', 0)

          tooltip.transition()
            .duration(200)
            .style('opacity', 0.9)

          tooltip.html(`
            <strong>${curve.currency} ${d.tenor}</strong><br/>
            Rate: ${d.rate!.toFixed(3)}%<br/>
            Ticker: ${d.ticker}
          `)
            .style('left', (event.pageX + 10) + 'px')
            .style('top', (event.pageY - 28) + 'px')
        })
        .on('mouseout', function() {
          d3.selectAll('.tooltip').remove()
        })

      // Add curve label
      const lastPoint = validPoints[validPoints.length - 1]
      if (lastPoint) {
        g.append('text')
          .attr('x', xScale(lastPoint.tenorYears) + 5)
          .attr('y', yScale(lastPoint.rate!))
          .attr('dy', '0.35em')
          .style('font-size', '12px')
          .style('font-weight', 'bold')
          .style('fill', CURVE_COLORS[curve.currency])
          .text(curve.currency)
      }
    })

    // X-axis
    g.append('g')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(xScale)
        .tickFormat(d => d < 1 ? `${Math.round(d * 12)}M` : `${d}Y`)
      )
      .style('font-size', '12px')

    // Y-axis
    g.append('g')
      .call(d3.axisLeft(yScale)
        .tickFormat(d => `${d}%`)
      )
      .style('font-size', '12px')

    // Axis labels
    g.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('y', 0 - margin.left)
      .attr('x', 0 - (height / 2))
      .attr('dy', '1em')
      .style('text-anchor', 'middle')
      .style('font-size', '14px')
      .text('Yield (%)')

    g.append('text')
      .attr('transform', `translate(${width / 2}, ${height + margin.bottom})`)
      .style('text-anchor', 'middle')
      .style('font-size', '14px')
      .text('Tenor')

    // Title
    svg.append('text')
      .attr('x', margin.left + width / 2)
      .attr('y', 20)
      .attr('text-anchor', 'middle')
      .style('font-size', '18px')
      .style('font-weight', 'bold')
      .text('OIS Yield Curves (Real Bloomberg Data)')
  }

  // Initial fetch
  useEffect(() => {
    if (selectedCurrencies.length > 0) {
      fetchCurves()
    }
  }, [selectedCurrencies])

  // Redraw chart when data or theme changes
  useEffect(() => {
    drawChart()
  }, [curveData, currentTheme])

  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      drawChart()
    }
    
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [curveData, currentTheme])

  return (
    <div style={{
      backgroundColor: currentTheme.surface,
      borderRadius: '8px',
      border: `1px solid ${currentTheme.border}`,
      padding: '20px',
      height: '100%',
      display: 'flex',
      flexDirection: 'column'
    }}>
      {/* Header */}
      <div style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h3 style={{ margin: 0 }}>OIS Yield Curves</h3>
          <button
            onClick={fetchCurves}
            disabled={loading || selectedCurrencies.length === 0}
            style={{
              padding: '8px 16px',
              backgroundColor: currentTheme.primary,
              color: currentTheme.background,
              border: 'none',
              borderRadius: '4px',
              cursor: loading || selectedCurrencies.length === 0 ? 'not-allowed' : 'pointer',
              opacity: loading || selectedCurrencies.length === 0 ? 0.6 : 1
            }}
          >
            {loading ? 'Loading...' : 'Refresh'}
          </button>
        </div>

        {/* Currency selector */}
        <div style={{ marginBottom: '16px' }}>
          <div style={{ fontSize: '14px', color: currentTheme.textSecondary, marginBottom: '8px' }}>
            Select currencies to display:
          </div>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {G10_CURRENCIES.map(currency => (
              <button
                key={currency}
                onClick={() => toggleCurrency(currency)}
                style={{
                  padding: '6px 12px',
                  borderRadius: '4px',
                  border: `1px solid ${currentTheme.border}`,
                  backgroundColor: selectedCurrencies.includes(currency) 
                    ? CURVE_COLORS[currency] 
                    : currentTheme.background,
                  color: selectedCurrencies.includes(currency) 
                    ? '#ffffff' 
                    : currentTheme.text,
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: selectedCurrencies.includes(currency) ? 'bold' : 'normal',
                  transition: 'all 0.2s'
                }}
              >
                {currency}
              </button>
            ))}
          </div>
        </div>

        {/* Data quality info */}
        {curveData.length > 0 && (
          <div style={{ fontSize: '14px', color: currentTheme.textSecondary }}>
            {curveData.map(curve => (
              <span key={curve.currency} style={{ marginRight: '16px' }}>
                {curve.currency}: {curve.dataQuality.validPoints}/{curve.dataQuality.totalPoints} points 
                ({curve.dataQuality.coverage.toFixed(0)}% coverage)
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Error display */}
      {error && (
        <div style={{ 
          color: '#ef4444', 
          marginBottom: '16px',
          padding: '12px',
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          borderRadius: '4px'
        }}>
          Error: {error}
        </div>
      )}

      {/* Chart container */}
      <div ref={chartContainerRef} style={{ flex: 1, minHeight: '500px' }} />

      {/* Data table */}
      {curveData.length > 0 && (
        <details style={{ marginTop: '20px' }}>
          <summary style={{ cursor: 'pointer', fontWeight: 'bold', marginBottom: '12px' }}>
            View Raw Data
          </summary>
          <div style={{ maxHeight: '300px', overflow: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
              <thead>
                <tr style={{ borderBottom: `2px solid ${currentTheme.border}` }}>
                  <th style={{ padding: '8px', textAlign: 'left' }}>Currency</th>
                  <th style={{ padding: '8px', textAlign: 'left' }}>Tenor</th>
                  <th style={{ padding: '8px', textAlign: 'right' }}>Rate (%)</th>
                  <th style={{ padding: '8px', textAlign: 'left' }}>Ticker</th>
                </tr>
              </thead>
              <tbody>
                {curveData.flatMap(curve => 
                  curve.points
                    .filter(p => p.rate !== null)
                    .map((point, idx) => (
                      <tr key={`${curve.currency}-${idx}`} style={{ borderBottom: `1px solid ${currentTheme.border}` }}>
                        <td style={{ padding: '8px', color: CURVE_COLORS[curve.currency], fontWeight: 'bold' }}>
                          {curve.currency}
                        </td>
                        <td style={{ padding: '8px' }}>{point.tenor}</td>
                        <td style={{ padding: '8px', textAlign: 'right' }}>{point.rate!.toFixed(3)}</td>
                        <td style={{ padding: '8px', fontSize: '12px', color: currentTheme.textSecondary }}>
                          {point.ticker}
                        </td>
                      </tr>
                    ))
                )}
              </tbody>
            </table>
          </div>
        </details>
      )}
    </div>
  )
}