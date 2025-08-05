import { useState, useEffect, useRef } from 'react'
import { useTheme } from '../contexts/ThemeContext'
import * as d3 from 'd3'
import { Currency, ALL_CURRENCIES } from '../constants/currencies'

interface CurvePoint {
  tenor: number     // Days to maturity
  years: number     // Years to maturity for proper scaling
  rate: number      // Rate in %
  label: string     // Display label
  ticker: string    // Bloomberg ticker
  instrumentType: 'money_market' | 'swap' | 'bond'
}

interface CurveConfig {
  dbCurveName: string
  displayName: string
  color: string
}

// Map currencies to their database curve names
const CURVE_MAPPINGS: Record<string, CurveConfig> = {
  USD: { dbCurveName: 'USD_SOFR_OIS', displayName: 'USD SOFR OIS', color: '#2E7D32' },
  EUR: { dbCurveName: 'EUR_IRS', displayName: 'EUR IRS', color: '#1976D2' },
  GBP: { dbCurveName: 'GBP_IRS', displayName: 'GBP IRS', color: '#D32F2F' },
  JPY: { dbCurveName: 'JPY_OIS', displayName: 'JPY OIS', color: '#7B1FA2' },
  CHF: { dbCurveName: 'CHF_IRS', displayName: 'CHF IRS', color: '#F57C00' },
  AUD: { dbCurveName: 'AUD_IRS', displayName: 'AUD IRS', color: '#00897B' },
  CAD: { dbCurveName: 'CAD_IRS', displayName: 'CAD IRS', color: '#E91E63' },
  NZD: { dbCurveName: 'NOK_IRS', displayName: 'NOK IRS', color: '#00ACC1' }, // Using NOK as proxy
  SEK: { dbCurveName: 'SEK_IRS', displayName: 'SEK IRS', color: '#FDD835' },
  NOK: { dbCurveName: 'NOK_IRS', displayName: 'NOK IRS', color: '#6A4C93' },
  DKK: { dbCurveName: 'EUR_IRS', displayName: 'EUR IRS', color: '#8E24AA' }, // DKK pegged to EUR
  ISK: { dbCurveName: 'EUR_IRS', displayName: 'EUR IRS', color: '#E53935' }, // ISK linked to EUR
  // Additional currencies
  CNH: { dbCurveName: 'CNH_IRS', displayName: 'CNH IRS', color: '#FF5722' },
  KRW: { dbCurveName: 'KRW_IRS', displayName: 'KRW IRS', color: '#795548' },
  MXN: { dbCurveName: 'MXN_IRS', displayName: 'MXN IRS', color: '#9C27B0' },
  BRL: { dbCurveName: 'BRL_IRS', displayName: 'BRL IRS', color: '#3F51B5' },
  TRY: { dbCurveName: 'TRY_IRS', displayName: 'TRY IRS', color: '#009688' },
  ZAR: { dbCurveName: 'ZAR_IRS', displayName: 'ZAR IRS', color: '#FF9800' },
  SGD: { dbCurveName: 'SGD_IRS', displayName: 'SGD IRS', color: '#4CAF50' },
  INR: { dbCurveName: 'INR_IRS', displayName: 'INR IRS', color: '#CDDC39' },
  THB: { dbCurveName: 'THB_IRS', displayName: 'THB IRS', color: '#2196F3' },
  PLN: { dbCurveName: 'PLN_IRS', displayName: 'PLN IRS', color: '#FF4081' }
}

export function YieldCurvesMulti() {
  const { currentTheme } = useTheme()
  const chartContainerRef = useRef<HTMLDivElement>(null)
  
  const [selectedCurrencies, setSelectedCurrencies] = useState<Set<Currency>>(new Set(['USD', 'EUR', 'JPY']))
  const [curveData, setCurveData] = useState<Map<Currency, CurvePoint[]>>(new Map())
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showGrid, setShowGrid] = useState(true)
  const [showLegend, setShowLegend] = useState(true)

  // Get database tickers for a curve
  const getCurveTickers = async (curveName: string): Promise<string[]> => {
    const conn_str = process.env.POSTGRES_CONNECTION_STRING
    if (!conn_str) {
      console.warn('No database connection, using fallback tickers')
      // Return known working tickers as fallback
      if (curveName === 'JPY_OIS') {
        return [
          "JYSO1Z BGN Curncy", "JYSO2Z BGN Curncy", "JYSO3Z BGN Curncy",
          "JYSOA BGN Curncy", "JYSOB BGN Curncy", "JYSOC BGN Curncy",
          "JYSOD BGN Curncy", "JYSOE BGN Curncy", "JYSOF BGN Curncy",
          "JYSOG BGN Curncy", "JYSOH BGN Curncy", "JYSOI BGN Curncy",
          "JYSOJ BGN Curncy", "JYSOK BGN Curncy", "JYSO1 BGN Curncy",
          "JYSO1C BGN Curncy", "JYSO1F BGN Curncy"
        ]
      }
      return []
    }
    
    // In real implementation, query database
    // For now, return empty array
    return []
  }

  // Fetch curve data from Bloomberg
  const fetchCurveData = async () => {
    console.log('🚀 Fetching curve data for:', Array.from(selectedCurrencies))
    setLoading(true)
    setError(null)
    
    try {
      const apiUrl = import.meta.env.DEV ? 'http://localhost:8000' : 'http://20.172.249.92:8080'
      const newCurveData = new Map<Currency, CurvePoint[]>()
      
      for (const currency of selectedCurrencies) {
        const config = CURVE_MAPPINGS[currency]
        if (!config) {
          console.warn(`No curve mapping for ${currency}`)
          continue
        }
        
        // For now, use hardcoded tickers for currencies we know work
        let tickers: string[] = []
        
        if (currency === 'JPY') {
          tickers = [
            "JYSO1Z BGN Curncy", "JYSO2Z BGN Curncy", "JYSO3Z BGN Curncy",
            "JYSOA BGN Curncy", "JYSOB BGN Curncy", "JYSOC BGN Curncy",
            "JYSOD BGN Curncy", "JYSOE BGN Curncy", "JYSOF BGN Curncy",
            "JYSOG BGN Curncy", "JYSOH BGN Curncy", "JYSOI BGN Curncy",
            "JYSOJ BGN Curncy", "JYSOK BGN Curncy", "JYSO1 BGN Curncy",
            "JYSO1C BGN Curncy", "JYSO1F BGN Curncy"
          ]
        } else if (currency === 'USD') {
          // USD SOFR OIS tickers from our earlier exploration
          tickers = [
            "SOFRRATE Index",
            "US0001M Index", "US0003M Index", "US0006M Index",
            "USSO1 Curncy", "USSO2 Curncy", "USSO3 Curncy", 
            "USSO5 Curncy", "USSO10 Curncy"
          ]
        } else if (currency === 'EUR') {
          tickers = [
            "ESTR Index",
            "EUR001M Index", "EUR003M Index", "EUR006M Index",
            "EESWE2 Curncy", "EESWE3 Curncy", "EESWE5 Curncy", "EESWE10 Curncy"
          ]
        }
        
        if (tickers.length === 0) {
          console.log(`No tickers configured for ${currency}`)
          continue
        }
        
        const response = await fetch(`${apiUrl}/api/bloomberg/reference`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test'
          },
          body: JSON.stringify({
            securities: tickers,
            fields: ['PX_LAST', 'YLD_YTM_MID', 'DAYS_TO_MTY', 'MATURITY']
          })
        })
        
        if (!response.ok) {
          console.error(`Failed to fetch ${currency}: HTTP ${response.status}`)
          continue
        }
        
        const result = await response.json()
        
        if (result.data?.securities_data) {
          const points: CurvePoint[] = []
          
          result.data.securities_data.forEach((secData: any, index: number) => {
            if (secData.success && index < tickers.length) {
              const rate = secData.fields?.YLD_YTM_MID || secData.fields?.PX_LAST
              const days = secData.fields?.DAYS_TO_MTY
              
              if (rate !== null && rate !== undefined) {
                // Estimate days/years if not provided
                let estimatedDays = days || estimateDaysFromTicker(tickers[index])
                let years = estimatedDays / 365
                
                points.push({
                  tenor: estimatedDays,
                  years: years,
                  rate: rate,
                  label: formatLabel(estimatedDays),
                  ticker: tickers[index],
                  instrumentType: getInstrumentType(tickers[index])
                })
              }
            }
          })
          
          // Sort by tenor and add to map
          points.sort((a, b) => a.tenor - b.tenor)
          if (points.length > 0) {
            newCurveData.set(currency, points)
            console.log(`✅ ${currency}: ${points.length} points`)
          }
        }
      }
      
      setCurveData(newCurveData)
    } catch (err) {
      console.error('❌ Curve data fetch error:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch curve data')
    } finally {
      setLoading(false)
    }
  }

  // Estimate days from ticker pattern
  const estimateDaysFromTicker = (ticker: string): number => {
    if (ticker.includes('RATE') || ticker.includes('ON')) return 1
    if (ticker.includes('1M')) return 30
    if (ticker.includes('3M')) return 90
    if (ticker.includes('6M')) return 180
    if (ticker.includes('9M')) return 270
    if (ticker.includes('12M') || ticker.includes('1Y')) return 365
    if (ticker.includes('2Y')) return 730
    if (ticker.includes('3Y')) return 1095
    if (ticker.includes('5Y')) return 1825
    if (ticker.includes('10Y')) return 3650
    if (ticker.includes('20Y')) return 7300
    if (ticker.includes('30Y')) return 10950
    
    // For OIS tickers
    if (ticker.includes('1Z')) return 7
    if (ticker.includes('2Z')) return 14
    if (ticker.includes('3Z')) return 21
    if (ticker.includes('SOA')) return 30
    if (ticker.includes('SOB')) return 60
    if (ticker.includes('SOC')) return 90
    if (ticker.includes('SOD')) return 120
    if (ticker.includes('SOE')) return 150
    if (ticker.includes('SOF')) return 180
    if (ticker.includes('SOG')) return 210
    if (ticker.includes('SOH')) return 240
    if (ticker.includes('SOI')) return 270
    if (ticker.includes('SOJ')) return 300
    if (ticker.includes('SOK')) return 330
    if (ticker.includes('SO1') && !ticker.includes('SO1C') && !ticker.includes('SO1F')) return 365
    if (ticker.includes('SO1C')) return 457
    if (ticker.includes('SO1F')) return 549
    
    return 365 // Default 1Y
  }

  // Get instrument type from ticker
  const getInstrumentType = (ticker: string): 'money_market' | 'swap' | 'bond' => {
    if (ticker.includes('Index') && !ticker.includes('Curncy')) return 'money_market'
    if (ticker.includes('Curncy')) return 'swap'
    return 'bond'
  }

  // Format label based on days
  const formatLabel = (days: number): string => {
    if (days === 1) return 'O/N'
    if (days < 30) return `${days}D`
    if (days < 365) {
      const months = Math.round(days / 30)
      return `${months}M`
    }
    const years = days / 365
    if (years === Math.floor(years)) return `${years}Y`
    return `${years.toFixed(1)}Y`
  }

  // Draw chart using D3
  const drawChart = () => {
    if (!chartContainerRef.current || curveData.size === 0) return

    // Clear previous chart
    d3.select(chartContainerRef.current).select('svg').remove()

    // Dimensions
    const margin = { top: 30, right: 150, bottom: 60, left: 70 }
    const width = chartContainerRef.current.clientWidth - margin.left - margin.right
    const height = 500 - margin.top - margin.bottom

    // Create SVG
    const svg = d3.select(chartContainerRef.current)
      .append('svg')
      .attr('width', width + margin.left + margin.right)
      .attr('height', height + margin.top + margin.bottom)

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`)

    // Find data range
    let minRate = Infinity
    let maxRate = -Infinity
    let maxYears = 0
    
    curveData.forEach(points => {
      points.forEach(point => {
        minRate = Math.min(minRate, point.rate)
        maxRate = Math.max(maxRate, point.rate)
        maxYears = Math.max(maxYears, point.years)
      })
    })

    // Scales
    const xScale = d3.scaleLinear()
      .domain([0, Math.min(maxYears, 10)]) // Cap at 10Y for better visibility
      .range([0, width])

    const yScale = d3.scaleLinear()
      .domain([Math.floor(minRate), Math.ceil(maxRate)])
      .nice()
      .range([height, 0])

    // Grid
    if (showGrid) {
      // X-axis grid
      g.append('g')
        .attr('class', 'grid')
        .attr('transform', `translate(0,${height})`)
        .call(d3.axisBottom(xScale)
          .tickSize(-height)
          .tickFormat(() => '')
        )
        .style('stroke-dasharray', '2,2')
        .style('opacity', 0.3)

      // Y-axis grid
      g.append('g')
        .attr('class', 'grid')
        .call(d3.axisLeft(yScale)
          .tickSize(-width)
          .tickFormat(() => '')
        )
        .style('stroke-dasharray', '2,2')
        .style('opacity', 0.3)
    }

    // Line generator
    const line = d3.line<CurvePoint>()
      .x(d => xScale(d.years))
      .y(d => yScale(d.rate))
      .curve(d3.curveCatmullRom.alpha(0.5))

    // Draw lines for each currency
    curveData.forEach((points, currency) => {
      const config = CURVE_MAPPINGS[currency]
      const color = config?.color || '#666'

      // Line
      g.append('path')
        .datum(points)
        .attr('fill', 'none')
        .attr('stroke', color)
        .attr('stroke-width', 2)
        .attr('d', line)

      // Points
      g.selectAll(`.point-${currency}`)
        .data(points)
        .enter().append('circle')
        .attr('class', `point-${currency}`)
        .attr('cx', d => xScale(d.years))
        .attr('cy', d => yScale(d.rate))
        .attr('r', 3)
        .attr('fill', color)
        .style('cursor', 'pointer')
        .on('mouseover', function(event, d) {
          // Show tooltip
          const tooltip = d3.select('body').append('div')
            .attr('class', 'tooltip')
            .style('position', 'absolute')
            .style('background', currentTheme.surface)
            .style('border', `1px solid ${currentTheme.border}`)
            .style('padding', '8px')
            .style('border-radius', '4px')
            .style('font-size', '12px')
            .style('pointer-events', 'none')
            .html(`
              <div><strong>${currency} ${d.label}</strong></div>
              <div>Rate: ${d.rate.toFixed(3)}%</div>
              <div style="font-size: 10px; color: ${currentTheme.textSecondary}">${d.ticker}</div>
            `)
            .style('left', (event.pageX + 10) + 'px')
            .style('top', (event.pageY - 28) + 'px')
        })
        .on('mouseout', function() {
          d3.selectAll('.tooltip').remove()
        })
    })

    // X-axis
    g.append('g')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(xScale).tickFormat(d => `${d}Y`))

    // Y-axis
    g.append('g')
      .call(d3.axisLeft(yScale).tickFormat(d => `${d}%`))

    // Title
    svg.append('text')
      .attr('x', margin.left + width / 2)
      .attr('y', 20)
      .attr('text-anchor', 'middle')
      .style('font-size', '16px')
      .style('font-weight', 'bold')
      .text('Multi-Currency Yield Curves')

    // Legend
    if (showLegend) {
      const legend = svg.append('g')
        .attr('transform', `translate(${width + margin.left + 20}, ${margin.top})`)

      let yOffset = 0
      curveData.forEach((points, currency) => {
        const config = CURVE_MAPPINGS[currency]
        const color = config?.color || '#666'
        const latestPoint = points[points.length - 1]

        const legendItem = legend.append('g')
          .attr('transform', `translate(0, ${yOffset})`)

        legendItem.append('rect')
          .attr('width', 12)
          .attr('height', 12)
          .attr('fill', color)

        legendItem.append('text')
          .attr('x', 18)
          .attr('y', 10)
          .text(`${currency}: ${latestPoint?.rate.toFixed(2)}%`)
          .style('font-size', '12px')

        yOffset += 20
      })
    }
  }

  useEffect(() => {
    if (selectedCurrencies.size > 0) {
      fetchCurveData()
    }
  }, [selectedCurrencies])

  useEffect(() => {
    drawChart()
  }, [curveData, currentTheme, showGrid, showLegend])

  const toggleCurrency = (currency: Currency) => {
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
      padding: '16px',
      height: '100%',
      display: 'flex',
      flexDirection: 'column'
    }}>
      {/* Header Controls */}
      <div style={{
        marginBottom: '16px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '12px'
      }}>
        {/* Currency Selector */}
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {Object.keys(CURVE_MAPPINGS).map(currency => (
            <button
              key={currency}
              onClick={() => toggleCurrency(currency as Currency)}
              style={{
                padding: '4px 8px',
                backgroundColor: selectedCurrencies.has(currency as Currency) 
                  ? CURVE_MAPPINGS[currency].color 
                  : currentTheme.surface,
                color: selectedCurrencies.has(currency as Currency) 
                  ? '#fff' 
                  : currentTheme.text,
                border: `1px solid ${currentTheme.border}`,
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '12px',
                transition: 'all 0.2s ease'
              }}
            >
              {currency}
            </button>
          ))}
        </div>

        {/* Options */}
        <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <input
              type="checkbox"
              checked={showGrid}
              onChange={(e) => setShowGrid(e.target.checked)}
            />
            Grid
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <input
              type="checkbox"
              checked={showLegend}
              onChange={(e) => setShowLegend(e.target.checked)}
            />
            Legend
          </label>
          <button
            onClick={fetchCurveData}
            disabled={loading || selectedCurrencies.size === 0}
            style={{
              padding: '6px 12px',
              backgroundColor: currentTheme.primary,
              color: currentTheme.background,
              border: 'none',
              borderRadius: '4px',
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? 'Loading...' : 'Refresh'}
          </button>
        </div>
      </div>

      {error && (
        <div style={{ color: '#ef4444', marginBottom: '16px' }}>
          Error: {error}
        </div>
      )}

      {/* Chart */}
      <div ref={chartContainerRef} style={{ flex: 1, minHeight: '500px' }} />

      {/* Status */}
      <div style={{
        marginTop: '16px',
        fontSize: '12px',
        color: currentTheme.textSecondary
      }}>
        {curveData.size > 0 && 
          `Showing ${curveData.size} curves with ${Array.from(curveData.values()).reduce((sum, points) => sum + points.length, 0)} total data points`
        }
      </div>
    </div>
  )
}