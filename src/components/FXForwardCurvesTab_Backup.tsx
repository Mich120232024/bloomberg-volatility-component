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

export function FXForwardCurvesTab() {
  const { currentTheme } = useTheme()
  const chartContainerRef = useRef<HTMLDivElement>(null)
  
  // Controls
  const [selectedPairs, setSelectedPairs] = useState<Set<CurrencyPair>>(new Set(['EURUSD']))
  const displayMode: DisplayMode = 'chart' // Fixed to chart view only
  const [showGrid, setShowGrid] = useState(true)
  const [showLegend, setShowLegend] = useState(true)
  const [expandedSelector, setExpandedSelector] = useState(false)
  const [showForwardPoints, setShowForwardPoints] = useState(true) // Toggle between points and rates
  
  // Data
  const [forwardData, setForwardData] = useState<Map<CurrencyPair, ForwardPoint[]>>(new Map())
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)
  const [dataSource, setDataSource] = useState<string>('')

  // Professional color palette with extensive coverage
  const getPairColor = (pair: CurrencyPair): string => {
    const colors: Partial<Record<CurrencyPair, string>> = {
      // G10 USD Pairs
      EURUSD: '#1976D2',
      GBPUSD: '#D32F2F', 
      USDJPY: '#7B1FA2',
      USDCHF: '#F57C00',
      AUDUSD: '#388E3C',
      USDCAD: '#E91E63',
      NZDUSD: '#00ACC1',
      USDNOK: '#795548',
      USDSEK: '#607D8B',
      USDSGD: '#FF5722',
      // EM USD Pairs
      USDBRL: '#9C27B0',
      USDMXN: '#3F51B5',
      USDCNH: '#009688',
      USDKRW: '#8BC34A',
      USDINR: '#FF9800',
      USDTRY: '#673AB7',
      USDCZK: '#4CAF50',
      USDHUF: '#2196F3',
      USDPLN: '#FFC107',
      USDRON: '#9E9E9E',
      USDZAR: '#CDDC39',
      USDTHB: '#FF9800',
      USDPHP: '#795548',
      // EUR Crosses
      EURGBP: '#E91E63',
      EURJPY: '#9C27B0',
      EURCHF: '#FF5722',
      EURAUD: '#4CAF50',
      EURCAD: '#2196F3',
      EURNZD: '#FF9800',
      EURNOK: '#607D8B',
      EURSEK: '#8BC34A',
      EURSGD: '#795548',
      EURCZK: '#FFC107',
      EURHUF: '#9E9E9E',
      EURPLN: '#CDDC39',
      EURTRY: '#673AB7',
      EURZAR: '#3F51B5',
      // GBP Crosses
      GBPJPY: '#7B1FA2',
      GBPCHF: '#009688',
      GBPAUD: '#8BC34A',
      GBPCAD: '#FF5722',
      GBPNZD: '#4CAF50',
      GBPNOK: '#2196F3',
      GBPSEK: '#FF9800',
      GBPSGD: '#795548',
      // Metals
      XAGUSD: '#9E9E9E',
      XAUUSD: '#FFC107'
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
          
          // First pass: find spot rate
          for (const secData of result.data.securities_data as BloombergResponse[]) {
            if (secData.success && secData.fields && secData.fields.PX_LAST !== null) {
              const ticker = secData.security
              if (ticker === `${pair} Curncy`) {
                spotRate = secData.fields.PX_LAST
                spotLastUpdate = secData.fields.LAST_UPDATE || ''
                // console.log(`Found ${pair} spot rate:`, spotRate)
                break
              }
            }
          }
          
          // Second pass: process all data including forwards
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
                // console.log(`${pair} Spot rate:`, { ticker, spotRate, value })
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
                  
                  // Bloomberg forward tickers return outright forward rates, not forward points
                  // We need to calculate forward points from the outright rates
                  const outrightForwardRate = value
                  const outright = outrightForwardRate
                  
                  // Calculate forward points: (Forward Rate - Spot Rate) * Pip Factor
                  let forwardPoints: number
                  if (pair.includes('JPY')) {
                    forwardPoints = (outrightForwardRate - spotRate) * 100
                  } else {
                    forwardPoints = (outrightForwardRate - spotRate) * 10000
                  }
                  
                  // Debug log for first few pairs to verify calculation
                  if (['EURUSD', 'USDPLN', 'EURPLN'].includes(pair) && ['1Y', '5Y'].includes(tenor)) {
                    console.log(`${pair} ${tenor} DEBUG:`, {
                      ticker,
                      rawValue: value,
                      spotRate: spotRate.toFixed(6),
                      forwardRate: outrightForwardRate.toFixed(6),
                      forwardPoints: forwardPoints.toFixed(1),
                      isValidForwardRate: outrightForwardRate > 0 && outrightForwardRate < 1000,
                      pipFactor: pair.includes('JPY') ? 100 : 10000
                    })
                  }
                  
                  // Calculate implied yield differential
                  const impliedYield = years > 0 ? ((outright / spotRate) ** (1 / years) - 1) * 100 : 0
                  
                  // Debug calculation for EURUSD
                  // if (pair === 'EURUSD' && tenor === '1M') {
                  //   console.log(`${pair} ${tenor} calculation:`, {
                  //     spotRate,
                  //     forwardPoints,
                  //     pipFactor: pair.includes('JPY') ? 100 : 10000,
                  //     calculation: `${spotRate} + (${forwardPoints} / ${pair.includes('JPY') ? 100 : 10000})`,
                  //     outright,
                  //     expected: spotRate + (forwardPoints / 10000)
                  //   })
                  // }
                  
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
          
          // Filter out invalid points (NaN or null values)
          const validPoints = points.filter(p => 
            p.forward != null && 
            !isNaN(p.forward) && 
            p.points != null && 
            !isNaN(p.points)
          )
          
          // Sort by tenor days
          validPoints.sort((a, b) => a.tenor - b.tenor)
          
          // Debug: Log the data for the first pair
          // if (pair === 'EURUSD' && validPoints.length > 0) {
          //   console.log(`${pair} Forward Data:`, {
          //     spot: spotRate,
          //     firstPoint: validPoints[0],
          //     lastPoint: validPoints[validPoints.length - 1],
          //     allForwards: validPoints.map(p => ({ tenor: p.label, forward: p.forward, points: p.points }))
          //   })
          // }
          
          if (validPoints.length > 0) {
            newForwardData.set(pair, validPoints)
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
                  <span style={{ fontWeight: '600' }}>{point.forward?.toFixed(4) || 'N/A'}</span>
                </div>
                <div style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between',
                  marginBottom: '4px'
                }}>
                  <span style={{ color: currentTheme.textSecondary }}>Points:</span>
                  <span>{point.points?.toFixed(1) || 'N/A'}</span>
                </div>
                {point.bid && point.ask && (
                  <div style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between',
                    marginBottom: '4px',
                    fontSize: '10px'
                  }}>
                    <span style={{ color: currentTheme.textSecondary }}>Bid/Ask:</span>
                    <span>{point.bid?.toFixed(1) || 'N/A'}/{point.ask?.toFixed(1) || 'N/A'}</span>
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

  // Draw chart using D3 with enhanced hover cards
  const drawChart = () => {
    if (!chartContainerRef.current || forwardData.size === 0) return

    // Clear previous chart
    d3.select(chartContainerRef.current).select('svg').remove()
    d3.select(chartContainerRef.current).select('.tooltip').remove()

    // Dimensions - optimize for space usage
    const margin = { top: 30, right: 20, bottom: 120, left: 80 }
    const containerRect = chartContainerRef.current.getBoundingClientRect()
    const width = containerRect.width - margin.left - margin.right
    const height = containerRect.height - margin.top - margin.bottom

    // Create tooltip div
    const tooltip = d3.select(chartContainerRef.current)
      .append('div')
      .attr('class', 'tooltip')
      .style('position', 'absolute')
      .style('visibility', 'hidden')
      .style('background', currentTheme.surface)
      .style('border', `1px solid ${currentTheme.border}`)
      .style('border-radius', '6px')
      .style('padding', '12px')
      .style('font-size', '12px')
      .style('box-shadow', '0 4px 6px rgba(0, 0, 0, 0.1)')
      .style('z-index', '1000')

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

    // Y scale - switch between forward points and forward rates
    let yMin: number
    let yMax: number
    
    if (showForwardPoints) {
      // Show forward points
      const allPoints = Array.from(forwardData.values()).flat().map(d => d.points)
      yMin = Math.min(...allPoints)
      yMax = Math.max(...allPoints)
      
      // Add some padding
      const range = yMax - yMin
      const padding = range * 0.1
      yMin = yMin - padding
      yMax = yMax + padding
    } else {
      // Show forward rates
      const allForwards = Array.from(forwardData.values()).flat().map(d => d.forward)
      const validForwards = allForwards.filter(f => f != null && f > 0 && f < 100) // Most FX rates are under 100
      
      console.log('Y-axis DEBUG:', {
        totalForwards: allForwards.length,
        validForwards: validForwards.length,
        allValues: allForwards.slice(0, 10).map(f => f?.toFixed(6)),
        validValues: validForwards.slice(0, 10).map(f => f?.toFixed(6))
      })
      
      if (validForwards.length > 0) {
        yMin = Math.min(...validForwards)
        yMax = Math.max(...validForwards)
        
        // Expand scale by 2%
        const range = yMax - yMin
        const padding = range * 0.02
        yMin = yMin - padding
        yMax = yMax + padding
      } else {
        yMin = 0.5
        yMax = 2.0
      }
    }
    
    // console.log('Y-axis scale:', { 
    //   yMin, 
    //   yMax, 
    //   totalPoints: fxValidForwards.length,
    //   firstFew: fxValidForwards.slice(0, 5)
    // })
    
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

    // Line generator - switch between points and rates
    const line = d3.line<ForwardPoint>()
      .x(d => xScale(d.years))
      .y(d => yScale(showForwardPoints ? d.points : d.forward))
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
        .style('transition', 'opacity 0.2s ease')
        
      // Add invisible thick line for better hover detection
      g.append('path')
        .datum(points)
        .attr('fill', 'none')
        .attr('stroke', 'transparent')
        .attr('stroke-width', 10)
        .attr('d', line)
        .style('cursor', 'pointer')
        .on('mouseover', function() {
          path.style('opacity', 1).attr('stroke-width', 3)
        })
        .on('mouseout', function() {
          path.style('opacity', 0.9).attr('stroke-width', 2.5)
        })

      // Add points with hover
      const pointGroup = g.selectAll(`.point-${pair.replace('/', '')}`)
        .data(points)
        .enter().append('g')
        .attr('class', `point-${pair.replace('/', '')}`)

      pointGroup.append('circle')
        .attr('cx', d => xScale(d.years))
        .attr('cy', d => yScale(showForwardPoints ? d.points : d.forward))
        .attr('r', 4)
        .attr('fill', color)
        .style('cursor', 'pointer')
        .on('mouseover', function(event, d) {
          // Enlarge the circle
          d3.select(this).attr('r', 6)
          
          // Create card content
          const cardContent = `
            <div style="font-weight: 600; color: ${color}; margin-bottom: 8px; font-size: 14px;">
              ${pair} ${d.label}
            </div>
            <div style="margin-bottom: 6px;">
              <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                <span style="color: ${currentTheme.textSecondary}">Forward Rate:</span>
                <span style="font-weight: 600">${d.forward?.toFixed(4) || 'N/A'}</span>
              </div>
              <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                <span style="color: ${currentTheme.textSecondary}">Forward Points:</span>
                <span>${d.points?.toFixed(1) || 'N/A'}</span>
              </div>
              <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                <span style="color: ${currentTheme.textSecondary}">Spot Rate:</span>
                <span>${d.spot?.toFixed(4) || 'N/A'}</span>
              </div>
              <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                <span style="color: ${currentTheme.textSecondary}">Implied Yield:</span>
                <span>${d.impliedYield?.toFixed(2) || 'N/A'}%</span>
              </div>
              ${d.bid && d.ask ? `
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                  <span style="color: ${currentTheme.textSecondary}">Bid/Ask:</span>
                  <span>${d.bid.toFixed(1)}/${d.ask.toFixed(1)}</span>
                </div>
              ` : ''}
            </div>
            <div style="border-top: 1px solid ${currentTheme.border}; padding-top: 6px; margin-top: 8px;">
              <div style="font-size: 10px; color: ${currentTheme.textSecondary}; margin-bottom: 2px;">
                Bloomberg Terminal Data
              </div>
              <div style="font-size: 10px; color: ${currentTheme.textSecondary}">
                ${d.ticker}
              </div>
              ${d.lastUpdate ? `
                <div style="font-size: 10px; color: ${currentTheme.textSecondary}; margin-top: 2px;">
                  Updated: ${d.lastUpdate}
                </div>
              ` : ''}
            </div>
          `
          
          // Show tooltip
          tooltip
            .html(cardContent)
            .style('visibility', 'visible')
            .style('left', (event.pageX - chartContainerRef.current!.getBoundingClientRect().left + 10) + 'px')
            .style('top', (event.pageY - chartContainerRef.current!.getBoundingClientRect().top - 10) + 'px')
        })
        .on('mouseout', function() {
          // Restore circle size
          d3.select(this).attr('r', 4)
          
          // Hide tooltip
          tooltip.style('visibility', 'hidden')
        })
        .on('mousemove', function(event) {
          // Update tooltip position
          tooltip
            .style('left', (event.pageX - chartContainerRef.current!.getBoundingClientRect().left + 10) + 'px')
            .style('top', (event.pageY - chartContainerRef.current!.getBoundingClientRect().top - 10) + 'px')
        })
    })

    // Horizontal Legend at bottom
    if (showLegend) {
      const legend = svg.append('g')
        .attr('transform', `translate(${margin.left}, ${height + margin.top + 35})`)

      let xOffset = 0
      const itemWidth = Math.min(150, width / forwardData.size)
      
      forwardData.forEach((points, pair) => {
        const color = getPairColor(pair)
        
        const legendItem = legend.append('g')
          .attr('transform', `translate(${xOffset}, 0)`)

        // Color circle (smaller)
        legendItem.append('circle')
          .attr('cx', 6)
          .attr('cy', 8)
          .attr('r', 4)
          .attr('fill', color)

        // Label
        legendItem.append('text')
          .attr('x', 16)
          .attr('y', 12)
          .text(pair)
          .style('font-size', '12px')
          .style('fill', currentTheme.text)
          .style('font-weight', '600')

        // Latest value
        const latestPoint = points[points.length - 1]
        if (latestPoint) {
          const displayValue = showForwardPoints ? latestPoint.points : latestPoint.forward
          legendItem.append('text')
            .attr('x', 16)
            .attr('y', 26)
            .text(`${latestPoint.label}: ${displayValue?.toFixed(showForwardPoints ? 1 : 4) || 'N/A'}`)
            .style('font-size', '10px')
            .style('fill', currentTheme.textSecondary)
        }

        xOffset += itemWidth
      })
    }

    // Title
    svg.append('text')
      .attr('x', margin.left + width / 2)
      .attr('y', 12)
      .attr('text-anchor', 'middle')
      .style('font-size', '14px')
      .style('font-weight', '600')
      .style('fill', currentTheme.text)
      .text(showForwardPoints ? 'FX Forward Points' : 'FX Forward Rates')

    // Axis labels
    svg.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('y', 20)
      .attr('x', 0 - (height / 2 + margin.top))
      .attr('dy', '1em')
      .style('text-anchor', 'middle')
      .style('fill', currentTheme.text)
      .style('font-size', '14px')
      .text(showForwardPoints ? 'Forward Points (Pips)' : 'Forward Rate')

    svg.append('text')
      .attr('transform', `translate(${width / 2 + margin.left}, ${height + margin.top + 40})`)
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
  }, [forwardData, currentTheme, showGrid, showLegend, displayMode, showForwardPoints])

  useEffect(() => {
    let resizeTimeout: NodeJS.Timeout
    const handleResize = () => {
      // Debounce resize events to avoid excessive redraws
      clearTimeout(resizeTimeout)
      resizeTimeout = setTimeout(() => {
        if (displayMode === 'chart' && forwardData.size > 0) {
          drawChart()
        }
      }, 200) // 200ms debounce
    }
    
    // Listen to window resize events
    window.addEventListener('resize', handleResize)
    return () => {
      window.removeEventListener('resize', handleResize)
      clearTimeout(resizeTimeout)
    }
  }, [forwardData, displayMode, showForwardPoints])

  // Separate effect to handle chart redraw when selector expands/collapses
  useEffect(() => {
    let layoutTimeout: NodeJS.Timeout
    if (displayMode === 'chart' && forwardData.size > 0) {
      // Small delay to allow DOM to update after selector state change
      layoutTimeout = setTimeout(() => {
        drawChart()
      }, 100)
    }
    return () => clearTimeout(layoutTimeout)
  }, [expandedSelector, displayMode, forwardData.size, showForwardPoints])

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
            <td style={{ padding: '8px', textAlign: 'right' }}>{point.forward?.toFixed(4) || 'N/A'}</td>
            <td style={{ padding: '8px', textAlign: 'right' }}>{point.points?.toFixed(1) || 'N/A'}</td>
            <td style={{ padding: '8px', textAlign: 'right' }}>{point.impliedYield?.toFixed(2) || 'N/A'}%</td>
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
          <span style={{ fontSize: '12px', fontWeight: '600', color: currentTheme.text }}>
            FX Forward Curves
          </span>
        </div>

        <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
          {/* Chart controls only */}
          <button
            onClick={() => setShowForwardPoints(!showForwardPoints)}
            style={{
              padding: '2px 8px',
              backgroundColor: currentTheme.surface,
              color: currentTheme.text,
              border: `1px solid ${currentTheme.border}`,
              borderRadius: '3px',
              cursor: 'pointer',
              fontSize: '11px'
            }}
          >
            {showForwardPoints ? 'Show Rates' : 'Show Points'}
          </button>
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

      {/* Currency Pair Selector - Organized by Category */}
      <div style={{
        borderBottom: `1px solid ${currentTheme.border}`,
        backgroundColor: currentTheme.background,
      }}>
        <div style={{
          padding: '8px 16px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          cursor: 'pointer',
          userSelect: 'none'
        }}
        onClick={() => setExpandedSelector(!expandedSelector)}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '12px', fontWeight: '600', color: currentTheme.text }}>Currency Pairs</span>
            <span style={{ fontSize: '10px', color: currentTheme.textSecondary }}>
              ({selectedPairs.size} selected)
            </span>
          </div>
          <svg
            width="14"
            height="14"
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
          <div style={{ padding: '0 16px 12px' }}>
            {/* G10 USD Pairs */}
            <div style={{ marginBottom: '10px' }}>
              <div style={{ fontSize: '10px', color: currentTheme.textSecondary, marginBottom: '4px', fontWeight: '600' }}>
                G10 USD Pairs
              </div>
              <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                {G10_USD_PAIRS.map(pair => (
                  <button
                    key={pair}
                    onClick={() => togglePair(pair)}
                    style={{
                      padding: '2px 6px',
                      backgroundColor: selectedPairs.has(pair) ? getPairColor(pair) : currentTheme.surface,
                      color: selectedPairs.has(pair) ? '#ffffff' : currentTheme.textSecondary,
                      border: `1px solid ${selectedPairs.has(pair) ? getPairColor(pair) : currentTheme.border}`,
                      borderRadius: '3px',
                      cursor: 'pointer',
                      fontSize: '9px',
                      fontWeight: selectedPairs.has(pair) ? '600' : '400',
                      transition: 'all 0.2s ease'
                    }}
                  >
                    {pair}
                  </button>
                ))}
              </div>
            </div>

            {/* EM USD Pairs */}
            <div style={{ marginBottom: '10px' }}>
              <div style={{ fontSize: '10px', color: currentTheme.textSecondary, marginBottom: '4px', fontWeight: '600' }}>
                EM USD Pairs
              </div>
              <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                {EM_USD_PAIRS.map(pair => (
                  <button
                    key={pair}
                    onClick={() => togglePair(pair)}
                    style={{
                      padding: '2px 6px',
                      backgroundColor: selectedPairs.has(pair) ? getPairColor(pair) : currentTheme.surface,
                      color: selectedPairs.has(pair) ? '#ffffff' : currentTheme.textSecondary,
                      border: `1px solid ${selectedPairs.has(pair) ? getPairColor(pair) : currentTheme.border}`,
                      borderRadius: '3px',
                      cursor: 'pointer',
                      fontSize: '9px',
                      fontWeight: selectedPairs.has(pair) ? '600' : '400',
                      transition: 'all 0.2s ease'
                    }}
                  >
                    {pair}
                  </button>
                ))}
              </div>
            </div>

            {/* EUR Crosses */}
            <div style={{ marginBottom: '10px' }}>
              <div style={{ fontSize: '10px', color: currentTheme.textSecondary, marginBottom: '4px', fontWeight: '600' }}>
                EUR Crosses
              </div>
              <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                {EUR_CROSSES.map(pair => (
                  <button
                    key={pair}
                    onClick={() => togglePair(pair)}
                    style={{
                      padding: '2px 6px',
                      backgroundColor: selectedPairs.has(pair) ? getPairColor(pair) : currentTheme.surface,
                      color: selectedPairs.has(pair) ? '#ffffff' : currentTheme.textSecondary,
                      border: `1px solid ${selectedPairs.has(pair) ? getPairColor(pair) : currentTheme.border}`,
                      borderRadius: '3px',
                      cursor: 'pointer',
                      fontSize: '9px',
                      fontWeight: selectedPairs.has(pair) ? '600' : '400',
                      transition: 'all 0.2s ease'
                    }}
                  >
                    {pair}
                  </button>
                ))}
              </div>
            </div>

            {/* GBP Crosses */}
            <div style={{ marginBottom: '10px' }}>
              <div style={{ fontSize: '10px', color: currentTheme.textSecondary, marginBottom: '4px', fontWeight: '600' }}>
                GBP Crosses
              </div>
              <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                {GBP_CROSSES.map(pair => (
                  <button
                    key={pair}
                    onClick={() => togglePair(pair)}
                    style={{
                      padding: '2px 6px',
                      backgroundColor: selectedPairs.has(pair) ? getPairColor(pair) : currentTheme.surface,
                      color: selectedPairs.has(pair) ? '#ffffff' : currentTheme.textSecondary,
                      border: `1px solid ${selectedPairs.has(pair) ? getPairColor(pair) : currentTheme.border}`,
                      borderRadius: '3px',
                      cursor: 'pointer',
                      fontSize: '9px',
                      fontWeight: selectedPairs.has(pair) ? '600' : '400',
                      transition: 'all 0.2s ease'
                    }}
                  >
                    {pair}
                  </button>
                ))}
              </div>
            </div>

            {/* Metals */}
            <div>
              <div style={{ fontSize: '10px', color: currentTheme.textSecondary, marginBottom: '4px', fontWeight: '600' }}>
                Metals
              </div>
              <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                {METAL_PAIRS.map(pair => (
                  <button
                    key={pair}
                    onClick={() => togglePair(pair)}
                    style={{
                      padding: '2px 6px',
                      backgroundColor: selectedPairs.has(pair) ? getPairColor(pair) : currentTheme.surface,
                      color: selectedPairs.has(pair) ? '#ffffff' : currentTheme.textSecondary,
                      border: `1px solid ${selectedPairs.has(pair) ? getPairColor(pair) : currentTheme.border}`,
                      borderRadius: '3px',
                      cursor: 'pointer',
                      fontSize: '9px',
                      fontWeight: selectedPairs.has(pair) ? '600' : '400',
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

      {/* Main Content Container - Dynamic height with resize protection */}
      <div style={{ flex: 1, minHeight: '400px', overflow: 'hidden', position: 'relative' }}>
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
          <div ref={chartContainerRef} style={{ width: '100%', height: '100%' }} />
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