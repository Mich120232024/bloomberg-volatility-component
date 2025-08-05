import { useState, useEffect, useRef } from 'react'
import { useTheme } from '../contexts/ThemeContext'
import * as d3 from 'd3'
import { 
  getYieldCurveConfig, 
  getCurrencyTitle,
  G10_CURRENCIES,
  EM_CURRENCIES
} from '../services/yieldCurveDatabaseService'

interface CurvePoint {
  tenor: number     // Days to maturity
  years: number     // Years to maturity for proper scaling
  rate: number      // Yield rate
  label: string     // Display label (1M, 1Y, etc.)
  ticker: string    // Bloomberg ticker
  type: 'money_market' | 'ois' | 'government_bond' | 'swap'
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

export function YieldCurvesTab() {
  const { currentTheme } = useTheme()
  const chartContainerRef = useRef<HTMLDivElement>(null)
  
  // Controls
  const [selectedCurrencies, setSelectedCurrencies] = useState<Set<string>>(new Set(['USD', 'EUR']))
  const [showGrid, setShowGrid] = useState(true)
  const [showLegend, setShowLegend] = useState(true)
  const [expandedSelector, setExpandedSelector] = useState(false)
  
  // Data
  const [curveData, setCurveData] = useState<Map<string, CurvePoint[]>>(new Map())
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)
  const [dataSource, setDataSource] = useState<string>('')

  // Professional color palette matching FX Forward Curves
  const getCurrencyColor = (currency: string): string => {
    const colors: Record<string, string> = {
      // G10
      USD: '#1976D2', // Blue
      EUR: '#D32F2F', // Red  
      GBP: '#7B1FA2', // Purple
      JPY: '#F57C00', // Orange
      CHF: '#388E3C', // Green
      CAD: '#512DA8', // Deep Purple
      AUD: '#00897B', // Teal
      NZD: '#6A4C93', // Violet
      // EM
      SGD: '#E91E63', // Pink
      BRL: '#795548', // Brown
      TRY: '#FF5722', // Deep Orange
      CZK: '#00ACC1', // Cyan
      PLN: '#4CAF50', // Light Green
      HUF: '#FFC107'  // Amber
    }
    return colors[currency] || '#757575'
  }

  // Fetch yield curve data using generic Bloomberg reference endpoint
  const fetchCurveData = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const apiUrl = import.meta.env.DEV ? 'http://localhost:8000' : 'http://20.172.249.92:8080'
      const newCurveData = new Map<string, CurvePoint[]>()
      
      // Process each selected currency
      for (const currency of selectedCurrencies) {
        const config = getYieldCurveConfig(currency)
        if (!config) continue
        
        // Build list of all tickers we need
        const securities = config.instruments.map(inst => inst.ticker)
        
        // Fetch data from Bloomberg
        const response = await fetch(`${apiUrl}/api/bloomberg/reference`, {
          method: 'POST',
          headers: {
            'Authorization': 'Bearer test',
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            securities: securities,
            fields: ['PX_LAST', 'PX_BID', 'PX_ASK', 'LAST_UPDATE']
          })
        })
        
        if (!response.ok) {
          throw new Error(`Bloomberg API error: ${response.status}`)
        }
        
        const data = await response.json()
        console.log(`[${currency}] Bloomberg response:`, data)
        
        if (data.success && data.data) {
          const points: CurvePoint[] = []
          const securities_data = data.data.securities_data || []
          
          securities_data.forEach((item: BloombergResponse, index: number) => {
            if (item.success && item.fields?.PX_LAST !== undefined) {
              const instrument = config.instruments[index]
              if (!instrument) return
              
              const tenorToYears = (days: number): number => days / 365
              
              points.push({
                tenor: instrument.tenor,
                years: tenorToYears(instrument.tenor),
                rate: item.fields.PX_LAST,
                label: instrument.label,
                ticker: instrument.ticker,
                type: instrument.type,
                bid: item.fields.PX_BID,
                ask: item.fields.PX_ASK,
                lastUpdate: item.fields.LAST_UPDATE
              })
            }
          })
          
          // Sort by tenor
          points.sort((a, b) => a.tenor - b.tenor)
          
          if (points.length > 0) {
            newCurveData.set(currency, points)
            console.log(`[${currency}] Found ${points.length} valid points`)
          }
        }
      }
      
      setCurveData(newCurveData)
      setLastUpdate(new Date())
      setDataSource(newCurveData.size > 0 ? 'Bloomberg Terminal' : '')
    } catch (error) {
      console.error('Failed to fetch curve data:', error)
      setError(error instanceof Error ? error.message : 'Failed to fetch yield curves')
    } finally {
      setLoading(false)
    }
  }

  // D3.js chart rendering (simplified version matching FX Forward Curves style)
  const drawChart = () => {
    if (!chartContainerRef.current || curveData.size === 0) return

    // Clear previous chart
    d3.select(chartContainerRef.current).selectAll("*").remove()

    const margin = { top: 20, right: showLegend ? 120 : 50, bottom: 50, left: 60 }
    const width = chartContainerRef.current.clientWidth - margin.left - margin.right
    const height = chartContainerRef.current.clientHeight - margin.top - margin.bottom

    if (width <= 0 || height <= 0) return

    const svg = d3.select(chartContainerRef.current)
      .append("svg")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)

    const g = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`)

    // Find data ranges
    const allPoints: CurvePoint[] = []
    curveData.forEach(points => {
      allPoints.push(...points)
    })

    if (allPoints.length === 0) return

    // X scale - years
    const xExtent = d3.extent(allPoints, d => d.years) as [number, number]
    const xScale = d3.scaleLinear()
      .domain([0, Math.max(xExtent[1], 30)])
      .range([0, width])

    // Y scale - rates
    const yExtent = d3.extent(allPoints, d => d.rate) as [number, number]
    const yScale = d3.scaleLinear()
      .domain([Math.min(0, yExtent[0] - 0.5), yExtent[1] + 0.5])
      .range([height, 0])

    // Grid lines
    if (showGrid) {
      // X grid
      g.append("g")
        .attr("class", "grid")
        .attr("transform", `translate(0,${height})`)
        .call(d3.axisBottom(xScale)
          .tickSize(-height)
          .tickFormat(() => "")
        )
        .style("stroke-dasharray", "3,3")
        .style("opacity", 0.3)
        .style("stroke", currentTheme.border)

      // Y grid
      g.append("g")
        .attr("class", "grid")
        .call(d3.axisLeft(yScale)
          .tickSize(-width)
          .tickFormat(() => "")
        )
        .style("stroke-dasharray", "3,3")
        .style("opacity", 0.3)
        .style("stroke", currentTheme.border)
    }

    // Line generator
    const line = d3.line<CurvePoint>()
      .x(d => xScale(d.years))
      .y(d => yScale(d.rate))
      .curve(d3.curveCatmullRom.alpha(0.5))

    // Enhanced tooltip
    const tooltip = d3.select("body").append("div")
      .attr("class", "yield-tooltip")
      .style("opacity", 0)
      .style("position", "absolute")
      .style("background", currentTheme.surface)
      .style("border", `1px solid ${currentTheme.border}`)
      .style("border-radius", "6px")
      .style("padding", "10px")
      .style("font-size", "11px")
      .style("color", currentTheme.text)
      .style("pointer-events", "none")
      .style("box-shadow", "0 2px 8px rgba(0,0,0,0.15)")

    // Draw curves
    curveData.forEach((points, currency) => {
      const color = getCurrencyColor(currency)

      // Line
      g.append("path")
        .datum(points)
        .attr("fill", "none")
        .attr("stroke", color)
        .attr("stroke-width", 2)
        .attr("d", line)
        .style("opacity", 0.9)

      // Points with hover
      g.selectAll(`.point-${currency}`)
        .data(points)
        .enter().append("circle")
        .attr("cx", d => xScale(d.years))
        .attr("cy", d => yScale(d.rate))
        .attr("r", 4)
        .attr("fill", currentTheme.background)
        .attr("stroke", color)
        .attr("stroke-width", 2)
        .style("cursor", "pointer")
        .on("mouseover", function(event, d) {
          tooltip.transition()
            .duration(200)
            .style("opacity", .95)
          
          const typeLabel = {
            'money_market': 'Money Market',
            'ois': 'OIS Swap',
            'government_bond': 'Gov Bond',
            'swap': 'Swap'
          }[d.type] || d.type

          tooltip.html(`
            <div style="font-weight: 600; margin-bottom: 6px; color: ${color}">
              ${getCurrencyTitle(currency)} - ${d.label}
            </div>
            <div style="display: flex; justify-content: space-between; gap: 20px;">
              <span style="color: ${currentTheme.textSecondary}">Rate:</span>
              <span style="font-weight: 500">${d.rate.toFixed(3)}%</span>
            </div>
            ${d.bid !== undefined ? `
              <div style="display: flex; justify-content: space-between; gap: 20px;">
                <span style="color: ${currentTheme.textSecondary}">Bid/Ask:</span>
                <span style="font-size: 10px">${d.bid.toFixed(3)}% / ${d.ask?.toFixed(3)}%</span>
              </div>
            ` : ''}
            <div style="display: flex; justify-content: space-between; gap: 20px; margin-top: 4px; padding-top: 4px; border-top: 1px solid ${currentTheme.border}">
              <span style="color: ${currentTheme.textSecondary}; font-size: 10px">Type:</span>
              <span style="font-size: 10px">${typeLabel}</span>
            </div>
            <div style="display: flex; justify-content: space-between; gap: 20px;">
              <span style="color: ${currentTheme.textSecondary}; font-size: 10px">Ticker:</span>
              <span style="font-size: 10px; font-family: monospace">${d.ticker}</span>
            </div>
          `)
            .style("left", (event.pageX + 15) + "px")
            .style("top", (event.pageY - 40) + "px")
        })
        .on("mouseout", function() {
          tooltip.transition()
            .duration(500)
            .style("opacity", 0)
        })
    })

    // X-axis
    g.append("g")
      .attr("transform", `translate(0,${height})`)
      .call(d3.axisBottom(xScale)
        .tickFormat(d => d < 1 ? `${Math.round(d * 12)}M` : `${d}Y`)
      )
      .style("color", currentTheme.textSecondary)

    // Y-axis
    g.append("g")
      .call(d3.axisLeft(yScale)
        .tickFormat(d => `${d.toFixed(2)}%`)
      )
      .style("color", currentTheme.textSecondary)

    // Axis labels
    g.append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", 0 - margin.left + 15)
      .attr("x", 0 - (height / 2))
      .attr("dy", "1em")
      .style("text-anchor", "middle")
      .style("font-size", "12px")
      .style("fill", currentTheme.textSecondary)
      .text("Yield (%)")

    g.append("text")
      .attr("transform", `translate(${width / 2}, ${height + margin.bottom - 10})`)
      .style("text-anchor", "middle")
      .style("font-size", "12px")
      .style("fill", currentTheme.textSecondary)
      .text("Maturity")

    // Legend
    if (showLegend) {
      const legend = svg.append("g")
        .attr("transform", `translate(${width + margin.left + 20}, ${margin.top})`)

      let yOffset = 0
      curveData.forEach((points, currency) => {
        const color = getCurrencyColor(currency)
        
        legend.append("line")
          .attr("x1", 0)
          .attr("x2", 20)
          .attr("y1", yOffset)
          .attr("y2", yOffset)
          .attr("stroke", color)
          .attr("stroke-width", 2)

        legend.append("text")
          .attr("x", 25)
          .attr("y", yOffset)
          .attr("dy", "0.32em")
          .style("font-size", "11px")
          .style("fill", currentTheme.text)
          .text(currency)

        yOffset += 20
      })
    }

    // Cleanup tooltip on unmount
    return () => {
      d3.select("body").selectAll(".yield-tooltip").remove()
    }
  }

  // Initial data fetch
  useEffect(() => {
    if (selectedCurrencies.size > 0) {
      fetchCurveData()
    }
  }, [selectedCurrencies])

  // Redraw chart when data or display settings change
  useEffect(() => {
    drawChart()
  }, [curveData, currentTheme, showGrid, showLegend])

  // Handle window resize
  useEffect(() => {
    let resizeTimeout: NodeJS.Timeout
    const handleResize = () => {
      clearTimeout(resizeTimeout)
      resizeTimeout = setTimeout(() => {
        if (curveData.size > 0) {
          drawChart()
        }
      }, 200)
    }
    
    window.addEventListener('resize', handleResize)
    return () => {
      window.removeEventListener('resize', handleResize)
      clearTimeout(resizeTimeout)
    }
  }, [curveData])

  // Handle selector expand/collapse with layout adjustment
  useEffect(() => {
    let layoutTimeout: NodeJS.Timeout
    if (curveData.size > 0) {
      layoutTimeout = setTimeout(() => {
        drawChart()
      }, 100)
    }
    return () => clearTimeout(layoutTimeout)
  }, [expandedSelector, curveData.size])

  const toggleCurrency = (currency: string) => {
    const newSet = new Set(selectedCurrencies)
    if (newSet.has(currency)) {
      newSet.delete(currency)
    } else {
      newSet.add(currency)
    }
    setSelectedCurrencies(newSet)
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
            OIS & Yield Curves
          </span>
        </div>

        <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
          {/* Chart controls */}
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
            onClick={fetchCurveData}
            disabled={loading || selectedCurrencies.size === 0}
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

      {/* Currency Selector - Organized by Category */}
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
            <span style={{ fontSize: '12px', fontWeight: '600', color: currentTheme.text }}>Currencies</span>
            <span style={{ fontSize: '10px', color: currentTheme.textSecondary }}>
              ({selectedCurrencies.size} selected)
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
            {/* G10 Currencies */}
            <div style={{ marginBottom: '10px' }}>
              <div style={{ fontSize: '10px', color: currentTheme.textSecondary, marginBottom: '4px', fontWeight: '600' }}>
                G10 Currencies
              </div>
              <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                {G10_CURRENCIES.map(currency => (
                  <button
                    key={currency}
                    onClick={() => toggleCurrency(currency)}
                    style={{
                      padding: '2px 6px',
                      backgroundColor: selectedCurrencies.has(currency) ? getCurrencyColor(currency) : currentTheme.surface,
                      color: selectedCurrencies.has(currency) ? '#ffffff' : currentTheme.textSecondary,
                      border: `1px solid ${selectedCurrencies.has(currency) ? getCurrencyColor(currency) : currentTheme.border}`,
                      borderRadius: '3px',
                      cursor: 'pointer',
                      fontSize: '9px',
                      fontWeight: selectedCurrencies.has(currency) ? '600' : '400',
                      transition: 'all 0.2s ease'
                    }}
                  >
                    {currency}
                  </button>
                ))}
              </div>
            </div>

            {/* Emerging Markets */}
            <div>
              <div style={{ fontSize: '10px', color: currentTheme.textSecondary, marginBottom: '4px', fontWeight: '600' }}>
                Emerging Markets
              </div>
              <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                {EM_CURRENCIES.map(currency => (
                  <button
                    key={currency}
                    onClick={() => toggleCurrency(currency)}
                    style={{
                      padding: '2px 6px',
                      backgroundColor: selectedCurrencies.has(currency) ? getCurrencyColor(currency) : currentTheme.surface,
                      color: selectedCurrencies.has(currency) ? '#ffffff' : currentTheme.textSecondary,
                      border: `1px solid ${selectedCurrencies.has(currency) ? getCurrencyColor(currency) : currentTheme.border}`,
                      borderRadius: '3px',
                      cursor: 'pointer',
                      fontSize: '9px',
                      fontWeight: selectedCurrencies.has(currency) ? '600' : '400',
                      transition: 'all 0.2s ease'
                    }}
                  >
                    {currency}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Main Content Container - Dynamic height with resize protection */}
      <div style={{ flex: 1, minHeight: '400px', overflow: 'hidden', position: 'relative' }}>
        {/* Status messages */}
        {error && (
          <div style={{
            position: 'absolute',
            top: '16px',
            left: '50%',
            transform: 'translateX(-50%)',
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid #ef4444',
            borderRadius: '6px',
            padding: '8px 16px',
            fontSize: '12px',
            color: '#ef4444',
            zIndex: 10
          }}>
            {error}
          </div>
        )}

        {lastUpdate && !error && curveData.size > 0 && (
          <div style={{
            position: 'absolute',
            top: '8px',
            right: '8px',
            fontSize: '10px',
            color: currentTheme.textSecondary,
            backgroundColor: currentTheme.background,
            padding: '4px 8px',
            borderRadius: '4px',
            border: `1px solid ${currentTheme.border}`
          }}>
            <span style={{ fontWeight: '600' }}>Source:</span> {dataSource} • 
            <span style={{ fontWeight: '600' }}> Updated:</span> {lastUpdate.toLocaleTimeString()}
          </div>
        )}

        {/* Chart container */}
        <div 
          ref={chartContainerRef}
          style={{
            width: '100%',
            height: '100%',
            padding: '20px'
          }}
        />

        {/* Loading overlay */}
        {loading && (
          <div style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: currentTheme.background + 'dd',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '14px',
            color: currentTheme.textSecondary
          }}>
            Loading yield curves...
          </div>
        )}

        {/* No data message */}
        {!loading && selectedCurrencies.size > 0 && curveData.size === 0 && !error && (
          <div style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            textAlign: 'center',
            color: currentTheme.textSecondary
          }}>
            <div style={{ fontSize: '14px', marginBottom: '8px' }}>No yield curve data available</div>
            <div style={{ fontSize: '12px' }}>Try selecting different currencies or check Bloomberg connection</div>
          </div>
        )}

        {/* No selection message */}
        {selectedCurrencies.size === 0 && (
          <div style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            textAlign: 'center',
            color: currentTheme.textSecondary
          }}>
            <div style={{ fontSize: '14px' }}>Select currencies to display yield curves</div>
          </div>
        )}
      </div>
    </div>
  )
}