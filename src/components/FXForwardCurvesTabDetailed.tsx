import { useState, useEffect, useRef } from 'react'
import { useTheme } from '../contexts/ThemeContext'
import * as d3 from 'd3'
import { FXPair, G10_USD_PAIRS, EM_USD_PAIRS, METAL_PAIRS, EUR_CROSSES, GBP_CROSSES } from '../constants/currencies'

type CurrencyPair = FXPair
type DisplayMode = 'cards' | 'chart' | 'table'

interface ForwardPoint {
  tenor: number     // Days to maturity
  years: number     // Years to maturity for proper scaling
  spot: number      // Spot rate
  forward: number   // Forward rate
  points: number    // Forward points (pips)
  impliedYield: number // Implied yield differential
  label: string     // Display label
  ticker: string    // Bloomberg ticker
  bid?: number      // Bid rate
  ask?: number      // Ask rate
  lastUpdate?: string // Bloomberg last update timestamp
  isInterpolated?: boolean
}

interface BloombergResponse {
  security: string
  fields: {
    PX_LAST?: number
    PX_BID?: number
    PX_ASK?: number
    LAST_UPDATE?: string
  }
  success: boolean
}

export function FXForwardCurvesTabDetailed() {
  const { currentTheme } = useTheme()
  const chartContainerRef = useRef<HTMLDivElement>(null)
  
  // Controls
  const [selectedPairs, setSelectedPairs] = useState<Set<CurrencyPair>>(new Set(['EURUSD']))
  const [displayMode, setDisplayMode] = useState<DisplayMode>('cards')
  const [showGrid, setShowGrid] = useState(true)
  const [showLegend, setShowLegend] = useState(true)
  const [expandedSelector, setExpandedSelector] = useState(false)
  
  // Data
  const [forwardData, setForwardData] = useState<Map<CurrencyPair, ForwardPoint[]>>(new Map())
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)
  const [dataSource, setDataSource] = useState<string>('')

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
        
        // Call generic Bloomberg reference endpoint with more fields
        const response = await fetch(`${apiUrl}/api/bloomberg/reference`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test'
          },
          body: JSON.stringify({
            securities: securities,
            fields: ['PX_LAST', 'PX_BID', 'PX_ASK', 'LAST_UPDATE']
          })
        })
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }
        
        const result = await response.json()
        
        // Set data source
        if (result.data?.source) {
          setDataSource(result.data.source)
        }
        
        if (result.data && result.data.securities_data) {
          const points: ForwardPoint[] = []
          let spotRate = 0
          let spotLastUpdate = ''
          
          // Process each security response
          for (const secData of result.data.securities_data as BloombergResponse[]) {
            if (secData.success && secData.fields && secData.fields.PX_LAST !== null) {
              const ticker = secData.security
              const value = secData.fields.PX_LAST
              const bid = secData.fields.PX_BID
              const ask = secData.fields.PX_ASK
              const lastUpdate = secData.fields.LAST_UPDATE
              
              // Check if this is spot rate
              if (ticker === `${pair} Curncy`) {
                spotRate = value
                spotLastUpdate = lastUpdate || ''
                points.push({
                  tenor: 0,
                  years: 0,
                  spot: spotRate,
                  forward: spotRate,
                  points: 0,
                  impliedYield: 0,
                  label: 'Spot',
                  ticker: ticker,
                  bid: bid,
                  ask: ask,
                  lastUpdate: lastUpdate
                })
              } else {
                // This is a forward rate
                const tenorMatch = ticker.match(new RegExp(`${pair}(\\d+[WM]|\\d+Y) Curncy`))
                if (tenorMatch && spotRate > 0) {
                  const tenor = tenorMatch[1]
                  const days = tenorDays[tenor] || 30
                  const years = days / 365.25
                  
                  // Forward points are the raw value from Bloomberg
                  const forwardPoints = value
                  
                  // Calculate outright forward rate
                  // Bloomberg convention: JPY pairs use 100 pip factor, all others use 10000
                  let outright: number
                  if (pair.includes('JPY')) {
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
                    ticker: ticker,
                    bid: bid,
                    ask: ask,
                    lastUpdate: lastUpdate || spotLastUpdate
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

  // Render cards view
  const renderCards = () => {
    const cards: JSX.Element[] = []
    
    forwardData.forEach((points, pair) => {
      cards.push(
        <div key={pair} style={{ marginBottom: '24px' }}>
          <h4 style={{ 
            fontSize: '14px', 
            fontWeight: '600', 
            margin: '0 0 12px 0',
            color: getPairColor(pair)
          }}>
            {pair}
          </h4>
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
            gap: '12px'
          }}>
            {points.map((point, idx) => (
              <div key={idx} style={{
                backgroundColor: currentTheme.surface,
                border: `1px solid ${currentTheme.border}`,
                borderRadius: '6px',
                padding: '12px',
                fontSize: '11px'
              }}>
                <div style={{ 
                  fontWeight: '600', 
                  marginBottom: '6px',
                  color: currentTheme.text
                }}>
                  {point.label}
                </div>
                <div style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between',
                  marginBottom: '4px'
                }}>
                  <span style={{ color: currentTheme.textSecondary }}>Rate:</span>
                  <span style={{ fontWeight: '600' }}>{point.forward.toFixed(4)}</span>
                </div>
                <div style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between',
                  marginBottom: '4px'
                }}>
                  <span style={{ color: currentTheme.textSecondary }}>Points:</span>
                  <span>{point.points.toFixed(1)}</span>
                </div>
                {point.bid && point.ask && (
                  <div style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between',
                    marginBottom: '4px',
                    fontSize: '10px'
                  }}>
                    <span style={{ color: currentTheme.textSecondary }}>Bid/Ask:</span>
                    <span>{point.bid.toFixed(1)}/{point.ask.toFixed(1)}</span>
                  </div>
                )}
                {point.lastUpdate && (
                  <div style={{ 
                    fontSize: '9px',
                    color: currentTheme.textSecondary,
                    textAlign: 'right',
                    marginTop: '4px'
                  }}>
                    {point.lastUpdate}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )
    })
    
    return <div style={{ padding: '16px', overflow: 'auto' }}>{cards}</div>
  }

  // Draw chart using D3 (previous implementation)
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

      // Add points with hover
      const pointGroup = g.selectAll(`.point-${pair.replace('/', '')}`)
        .data(points)
        .enter().append('g')
        .attr('class', `point-${pair.replace('/', '')}`)

      pointGroup.append('circle')
        .attr('cx', d => xScale(d.years))
        .attr('cy', d => yScale(d.forward))
        .attr('r', 4)
        .attr('fill', color)
        .style('cursor', 'pointer')

      // Add tooltip on hover
      pointGroup.append('title')
        .text(d => 
          `${pair} ${d.label}\n` +
          `Rate: ${d.forward.toFixed(4)}\n` +
          `Points: ${d.points.toFixed(1)}\n` +
          `Implied Yield: ${d.impliedYield.toFixed(2)}%\n` +
          `Updated: ${d.lastUpdate || 'N/A'}`
        )
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
    if (displayMode === 'chart') {
      drawChart()
    }
  }, [forwardData, currentTheme, showGrid, showLegend, displayMode])

  useEffect(() => {
    const handleResize = () => {
      if (displayMode === 'chart') {
        drawChart()
      }
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

  // Table view
  const renderTable = () => {
    const rows: JSX.Element[] = []
    
    forwardData.forEach((points, pair) => {
      points.forEach((point, idx) => {
        rows.push(
          <tr key={`${pair}-${idx}`}>
            <td style={{ padding: '8px', fontWeight: '600', color: getPairColor(pair) }}>{pair}</td>
            <td style={{ padding: '8px' }}>{point.label}</td>
            <td style={{ padding: '8px', textAlign: 'right' }}>{point.forward.toFixed(4)}</td>
            <td style={{ padding: '8px', textAlign: 'right' }}>{point.points.toFixed(1)}</td>
            <td style={{ padding: '8px', textAlign: 'right' }}>{point.impliedYield.toFixed(2)}%</td>
            <td style={{ padding: '8px', fontSize: '10px', color: currentTheme.textSecondary }}>
              {point.lastUpdate || 'N/A'}
            </td>
          </tr>
        )
      })
    })
    
    return (
      <div style={{ padding: '16px', overflow: 'auto' }}>
        <table style={{ 
          width: '100%', 
          borderCollapse: 'collapse',
          fontSize: '12px'
        }}>
          <thead>
            <tr style={{ borderBottom: `2px solid ${currentTheme.border}` }}>
              <th style={{ padding: '8px', textAlign: 'left' }}>Pair</th>
              <th style={{ padding: '8px', textAlign: 'left' }}>Tenor</th>
              <th style={{ padding: '8px', textAlign: 'right' }}>Rate</th>
              <th style={{ padding: '8px', textAlign: 'right' }}>Points</th>
              <th style={{ padding: '8px', textAlign: 'right' }}>Impl. Yield</th>
              <th style={{ padding: '8px', textAlign: 'left' }}>Updated</th>
            </tr>
          </thead>
          <tbody>
            {rows}
          </tbody>
        </table>
      </div>
    )
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
            FX Forward Rates - {dataSource || 'Connecting...'}
          </span>
        </div>

        <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
          {/* Display mode selector */}
          <div style={{ display: 'flex', gap: '4px' }}>
            {(['cards', 'chart', 'table'] as DisplayMode[]).map(mode => (
              <button
                key={mode}
                onClick={() => setDisplayMode(mode)}
                style={{
                  padding: '2px 8px',
                  backgroundColor: displayMode === mode ? currentTheme.primary : currentTheme.surface,
                  color: displayMode === mode ? currentTheme.background : currentTheme.text,
                  border: `1px solid ${currentTheme.border}`,
                  borderRadius: '3px',
                  cursor: 'pointer',
                  fontSize: '11px',
                  textTransform: 'capitalize'
                }}
              >
                {mode}
              </button>
            ))}
          </div>

          {displayMode === 'chart' && (
            <>
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
            </>
          )}
          
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
            {/* G10 USD Pairs */}
            <div style={{ marginBottom: '12px' }}>
              <div style={{ fontSize: '11px', color: currentTheme.textSecondary, marginBottom: '6px', fontWeight: '600' }}>
                G10 USD Pairs
              </div>
              <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '8px' }}>
                {G10_USD_PAIRS.map(pair => (
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

            {/* EM USD Pairs */}
            <div style={{ marginBottom: '12px' }}>
              <div style={{ fontSize: '11px', color: currentTheme.textSecondary, marginBottom: '6px', fontWeight: '600' }}>
                EM USD Pairs
              </div>
              <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '8px' }}>
                {EM_USD_PAIRS.map(pair => (
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

            {/* EUR Crosses */}
            <div style={{ marginBottom: '12px' }}>
              <div style={{ fontSize: '11px', color: currentTheme.textSecondary, marginBottom: '6px', fontWeight: '600' }}>
                EUR Crosses
              </div>
              <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '8px' }}>
                {EUR_CROSSES.map(pair => (
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

            {/* GBP Crosses */}
            <div>
              <div style={{ fontSize: '11px', color: currentTheme.textSecondary, marginBottom: '6px', fontWeight: '600' }}>
                GBP Crosses
              </div>
              <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                {GBP_CROSSES.map(pair => (
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
          </div>
        )}
      </div>

      {/* Main Content Container */}
      <div style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
        {loading && (
          <div style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            fontSize: '14px',
            color: currentTheme.textSecondary,
            zIndex: 10
          }}>
            Loading forward curve data from Bloomberg Terminal...
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
            textAlign: 'center',
            zIndex: 10
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
            textAlign: 'center',
            zIndex: 10
          }}>
            Select one or more currency pairs to display forward curves
          </div>
        )}
        
        {!loading && !error && selectedPairs.size > 0 && forwardData.size > 0 && (
          displayMode === 'cards' ? renderCards() :
          displayMode === 'table' ? renderTable() :
          <div ref={chartContainerRef} style={{ width: '100%', height: '100%', padding: '16px' }} />
        )}
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