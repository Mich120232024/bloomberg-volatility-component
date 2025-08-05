import { useState, useEffect, useRef } from 'react'
import { useTheme } from '../contexts/ThemeContext'
import * as d3 from 'd3'
import { FXPair } from '../constants/currencies'

type CurrencyPair = FXPair
type DisplayMode = 'outright' | 'points' | 'implied_yield'

interface ForwardPoint {
  tenor: number     // Days to maturity
  years: number     // Years to maturity for proper scaling
  spot: number      // Spot rate
  forward: number   // Forward rate
  points: number    // Forward points (pips)
  impliedYield: number // Implied yield differential
  label: string     // Display label
  ticker: string    // Bloomberg ticker
  isInterpolated?: boolean
}

export function FXForwardCurvesTab() {
  const { currentTheme } = useTheme()
  const chartContainerRef = useRef<HTMLDivElement>(null)
  
  // Controls
  const [selectedPairs, setSelectedPairs] = useState<Set<CurrencyPair>>(new Set(['EURUSD', 'GBPUSD']))
  const [displayMode] = useState<DisplayMode>('outright')
  const [showGrid, setShowGrid] = useState(true)
  const [showLegend, setShowLegend] = useState(true)
  const [expandedSelector, setExpandedSelector] = useState(false)
  
  // Data
  const [forwardData, setForwardData] = useState<Map<CurrencyPair, ForwardPoint[]>>(new Map())
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)

  // Professional color palette
  const getPairColor = (pair: CurrencyPair): string => {
    const colors: Partial<Record<CurrencyPair, string>> = {
      EURUSD: '#1976D2',
      GBPUSD: '#D32F2F',
      USDJPY: '#7B1FA2',
      USDCHF: '#F57C00',
      AUDUSD: '#388E3C',
      USDCAD: '#E91E63',
      NZDUSD: '#00ACC1',
      // Add more as needed
    }
    return colors[pair] || '#757575'
  }

  // Fetch forward data using generic Bloomberg reference endpoint
  const fetchForwardData = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const apiUrl = import.meta.env.DEV ? 'http://localhost:8000' : 'http://20.172.249.92:8080'
      const newForwardData = new Map<CurrencyPair, ForwardPoint[]>()
      
      // Define tenors up to 5Y
      const tenors = ['1W', '2W', '1M', '2M', '3M', '6M', '9M', '12M', '15M', '18M', '21M', '2Y', '3Y', '4Y', '5Y']
      const tenorDays: Record<string, number> = {
        '1W': 7, '2W': 14, '1M': 30, '2M': 60, '3M': 90,
        '6M': 180, '9M': 270, '12M': 365, '15M': 455,
        '18M': 545, '21M': 635, '2Y': 730, '3Y': 1095,
        '4Y': 1460, '5Y': 1825
      }
      
      // Process each selected pair
      for (const pair of selectedPairs) {
        // Build list of all tickers we need
        const securities: string[] = [
          `${pair} Curncy`, // Spot rate
          ...tenors.map(tenor => `${pair}${tenor} Curncy`) // Forward rates
        ]
        
        // Call generic Bloomberg reference endpoint
        const response = await fetch(`${apiUrl}/api/bloomberg/reference`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test'
          },
          body: JSON.stringify({
            securities: securities,
            fields: ['PX_LAST', 'PX_BID', 'PX_ASK']
          })
        })
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }
        
        const result = await response.json()
        
        if (result.data && result.data.securities_data) {
          const points: ForwardPoint[] = []
          let spotRate = 0
          
          // Process each security response
          for (const secData of result.data.securities_data) {
            if (secData.success && secData.fields && secData.fields.PX_LAST !== null) {
              const ticker = secData.security
              const value = secData.fields.PX_LAST
              
              // Check if this is spot rate
              if (ticker === `${pair} Curncy`) {
                spotRate = value
                points.push({
                  tenor: 0,
                  years: 0,
                  spot: spotRate,
                  forward: spotRate,
                  points: 0,
                  impliedYield: 0,
                  label: 'Spot',
                  ticker: ticker
                })
              } else {
                // This is a forward rate
                const tenorMatch = ticker.match(new RegExp(`${pair}(\\d+[WMY]) Curncy`))
                if (tenorMatch && spotRate > 0) {
                  const tenor = tenorMatch[1]
                  const days = tenorDays[tenor] || 30
                  const years = days / 365.25
                  
                  // Forward points are the raw value from Bloomberg
                  const forwardPoints = value
                  
                  // Calculate outright forward rate
                  let outright: number
                  if (pair.startsWith('USD') && pair !== 'USDJPY') {
                    outright = spotRate + (forwardPoints / 10000)
                  } else if (pair === 'USDJPY' || pair.endsWith('JPY')) {
                    outright = spotRate + (forwardPoints / 100)
                  } else {
                    outright = spotRate + (forwardPoints / 10000)
                  }
                  
                  // Calculate implied yield differential
                  const impliedYield = years > 0 ? ((outright / spotRate) ** (1 / years) - 1) * 100 : 0
                  
                  points.push({
                    tenor: days,
                    years: years,
                    spot: spotRate,
                    forward: outright,
                    points: forwardPoints,
                    impliedYield: impliedYield,
                    label: tenor,
                    ticker: ticker
                  })
                }
              }
            }
          }
          
          // Sort by tenor days
          points.sort((a, b) => a.tenor - b.tenor)
          
          if (points.length > 0) {
            newForwardData.set(pair, points)
          }
        }
      }
      
      setForwardData(newForwardData)
      setLastUpdate(new Date())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch forward data')
      console.error('Forward data fetch error:', err)
    } finally {
      setLoading(false)
    }
  }

  // Draw chart using D3 (rest of the code remains the same)
  const drawChart = () => {
    if (!chartContainerRef.current || forwardData.size === 0) return

    // Clear previous chart
    d3.select(chartContainerRef.current).select('svg').remove()

    // Dimensions
    const margin = { top: 30, right: 150, bottom: 60, left: 80 }
    const width = chartContainerRef.current.clientWidth - margin.left - margin.right
    const height = 500 - margin.top - margin.bottom

    // Create SVG
    const svg = d3.select(chartContainerRef.current)
      .append('svg')
      .attr('width', width + margin.left + margin.right)
      .attr('height', height + margin.top + margin.bottom)
      .style('background', currentTheme.background)

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`)

    // Scales
    const xScale = d3.scaleLinear()
      .domain([0, 5])  // 0 to 5 years
      .range([0, width])
      .nice()

    // Y scale for outright rates
    const allForwards = Array.from(forwardData.values()).flat().map(d => d.forward)
    const yMin = Math.min(...allForwards) * 0.995
    const yMax = Math.max(...allForwards) * 1.005
    
    const yScale = d3.scaleLinear()
      .domain([yMin, yMax])
      .range([height, 0])
      .nice()

    // Grid lines
    if (showGrid) {
      // X-axis grid
      const xGridLines = g.append('g')
        .attr('class', 'grid')
        .attr('transform', `translate(0,${height})`)
        
      xGridLines.call(d3.axisBottom(xScale)
        .tickSize(-height)
        .tickFormat(() => '')
      )
      
      xGridLines.selectAll('line')
        .style('stroke', currentTheme.border)
        .style('stroke-dasharray', '2,2')
        .style('opacity', 0.3)
      
      xGridLines.select('.domain').remove()

      // Y-axis grid
      const yGridLines = g.append('g')
        .attr('class', 'grid')
        
      yGridLines.call(d3.axisLeft(yScale)
        .tickSize(-width)
        .tickFormat(() => '')
      )
      
      yGridLines.selectAll('line')
        .style('stroke', currentTheme.border)
        .style('stroke-dasharray', '2,2')
        .style('opacity', 0.3)
        
      yGridLines.select('.domain').remove()
    }

    // X-axis
    const xAxis = g.append('g')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(xScale)
        .tickFormat(d => d === 0 ? 'Spot' : `${d}Y`)
      )

    xAxis.selectAll('text')
      .style('fill', currentTheme.text)
      .style('font-size', '12px')

    xAxis.select('.domain')
      .style('stroke', currentTheme.border)

    xAxis.selectAll('.tick line')
      .style('stroke', currentTheme.border)

    // Y-axis
    const yAxis = g.append('g')
      .call(d3.axisLeft(yScale)
        .tickFormat(d => (d as number).toFixed(4))
      )

    yAxis.selectAll('text')
      .style('fill', currentTheme.text)
      .style('font-size', '12px')

    yAxis.select('.domain')
      .style('stroke', currentTheme.border)

    yAxis.selectAll('.tick line')
      .style('stroke', currentTheme.border)

    // Line generator
    const line = d3.line<ForwardPoint>()
      .x(d => xScale(d.years))
      .y(d => yScale(d.forward))
      .curve(d3.curveMonotoneX)

    // Draw lines for each currency pair
    forwardData.forEach((points, pair) => {
      const color = getPairColor(pair)
      
      // Draw the line
      const path = g.append('path')
        .datum(points)
        .attr('fill', 'none')
        .attr('stroke', color)
        .attr('stroke-width', 2.5)
        .attr('d', line)
        .style('opacity', 0.9)

      // Add points
      g.selectAll(`.point-${pair.replace('/', '')}`)
        .data(points)
        .enter().append('circle')
        .attr('class', `point-${pair.replace('/', '')}`)
        .attr('cx', d => xScale(d.years))
        .attr('cy', d => yScale(d.forward))
        .attr('r', 4)
        .attr('fill', color)
        .style('cursor', 'pointer')
    })

    // Legend
    if (showLegend) {
      const legend = svg.append('g')
        .attr('transform', `translate(${width + margin.left + 20}, ${margin.top})`)

      let yOffset = 0
      forwardData.forEach((points, pair) => {
        const color = getPairColor(pair)
        
        const legendItem = legend.append('g')
          .attr('transform', `translate(0, ${yOffset})`)

        // Color rect
        legendItem.append('rect')
          .attr('x', 0)
          .attr('y', 0)
          .attr('width', 14)
          .attr('height', 14)
          .attr('fill', color)
          .attr('rx', 2)

        // Label
        legendItem.append('text')
          .attr('x', 20)
          .attr('y', 11)
          .text(pair)
          .style('font-size', '13px')
          .style('fill', currentTheme.text)
          .style('font-weight', '600')

        // Latest value
        const latestPoint = points[points.length - 1]
        if (latestPoint) {
          legendItem.append('text')
            .attr('x', 20)
            .attr('y', 26)
            .text(`${latestPoint.label}: ${latestPoint.forward.toFixed(4)}`)
            .style('font-size', '11px')
            .style('fill', currentTheme.textSecondary)
        }

        yOffset += 35
      })
    }

    // Title
    svg.append('text')
      .attr('x', margin.left + width / 2)
      .attr('y', 15)
      .attr('text-anchor', 'middle')
      .style('font-size', '16px')
      .style('font-weight', '600')
      .style('fill', currentTheme.text)
      .text('FX Forward Rates')

    // Axis labels
    svg.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('y', 20)
      .attr('x', 0 - (height / 2 + margin.top))
      .attr('dy', '1em')
      .style('text-anchor', 'middle')
      .style('fill', currentTheme.text)
      .style('font-size', '14px')
      .text('Forward Rate')

    svg.append('text')
      .attr('transform', `translate(${width / 2 + margin.left}, ${height + margin.top + 45})`)
      .style('text-anchor', 'middle')
      .style('fill', currentTheme.text)
      .style('font-size', '14px')
      .text('Maturity')
  }

  // Effects
  useEffect(() => {
    if (selectedPairs.size > 0) {
      fetchForwardData()
    }
  }, [selectedPairs])

  useEffect(() => {
    drawChart()
  }, [forwardData, currentTheme, showGrid, showLegend, displayMode])

  useEffect(() => {
    const handleResize = () => {
      drawChart()
    }
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [forwardData, displayMode])

  const togglePair = (pair: CurrencyPair) => {
    const newSet = new Set(selectedPairs)
    if (newSet.has(pair)) {
      newSet.delete(pair)
    } else {
      newSet.add(pair)
    }
    setSelectedPairs(newSet)
  }

  // Rest of the component UI remains the same...
  return (
    <div style={{
      backgroundColor: currentTheme.surface,
      borderRadius: '8px',
      border: `1px solid ${currentTheme.border}`,
      overflow: 'hidden',
      height: '100%',
      display: 'flex',
      flexDirection: 'column'
    }}>
      {/* Header Controls */}
      <div style={{
        borderBottom: `1px solid ${currentTheme.border}`,
        backgroundColor: currentTheme.background,
        padding: '12px 16px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '12px'
      }}>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <span style={{ fontSize: '11px', color: currentTheme.textSecondary }}>
            FX Forward Rates (Outright) - Using Generic Bloomberg API
          </span>
        </div>

        <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={showGrid}
              onChange={(e) => setShowGrid(e.target.checked)}
              style={{ cursor: 'pointer' }}
            />
            Grid
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={showLegend}
              onChange={(e) => setShowLegend(e.target.checked)}
              style={{ cursor: 'pointer' }}
            />
            Legend
          </label>
          
          <button
            onClick={fetchForwardData}
            disabled={loading || selectedPairs.size === 0}
            style={{
              padding: '2px 6px',
              backgroundColor: currentTheme.primary,
              color: currentTheme.background,
              border: `1px solid ${currentTheme.border}`,
              borderRadius: '3px',
              cursor: loading ? 'not-allowed' : 'pointer',
              fontSize: '9px',
              opacity: loading ? 0.5 : 1
            }}
          >
            {loading ? 'Loading...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Currency Pair Selector */}
      <div style={{
        borderBottom: `1px solid ${currentTheme.border}`,
        backgroundColor: currentTheme.background,
      }}>
        <div style={{
          padding: '12px 16px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          cursor: 'pointer',
          userSelect: 'none'
        }}
        onClick={() => setExpandedSelector(!expandedSelector)}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '13px', fontWeight: '600', color: currentTheme.text }}>Currency Pairs</span>
            <span style={{ fontSize: '11px', color: currentTheme.textSecondary }}>
              ({selectedPairs.size} selected)
            </span>
          </div>
          <svg
            width="16"
            height="16"
            viewBox="0 0 16 16"
            style={{
              transform: expandedSelector ? 'rotate(180deg)' : 'rotate(0deg)',
              transition: 'transform 0.2s ease',
              fill: currentTheme.textSecondary
            }}
          >
            <path d="M8 10.5l-4-4h8l-4 4z"/>
          </svg>
        </div>
        
        {expandedSelector && (
          <div style={{ padding: '0 16px 16px' }}>
            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
              {(['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD'] as CurrencyPair[]).map(pair => (
                <button
                  key={pair}
                  onClick={() => togglePair(pair)}
                  style={{
                    padding: '2px 6px',
                    backgroundColor: selectedPairs.has(pair) ? currentTheme.primary : currentTheme.surface,
                    color: selectedPairs.has(pair) ? currentTheme.background : currentTheme.textSecondary,
                    border: `1px solid ${currentTheme.border}`,
                    borderRadius: '3px',
                    cursor: 'pointer',
                    fontSize: '9px',
                    transition: 'all 0.2s ease'
                  }}
                >
                  {pair}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Chart Container */}
      <div style={{ flex: 1, padding: '16px' }}>
        <div style={{
          backgroundColor: currentTheme.background,
          padding: '12px',
          borderRadius: '6px',
          border: `1px solid ${currentTheme.border}`,
          height: 'calc(100% - 24px)',
          display: 'flex',
          flexDirection: 'column',
          position: 'relative'
        }}>
          <h3 style={{ 
            fontSize: '13px', 
            fontWeight: '600', 
            margin: '0 0 12px 0',
            color: currentTheme.text
          }}>
            FX Forward Curves - Outright Rates
          </h3>
          
          {loading && (
            <div style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              fontSize: '14px',
              color: currentTheme.textSecondary
            }}>
              Loading forward curve data...
            </div>
          )}
          
          {error && (
            <div style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              fontSize: '14px',
              color: '#ef4444',
              textAlign: 'center'
            }}>
              Error: {error}
            </div>
          )}
          
          {!loading && !error && selectedPairs.size === 0 && (
            <div style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              fontSize: '14px',
              color: currentTheme.textSecondary,
              textAlign: 'center'
            }}>
              Select one or more currency pairs to display forward curves
            </div>
          )}
          
          <div ref={chartContainerRef} style={{ width: '100%', flex: 1 }} />
        </div>
      </div>

      {/* Status Bar */}
      <div style={{
        borderTop: `1px solid ${currentTheme.border}`,
        padding: '8px 16px',
        fontSize: '12px',
        color: currentTheme.textSecondary,
        display: 'flex',
        justifyContent: 'space-between'
      }}>
        <span>
          {forwardData.size > 0 && `Showing ${Array.from(forwardData.values()).flat().length} forward points across ${forwardData.size} pairs`}
        </span>
        <span>
          {lastUpdate && `Last update: ${lastUpdate.toLocaleTimeString()}`}
        </span>
      </div>
    </div>
  )
}