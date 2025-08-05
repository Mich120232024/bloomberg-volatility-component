import { useState, useEffect, useRef } from 'react'
import { useTheme } from '../contexts/ThemeContext'
import * as d3 from 'd3'
import { FXPair, G10_USD_PAIRS, EM_USD_PAIRS, METAL_PAIRS, EUR_CROSSES, GBP_CROSSES } from '../constants/currencies'
import { NDF_MAPPINGS, usesNDF, getNDFTicker } from '../constants/ndfMappings'

type CurrencyPair = FXPair

interface ForwardPoint {
  tenor: number     // Days to maturity
  years: number     // Years to maturity for proper scaling
  spot: number      // Spot rate
  forward: number   // Forward rate (outright)
  points: number    // Forward points (pips)
  impliedYield: number // Implied yield differential
  label: string     // Display label (1W, 1M, etc.)
  ticker: string    // Bloomberg ticker
  bid?: number      // Bid rate
  ask?: number      // Ask rate
  lastUpdate?: string // Bloomberg last update timestamp
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
  const [showGrid, setShowGrid] = useState(true)
  const [showLegend, setShowLegend] = useState(true)
  const [expandedSelector, setExpandedSelector] = useState(false)
  const [showForwardPoints, setShowForwardPoints] = useState(false) // Start with rates view
  
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
      EURUSD: '#1976D2', GBPUSD: '#D32F2F', USDJPY: '#7B1FA2', USDCHF: '#F57C00',
      AUDUSD: '#388E3C', USDCAD: '#E91E63', NZDUSD: '#00ACC1', USDNOK: '#795548',
      USDSEK: '#607D8B', USDSGD: '#FF5722',
      // EM USD Pairs
      USDBRL: '#9C27B0', USDMXN: '#3F51B5', USDCNH: '#009688', USDKRW: '#8BC34A',
      USDINR: '#FF9800', USDTRY: '#673AB7', USDCZK: '#4CAF50', USDHUF: '#2196F3',
      USDPLN: '#FFC107', USDRON: '#9E9E9E', USDZAR: '#CDDC39', USDTHB: '#FF6722',
      USDPHP: '#795548',
      // EUR Crosses
      EURGBP: '#E91E63', EURJPY: '#9C27B0', EURCHF: '#FF5722', EURAUD: '#4CAF50',
      EURCAD: '#2196F3', EURNZD: '#FF9800', EURNOK: '#607D8B', EURSEK: '#8BC34A',
      EURSGD: '#795548', EURCZK: '#FFC107', EURHUF: '#9E9E9E', EURPLN: '#CDDC39',
      EURTRY: '#673AB7', EURZAR: '#3F51B5',
      // GBP Crosses
      GBPJPY: '#7B1FA2', GBPCHF: '#009688', GBPAUD: '#8BC34A', GBPCAD: '#FF5722',
      GBPNZD: '#4CAF50', GBPNOK: '#2196F3', GBPSEK: '#FF9800', GBPSGD: '#795548',
      // Metals
      XAGUSD: '#9E9E9E', XAUUSD: '#FFC107'
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
      const tenors = ['1W', '2W', '1M', '2M', '3M', '6M', '9M', '1Y', '18M', '2Y', '3Y', '4Y', '5Y']
      const tenorDays: Record<string, number> = {
        '1W': 7, '2W': 14, '1M': 30, '2M': 60, '3M': 90, '6M': 180, '9M': 270,
        '1Y': 365, '18M': 545, '2Y': 730, '3Y': 1095, '4Y': 1460, '5Y': 1825
      }
      
      // Process each selected pair
      for (const pair of selectedPairs) {
        // Check if this pair needs NDF tickers
        const needsNDF = usesNDF(pair)
        const ndfMapping = NDF_MAPPINGS[pair]
        
        // Build list of all tickers we need
        const securities: string[] = [`${pair} Curncy`] // Always include spot
        
        if (needsNDF && ndfMapping?.format) {
          // Use NDF tickers for this currency
          console.log(`🔄 Using NDF tickers for ${pair} (${ndfMapping.format} format)`)
          console.log(`📊 NDF Coverage: ${ndfMapping.coverage}`)
          
          // Only add tenors that are within the NDF coverage
          for (const tenor of tenors) {
            const ndfTicker = getNDFTicker(pair, tenor)
            if (ndfTicker) {
              securities.push(ndfTicker)
            }
          }
        } else {
          // Use standard forward tickers
          securities.push(...tenors.map(tenor => `${pair}${tenor} Curncy`))
        }
        
        console.log(`📡 Fetching data for ${pair}:`)
        console.log(`   Spot ticker: ${securities[0]}`)
        console.log(`   Forward tickers (first 5):`, securities.slice(1, 6))
        console.log(`   Total tickers: ${securities.length}`)
        
        // Call generic Bloomberg reference endpoint
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
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }
        
        const result = await response.json()
        console.log(`${pair} API Response:`, result)
        
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
            if (secData.success && secData.fields && typeof secData.fields.PX_LAST === 'number') {
              const ticker = secData.security
              if (ticker === `${pair} Curncy`) {
                spotRate = secData.fields.PX_LAST
                spotLastUpdate = secData.fields.LAST_UPDATE || ''
                console.log(`${pair} spot rate:`, spotRate)
                break
              }
            }
          }
          
          if (spotRate <= 0) {
            console.warn(`No valid spot rate found for ${pair}`)
            continue
          }
          
          // Add spot point
          points.push({
            tenor: 0,
            years: 0,
            spot: spotRate,
            forward: spotRate,
            points: 0,
            impliedYield: 0,
            label: 'Spot',
            ticker: `${pair} Curncy`,
            lastUpdate: spotLastUpdate
          })
          
          // Second pass: process forward rates
          for (const secData of result.data.securities_data as BloombergResponse[]) {
            if (secData.success && secData.fields && typeof secData.fields.PX_LAST === 'number') {
              const ticker = secData.security
              const value = secData.fields.PX_LAST
              const bid = secData.fields.PX_BID
              const ask = secData.fields.PX_ASK
              const lastUpdate = secData.fields.LAST_UPDATE
              
              // Skip spot rate (already processed)
              if (ticker === `${pair} Curncy`) continue
              
              // Match forward tickers - both standard and NDF formats
              let tenorMatch = ticker.match(new RegExp(`${pair}(\\d+[WMY]) Curncy`))
              let tenor: string | null = null
              
              if (tenorMatch) {
                // Standard forward ticker
                tenor = tenorMatch[1]
              } else if (needsNDF && ndfMapping?.format) {
                // NDF ticker format
                const ndfMatch = ticker.match(new RegExp(`${ndfMapping.format}(\\d+[WMY]) Curncy`))
                if (ndfMatch) {
                  tenor = ndfMatch[1]
                  console.log(`✅ Matched NDF ticker: ${ticker} -> tenor: ${tenor}`)
                }
              }
              
              if (tenor && spotRate > 0) {
                const days = tenorDays[tenor]
                if (!days) {
                  console.warn(`Unknown tenor: ${tenor}`)
                  continue
                }
                
                const years = days / 365.25
                
                // Bloomberg returns forward points, not outright forward rates
                const forwardPoints = value
                
                // Calculate outright forward rate: Spot + (Forward Points / Pip Factor)
                let forwardRate: number
                if (pair.includes('JPY')) {
                  forwardRate = spotRate + (forwardPoints / 100)
                } else {
                  forwardRate = spotRate + (forwardPoints / 10000)
                }
                
                // Calculate implied yield differential
                const impliedYield = years > 0 ? ((forwardRate / spotRate) ** (1 / years) - 1) * 100 : 0
                
                // Log for debugging
                if (pair === 'EURUSD' && ['1M', '1Y', '5Y'].includes(tenor)) {
                  console.log(`${pair} ${tenor} calculation:`, {
                    ticker,
                    bloombergForwardPoints: value,
                    spotRate: spotRate.toFixed(6),
                    calculatedForwardRate: forwardRate.toFixed(6),
                    forwardPoints: forwardPoints.toFixed(1),
                    impliedYield: impliedYield.toFixed(2) + '%'
                  })
                }
                
                points.push({
                  tenor: days,
                  years: years,
                  spot: spotRate,
                  forward: forwardRate,
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
          
          // Filter out invalid points and sort by tenor
          const validPoints = points
            .filter(p => p.forward > 0 && !isNaN(p.forward) && !isNaN(p.points))
            .sort((a, b) => a.tenor - b.tenor)
          
          console.log(`${pair} processed points:`, validPoints.length, 'valid out of', points.length)
          if (validPoints.length === 0) {
            console.warn(`${pair}: No valid forward points found. Available tenors may be limited.`)
          } else if (validPoints.length === 1 && validPoints[0].label === 'Spot') {
            console.warn(`${pair}: Only spot rate available, no forward data`)
          }
          
          if (validPoints.length > 0) {
            newForwardData.set(pair, validPoints)
          }
        }
      }
      
      setForwardData(newForwardData)
      setLastUpdate(new Date())
      console.log('Final forward data:', newForwardData)
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch forward data'
      setError(errorMessage)
      console.error('Forward data fetch error:', err)
    } finally {
      setLoading(false)
    }
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
      .style('color', currentTheme.text)
      .style('border', `1px solid ${currentTheme.border}`)
      .style('border-radius', '6px')
      .style('padding', '10px')
      .style('font-size', '11px')
      .style('box-shadow', '0 2px 8px rgba(0, 0, 0, 0.15)')
      .style('z-index', '9999')
      .style('pointer-events', 'none')
      .style('max-width', '280px')
      .style('font-family', 'system-ui, -apple-system, sans-serif')

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
      const allPoints = Array.from(forwardData.values()).flat().map(d => d.points).filter(p => !isNaN(p))
      if (allPoints.length > 0) {
        yMin = Math.min(...allPoints)
        yMax = Math.max(...allPoints)
        // Add padding
        const range = yMax - yMin
        const padding = Math.max(range * 0.1, 10) // Minimum 10 pips padding
        yMin = yMin - padding
        yMax = yMax + padding
      } else {
        yMin = -100
        yMax = 500
      }
    } else {
      // Show forward rates
      const allForwards = Array.from(forwardData.values()).flat().map(d => d.forward).filter(f => f > 0 && f < 1000)
      if (allForwards.length > 0) {
        yMin = Math.min(...allForwards)
        yMax = Math.max(...allForwards)
        // Add 2% padding
        const range = yMax - yMin
        const padding = range * 0.02
        yMin = yMin - padding
        yMax = yMax + padding
      } else {
        yMin = 0.5
        yMax = 2.0
      }
    }
    
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
        .tickFormat(d => showForwardPoints ? `${(d as number).toFixed(0)}` : `${(d as number).toFixed(4)}`)
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
        .attr('stroke-width', 1.2)
        .attr('d', line)
        .style('opacity', 0.9)

      // Add points with hover
      const pointGroup = g.selectAll(`.point-${pair.replace('/', '')}`)
        .data(points)
        .enter().append('g')
        .attr('class', `point-${pair.replace('/', '')}`)

      // Add invisible hover area
      pointGroup.append('circle')
        .attr('cx', d => xScale(d.years))
        .attr('cy', d => yScale(showForwardPoints ? d.points : d.forward))
        .attr('r', 10)  // Large invisible hover area
        .attr('fill', 'transparent')
        .style('cursor', 'pointer')
        
      // Add visible point
      const visiblePoint = pointGroup.append('circle')
        .attr('cx', d => xScale(d.years))
        .attr('cy', d => yScale(showForwardPoints ? d.points : d.forward))
        .attr('r', 2)
        .attr('fill', color)
        .style('opacity', 0.7)
        .style('pointer-events', 'none')  // Let hover area handle events
        
      // Handle hover on the invisible area
      pointGroup.select('circle:first-child')
        .on('mouseenter', function(event, d) {
          console.log(`Hover on ${pair} ${d.label}:`, {
            spot: d.spot,
            forward: d.forward,
            points: d.points,
            years: d.years
          })
          
          // Enlarge visible point
          d3.select(this.parentNode).select('circle:nth-child(2)')
            .transition()
            .duration(150)
            .attr('r', 3.5)
            .style('opacity', 1)
          
          // Calculate FX net rate (forward - spot in percentage terms)
          const fxNetRate = d.spot > 0 ? ((d.forward - d.spot) / d.spot) * 100 : 0
          
          // Create enhanced card content
          const cardContent = `
            <div style="font-weight: 700; color: ${color}; margin-bottom: 10px; font-size: 15px; text-align: center;">
              ${pair} ${d.label}
            </div>
            <div style="margin-bottom: 8px;">
              <div style="display: flex; justify-content: space-between; margin-bottom: 6px; padding: 4px; background: ${currentTheme.background}; border-radius: 4px;">
                <span style="color: ${currentTheme.textSecondary}; font-weight: 600;">Spot Rate:</span>
                <span style="font-weight: 700; font-size: 13px;">${d.spot?.toFixed(4) || 'N/A'}</span>
              </div>
              <div style="display: flex; justify-content: space-between; margin-bottom: 6px; padding: 4px; background: ${currentTheme.background}; border-radius: 4px;">
                <span style="color: ${currentTheme.textSecondary}; font-weight: 600;">Forward Rate:</span>
                <span style="font-weight: 700; font-size: 13px; color: ${color};">${d.forward?.toFixed(4) || 'N/A'}</span>
              </div>
              <div style="display: flex; justify-content: space-between; margin-bottom: 6px; padding: 4px; background: ${currentTheme.background}; border-radius: 4px;">
                <span style="color: ${currentTheme.textSecondary}; font-weight: 600;">FX Net Rate:</span>
                <span style="font-weight: 700; font-size: 13px; color: ${fxNetRate >= 0 ? '#10B981' : '#EF4444'};">${fxNetRate?.toFixed(3) || 'N/A'}%</span>
              </div>
              <div style="border-top: 1px solid ${currentTheme.border}; margin: 8px 0; padding-top: 6px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                  <span style="color: ${currentTheme.textSecondary}; font-size: 12px;">Forward Points:</span>
                  <span style="font-size: 12px;">${d.points?.toFixed(1) || 'N/A'}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                  <span style="color: ${currentTheme.textSecondary}; font-size: 12px;">Implied Yield:</span>
                  <span style="font-size: 12px;">${d.impliedYield?.toFixed(2) || 'N/A'}%</span>
                </div>
                ${d.bid && d.ask ? `
                  <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span style="color: ${currentTheme.textSecondary}; font-size: 12px;">Bid/Ask:</span>
                    <span style="font-size: 12px;">${d.bid.toFixed(4)}/${d.ask.toFixed(4)}</span>
                  </div>
                ` : ''}
              </div>
            </div>
            <div style="border-top: 1px solid ${currentTheme.border}; padding-top: 6px; margin-top: 8px;">
              <div style="font-size: 10px; color: ${currentTheme.textSecondary}; margin-bottom: 2px; text-align: center;">
                Bloomberg Terminal Data
              </div>
              <div style="font-size: 10px; color: ${currentTheme.textSecondary}; text-align: center;">
                ${d.ticker}
              </div>
              ${d.lastUpdate ? `
                <div style="font-size: 10px; color: ${currentTheme.textSecondary}; margin-top: 2px; text-align: center;">
                  Updated: ${d.lastUpdate}
                </div>
              ` : ''}
            </div>
          `
          
          // Show tooltip with smart positioning
          const rect = chartContainerRef.current!.getBoundingClientRect()
          const mouseX = event.pageX - rect.left
          const mouseY = event.pageY - rect.top
          
          // Position tooltip to avoid edges
          const tooltipX = mouseX + 15 > width - 200 ? mouseX - 215 : mouseX + 15
          const tooltipY = mouseY - 20 < 0 ? mouseY + 20 : mouseY - 20
          
          tooltip
            .html(cardContent)
            .style('visibility', 'visible')
            .style('opacity', '1')
            .style('left', tooltipX + 'px')
            .style('top', tooltipY + 'px')
            .raise()  // Bring to front
        })
        .on('mouseleave', function() {
          // Restore visible point to normal size
          d3.select(this.parentNode).select('circle:nth-child(2)')
            .transition()
            .duration(150)
            .attr('r', 2)
            .style('opacity', 0.7)
          
          // Hide tooltip
          tooltip.style('visibility', 'hidden')
        })
        .on('mousemove', function(event) {
          // Update tooltip position with smart positioning
          const rect = chartContainerRef.current!.getBoundingClientRect()
          const mouseX = event.pageX - rect.left
          const mouseY = event.pageY - rect.top
          
          const tooltipX = mouseX + 15 > width - 200 ? mouseX - 215 : mouseX + 15
          const tooltipY = mouseY - 20 < 0 ? mouseY + 20 : mouseY - 20
          
          tooltip
            .style('left', tooltipX + 'px')
            .style('top', tooltipY + 'px')
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

        // Color circle
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
      .attr('y', 20)
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
    if (forwardData.size > 0) {
      drawChart()
    }
  }, [forwardData, currentTheme, showGrid, showLegend, showForwardPoints])

  useEffect(() => {
    let resizeTimeout: NodeJS.Timeout
    const handleResize = () => {
      clearTimeout(resizeTimeout)
      resizeTimeout = setTimeout(() => {
        if (forwardData.size > 0) {
          drawChart()
        }
      }, 200)
    }
    
    window.addEventListener('resize', handleResize)
    return () => {
      window.removeEventListener('resize', handleResize)
      clearTimeout(resizeTimeout)
    }
  }, [forwardData, showForwardPoints])

  // Separate effect to handle chart redraw when selector expands/collapses
  useEffect(() => {
    let layoutTimeout: NodeJS.Timeout
    if (forwardData.size > 0) {
      layoutTimeout = setTimeout(() => {
        drawChart()
      }, 100)
    }
    return () => clearTimeout(layoutTimeout)
  }, [expandedSelector, forwardData.size, showForwardPoints])

  const togglePair = (pair: CurrencyPair) => {
    const newSet = new Set(selectedPairs)
    if (newSet.has(pair)) {
      newSet.delete(pair)
    } else {
      newSet.add(pair)
    }
    setSelectedPairs(newSet)
  }

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
          <div ref={chartContainerRef} style={{ width: '100%', height: '100%', position: 'relative' }} />
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