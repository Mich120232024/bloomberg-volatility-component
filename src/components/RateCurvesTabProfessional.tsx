import { useState, useEffect, useRef } from 'react'
import { useTheme } from '../contexts/ThemeContext'
import * as d3 from 'd3'
import { Currency, ALL_CURRENCIES } from '../constants/currencies'

type CurveType = 'yield' | 'forward' | 'swap'

interface CurvePoint {
  tenor: number     // Days to maturity
  years: number     // Years to maturity for proper scaling
  rate: number      // Rate in %
  label: string     // Display label
  ticker: string    // Bloomberg ticker
  instrumentType: 'money_market' | 'swap' | 'bond'
  isInterpolated?: boolean
}

interface CurveConfig {
  title: string
  instruments: Array<{
    ticker: string
    tenor: number
    label: string
    years: number
    instrumentType: 'money_market' | 'swap' | 'bond'
  }>
}

export function RateCurvesTabProfessional() {
  const { currentTheme } = useTheme()
  const chartContainerRef = useRef<HTMLDivElement>(null)
  
  // Controls
  const [curveType, setCurveType] = useState<CurveType>('yield')
  const [selectedCurrencies, setSelectedCurrencies] = useState<Set<Currency>>(new Set(['USD', 'EUR']))
  const [showGrid, setShowGrid] = useState(true)
  const [showLegend, setShowLegend] = useState(true)
  
  // Data
  const [curveData, setCurveData] = useState<Map<Currency, CurvePoint[]>>(new Map())
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Professional color palette
  const currencyColors: Record<Currency, string> = {
    USD: '#2E7D32',  // Forest green
    EUR: '#1976D2',  // Royal blue
    GBP: '#D32F2F',  // Deep red
    JPY: '#7B1FA2',  // Purple
    CHF: '#F57C00'   // Orange
  }

  // Curve configurations using validated Bloomberg tickers
  const getCurveConfig = (currency: Currency, type: CurveType): CurveConfig => {
    if (type === 'yield') {
      const configs: Record<Currency, CurveConfig> = {
        USD: {
          title: 'USD Yield Curve',
          instruments: [
            // Money market rates
            { ticker: 'SOFRRATE Index', tenor: 1, label: 'O/N', years: 0.003, instrumentType: 'money_market' },
            { ticker: 'US0001M Index', tenor: 30, label: '1M', years: 0.083, instrumentType: 'money_market' },
            { ticker: 'US0003M Index', tenor: 90, label: '3M', years: 0.25, instrumentType: 'money_market' },
            { ticker: 'US0006M Index', tenor: 180, label: '6M', years: 0.5, instrumentType: 'money_market' },
            { ticker: 'US0012M Index', tenor: 365, label: '1Y', years: 1, instrumentType: 'money_market' },
            // Treasury yields
            { ticker: 'USGG2Y Index', tenor: 730, label: '2Y', years: 2, instrumentType: 'bond' },
            { ticker: 'USGG3Y Index', tenor: 1095, label: '3Y', years: 3, instrumentType: 'bond' },
            { ticker: 'USGG5Y Index', tenor: 1825, label: '5Y', years: 5, instrumentType: 'bond' },
            { ticker: 'USGG7Y Index', tenor: 2555, label: '7Y', years: 7, instrumentType: 'bond' },
            { ticker: 'USGG10Y Index', tenor: 3650, label: '10Y', years: 10, instrumentType: 'bond' },
            { ticker: 'USGG20Y Index', tenor: 7300, label: '20Y', years: 20, instrumentType: 'bond' },
            { ticker: 'USGG30Y Index', tenor: 10950, label: '30Y', years: 30, instrumentType: 'bond' }
          ]
        },
        EUR: {
          title: 'EUR Yield Curve',
          instruments: [
            // Money market rates
            { ticker: 'ESTR Index', tenor: 1, label: 'O/N', years: 0.003, instrumentType: 'money_market' },
            { ticker: 'EUR001M Index', tenor: 30, label: '1M', years: 0.083, instrumentType: 'money_market' },
            { ticker: 'EUR003M Index', tenor: 90, label: '3M', years: 0.25, instrumentType: 'money_market' },
            { ticker: 'EUR006M Index', tenor: 180, label: '6M', years: 0.5, instrumentType: 'money_market' },
            { ticker: 'EUR012M Index', tenor: 365, label: '1Y', years: 1, instrumentType: 'money_market' },
            // German government bonds
            { ticker: 'GDBR2 Index', tenor: 730, label: '2Y', years: 2, instrumentType: 'bond' },
            { ticker: 'GDBR5 Index', tenor: 1825, label: '5Y', years: 5, instrumentType: 'bond' },
            { ticker: 'GDBR10 Index', tenor: 3650, label: '10Y', years: 10, instrumentType: 'bond' },
            { ticker: 'GDBR30 Index', tenor: 10950, label: '30Y', years: 30, instrumentType: 'bond' }
          ]
        },
        GBP: {
          title: 'GBP Yield Curve',
          instruments: [
            // Money market rates
            { ticker: 'GBPON Index', tenor: 1, label: 'O/N', years: 0.003, instrumentType: 'money_market' },
            { ticker: 'GBP001M Index', tenor: 30, label: '1M', years: 0.083, instrumentType: 'money_market' },
            { ticker: 'GBP003M Index', tenor: 90, label: '3M', years: 0.25, instrumentType: 'money_market' },
            { ticker: 'GBP006M Index', tenor: 180, label: '6M', years: 0.5, instrumentType: 'money_market' },
            { ticker: 'GBP012M Index', tenor: 365, label: '1Y', years: 1, instrumentType: 'money_market' },
            // UK government bonds
            { ticker: 'GUKG2 Index', tenor: 730, label: '2Y', years: 2, instrumentType: 'bond' },
            { ticker: 'GUKG5 Index', tenor: 1825, label: '5Y', years: 5, instrumentType: 'bond' },
            { ticker: 'GUKG10 Index', tenor: 3650, label: '10Y', years: 10, instrumentType: 'bond' },
            { ticker: 'GUKG30 Index', tenor: 10950, label: '30Y', years: 30, instrumentType: 'bond' }
          ]
        },
        JPY: {
          title: 'JPY Yield Curve',
          instruments: [
            // Money market rates
            { ticker: 'JPYON Index', tenor: 1, label: 'O/N', years: 0.003, instrumentType: 'money_market' },
            { ticker: 'JPY001M Index', tenor: 30, label: '1M', years: 0.083, instrumentType: 'money_market' },
            { ticker: 'JPY003M Index', tenor: 90, label: '3M', years: 0.25, instrumentType: 'money_market' },
            { ticker: 'JPY006M Index', tenor: 180, label: '6M', years: 0.5, instrumentType: 'money_market' },
            { ticker: 'JPY012M Index', tenor: 365, label: '1Y', years: 1, instrumentType: 'money_market' },
            // Japanese government bonds
            { ticker: 'GJGB2 Index', tenor: 730, label: '2Y', years: 2, instrumentType: 'bond' },
            { ticker: 'GJGB5 Index', tenor: 1825, label: '5Y', years: 5, instrumentType: 'bond' },
            { ticker: 'GJGB10 Index', tenor: 3650, label: '10Y', years: 10, instrumentType: 'bond' },
            { ticker: 'GJGB30 Index', tenor: 10950, label: '30Y', years: 30, instrumentType: 'bond' }
          ]
        },
        CHF: {
          title: 'CHF Yield Curve',
          instruments: [
            // Money market rates
            { ticker: 'CHFON Index', tenor: 1, label: 'O/N', years: 0.003, instrumentType: 'money_market' },
            { ticker: 'CHF001M Index', tenor: 30, label: '1M', years: 0.083, instrumentType: 'money_market' },
            { ticker: 'CHF003M Index', tenor: 90, label: '3M', years: 0.25, instrumentType: 'money_market' },
            { ticker: 'CHF006M Index', tenor: 180, label: '6M', years: 0.5, instrumentType: 'money_market' },
            { ticker: 'CHF012M Index', tenor: 365, label: '1Y', years: 1, instrumentType: 'money_market' },
            // Swiss government bonds
            { ticker: 'GSWISS2 Index', tenor: 730, label: '2Y', years: 2, instrumentType: 'bond' },
            { ticker: 'GSWISS5 Index', tenor: 1825, label: '5Y', years: 5, instrumentType: 'bond' },
            { ticker: 'GSWISS10 Index', tenor: 3650, label: '10Y', years: 10, instrumentType: 'bond' },
            { ticker: 'GSWISS30 Index', tenor: 10950, label: '30Y', years: 30, instrumentType: 'bond' }
          ]
        }
      }
      return configs[currency]
    } else if (type === 'swap') {
      // Swap curve configurations
      const swapConfigs: Record<Currency, CurveConfig> = {
        USD: {
          title: 'USD SOFR Swap Curve',
          instruments: [
            { ticker: 'USOSFR1 Curncy', tenor: 365, label: '1Y', years: 1, instrumentType: 'swap' },
            { ticker: 'USOSFR2 Curncy', tenor: 730, label: '2Y', years: 2, instrumentType: 'swap' },
            { ticker: 'USOSFR3 Curncy', tenor: 1095, label: '3Y', years: 3, instrumentType: 'swap' },
            { ticker: 'USOSFR4 Curncy', tenor: 1460, label: '4Y', years: 4, instrumentType: 'swap' },
            { ticker: 'USOSFR5 Curncy', tenor: 1825, label: '5Y', years: 5, instrumentType: 'swap' },
            { ticker: 'USOSFR7 Curncy', tenor: 2555, label: '7Y', years: 7, instrumentType: 'swap' },
            { ticker: 'USOSFR10 Curncy', tenor: 3650, label: '10Y', years: 10, instrumentType: 'swap' },
            { ticker: 'USOSFR15 Curncy', tenor: 5475, label: '15Y', years: 15, instrumentType: 'swap' },
            { ticker: 'USOSFR20 Curncy', tenor: 7300, label: '20Y', years: 20, instrumentType: 'swap' },
            { ticker: 'USOSFR30 Curncy', tenor: 10950, label: '30Y', years: 30, instrumentType: 'swap' }
          ]
        },
        EUR: {
          title: 'EUR OIS Swap Curve',
          instruments: [
            { ticker: 'EESWE1 Curncy', tenor: 365, label: '1Y', years: 1, instrumentType: 'swap' },
            { ticker: 'EESWE2 Curncy', tenor: 730, label: '2Y', years: 2, instrumentType: 'swap' },
            { ticker: 'EESWE3 Curncy', tenor: 1095, label: '3Y', years: 3, instrumentType: 'swap' },
            { ticker: 'EESWE4 Curncy', tenor: 1460, label: '4Y', years: 4, instrumentType: 'swap' },
            { ticker: 'EESWE5 Curncy', tenor: 1825, label: '5Y', years: 5, instrumentType: 'swap' },
            { ticker: 'EESWE7 Curncy', tenor: 2555, label: '7Y', years: 7, instrumentType: 'swap' },
            { ticker: 'EESWE10 Curncy', tenor: 3650, label: '10Y', years: 10, instrumentType: 'swap' },
            { ticker: 'EESWE15 Curncy', tenor: 5475, label: '15Y', years: 15, instrumentType: 'swap' },
            { ticker: 'EESWE20 Curncy', tenor: 7300, label: '20Y', years: 20, instrumentType: 'swap' },
            { ticker: 'EESWE30 Curncy', tenor: 10950, label: '30Y', years: 30, instrumentType: 'swap' }
          ]
        },
        GBP: {
          title: 'GBP SONIA Swap Curve',
          instruments: [
            { ticker: 'BPSW1 Curncy', tenor: 365, label: '1Y', years: 1, instrumentType: 'swap' },
            { ticker: 'BPSW2 Curncy', tenor: 730, label: '2Y', years: 2, instrumentType: 'swap' },
            { ticker: 'BPSW3 Curncy', tenor: 1095, label: '3Y', years: 3, instrumentType: 'swap' },
            { ticker: 'BPSW5 Curncy', tenor: 1825, label: '5Y', years: 5, instrumentType: 'swap' },
            { ticker: 'BPSW10 Curncy', tenor: 3650, label: '10Y', years: 10, instrumentType: 'swap' },
            { ticker: 'BPSW20 Curncy', tenor: 7300, label: '20Y', years: 20, instrumentType: 'swap' },
            { ticker: 'BPSW30 Curncy', tenor: 10950, label: '30Y', years: 30, instrumentType: 'swap' }
          ]
        },
        JPY: {
          title: 'JPY OIS Swap Curve',
          instruments: [
            { ticker: 'JYSO1 Curncy', tenor: 365, label: '1Y', years: 1, instrumentType: 'swap' },
            { ticker: 'JYSO2 Curncy', tenor: 730, label: '2Y', years: 2, instrumentType: 'swap' },
            { ticker: 'JYSO3 Curncy', tenor: 1095, label: '3Y', years: 3, instrumentType: 'swap' },
            { ticker: 'JYSO5 Curncy', tenor: 1825, label: '5Y', years: 5, instrumentType: 'swap' },
            { ticker: 'JYSO10 Curncy', tenor: 3650, label: '10Y', years: 10, instrumentType: 'swap' },
            { ticker: 'JYSO20 Curncy', tenor: 7300, label: '20Y', years: 20, instrumentType: 'swap' },
            { ticker: 'JYSO30 Curncy', tenor: 10950, label: '30Y', years: 30, instrumentType: 'swap' }
          ]
        },
        CHF: {
          title: 'CHF SARON Swap Curve',
          instruments: [
            { ticker: 'SFSNT1 Curncy', tenor: 365, label: '1Y', years: 1, instrumentType: 'swap' },
            { ticker: 'SFSNT2 Curncy', tenor: 730, label: '2Y', years: 2, instrumentType: 'swap' },
            { ticker: 'SFSNT3 Curncy', tenor: 1095, label: '3Y', years: 3, instrumentType: 'swap' },
            { ticker: 'SFSNT5 Curncy', tenor: 1825, label: '5Y', years: 5, instrumentType: 'swap' },
            { ticker: 'SFSNT10 Curncy', tenor: 3650, label: '10Y', years: 10, instrumentType: 'swap' },
            { ticker: 'SFSNT20 Curncy', tenor: 7300, label: '20Y', years: 20, instrumentType: 'swap' },
            { ticker: 'SFSNT30 Curncy', tenor: 10950, label: '30Y', years: 30, instrumentType: 'swap' }
          ]
        }
      }
      return swapConfigs[currency]
    }
    
    // Default to yield curve
    return getCurveConfig(currency, 'yield')
  }

  // Fetch curve data from Bloomberg
  const fetchCurveData = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const apiUrl = import.meta.env.DEV ? 'http://localhost:8000' : 'http://20.172.249.92:8080'
      const newCurveData = new Map<Currency, CurvePoint[]>()
      
      // Fetch data for each selected currency
      for (const currency of selectedCurrencies) {
        const config = getCurveConfig(currency, curveType)
        const tickers = config.instruments.map(i => i.ticker)
        
        const response = await fetch(`${apiUrl}/api/bloomberg/reference`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test'
          },
          body: JSON.stringify({
            securities: tickers,
            fields: ['PX_LAST', 'YLD_YTM_MID']
          })
        })
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }
        
        const result = await response.json()
        
        if (result.data?.securities_data) {
          const points: CurvePoint[] = []
          
          result.data.securities_data.forEach((secData: any, index: number) => {
            if (secData.success && index < config.instruments.length) {
              const instrument = config.instruments[index]
              const rate = secData.fields?.YLD_YTM_MID || secData.fields?.PX_LAST
              
              if (rate !== null && rate !== undefined) {
                points.push({
                  tenor: instrument.tenor,
                  years: instrument.years,
                  rate: rate,
                  label: instrument.label,
                  ticker: instrument.ticker,
                  instrumentType: instrument.instrumentType
                })
              }
            }
          })
          
          // Sort by years and interpolate if needed
          points.sort((a, b) => a.years - b.years)
          newCurveData.set(currency, interpolateCurve(points))
        }
      }
      
      setCurveData(newCurveData)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch curve data')
      console.error('Curve data fetch error:', err)
    } finally {
      setLoading(false)
    }
  }

  // Interpolate curve for smooth display
  const interpolateCurve = (points: CurvePoint[]): CurvePoint[] => {
    if (points.length < 2) return points
    
    // Create interpolation function
    const xValues = points.map(p => p.years)
    const yValues = points.map(p => p.rate)
    
    const interpolate = d3.scaleLinear()
      .domain(xValues)
      .range(yValues)
      .clamp(true)
    
    // Add interpolated points for smooth curve
    const interpolatedPoints: CurvePoint[] = []
    const targetYears = [0.003, 0.083, 0.25, 0.5, 0.75, 1, 1.5, 2, 2.5, 3, 4, 5, 7, 10, 15, 20, 25, 30]
    
    targetYears.forEach(year => {
      const existingPoint = points.find(p => Math.abs(p.years - year) < 0.01)
      if (existingPoint) {
        interpolatedPoints.push(existingPoint)
      } else if (year >= xValues[0] && year <= xValues[xValues.length - 1]) {
        interpolatedPoints.push({
          tenor: Math.round(year * 365),
          years: year,
          rate: interpolate(year),
          label: formatTenorLabel(year),
          ticker: 'interpolated',
          instrumentType: 'money_market',
          isInterpolated: true
        })
      }
    })
    
    return interpolatedPoints.sort((a, b) => a.years - b.years)
  }

  // Format tenor label
  const formatTenorLabel = (years: number): string => {
    if (years < 0.08) return 'O/N'
    if (years < 1) return `${Math.round(years * 12)}M`
    return `${years}Y`
  }

  // Draw chart using D3
  const drawChart = () => {
    if (!chartContainerRef.current || curveData.size === 0) return

    // Clear previous chart
    d3.select(chartContainerRef.current).select('svg').remove()

    // Dimensions
    const margin = { top: 20, right: 120, bottom: 60, left: 70 }
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
    const xScale = d3.scaleLog()
      .domain([0.08, 30])  // 1 month to 30 years
      .range([0, width])
      .nice()

    const allRates = Array.from(curveData.values()).flat().map(d => d.rate)
    const yScale = d3.scaleLinear()
      .domain(d3.extent(allRates) as [number, number])
      .range([height, 0])
      .nice()

    // Grid lines
    if (showGrid) {
      // X-axis grid
      g.append('g')
        .attr('class', 'grid')
        .attr('transform', `translate(0,${height})`)
        .call(d3.axisBottom(xScale)
          .tickSize(-height)
          .tickFormat(() => '')
        )
        .style('stroke-dasharray', '3,3')
        .style('opacity', 0.3)
        .style('stroke', currentTheme.textSecondary)

      // Y-axis grid
      g.append('g')
        .attr('class', 'grid')
        .call(d3.axisLeft(yScale)
          .tickSize(-width)
          .tickFormat(() => '')
        )
        .style('stroke-dasharray', '3,3')
        .style('opacity', 0.3)
        .style('stroke', currentTheme.textSecondary)
    }

    // X-axis
    const xAxis = g.append('g')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(xScale)
        .tickValues([0.083, 0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30])
        .tickFormat(d => formatTenorLabel(d as number))
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
        .tickFormat(d => `${d}%`)
      )

    yAxis.selectAll('text')
      .style('fill', currentTheme.text)
      .style('font-size', '12px')

    yAxis.select('.domain')
      .style('stroke', currentTheme.border)

    yAxis.selectAll('.tick line')
      .style('stroke', currentTheme.border)

    // Line generator
    const line = d3.line<CurvePoint>()
      .x(d => xScale(d.years))
      .y(d => yScale(d.rate))
      .curve(d3.curveMonotoneX)  // Smooth monotonic curve

    // Draw lines for each currency
    curveData.forEach((points, currency) => {
      const color = currencyColors[currency]
      
      // Draw the line
      g.append('path')
        .datum(points)
        .attr('fill', 'none')
        .attr('stroke', color)
        .attr('stroke-width', 2.5)
        .attr('d', line)
        .style('opacity', 0.9)

      // Add points for actual data (not interpolated)
      g.selectAll(`.point-${currency}`)
        .data(points.filter(p => !p.isInterpolated))
        .enter().append('circle')
        .attr('class', `point-${currency}`)
        .attr('cx', d => xScale(d.years))
        .attr('cy', d => yScale(d.rate))
        .attr('r', 4)
        .attr('fill', color)
        .style('cursor', 'pointer')
        .on('mouseover', function(event, d) {
          // Tooltip
          const tooltip = d3.select('body').append('div')
            .attr('class', 'tooltip')
            .style('position', 'absolute')
            .style('background', currentTheme.surface)
            .style('border', `1px solid ${currentTheme.border}`)
            .style('padding', '8px')
            .style('border-radius', '4px')
            .style('font-size', '12px')
            .style('pointer-events', 'none')
            .style('opacity', 0)

          tooltip.transition()
            .duration(200)
            .style('opacity', 0.9)

          tooltip.html(`
            <div style="color: ${currentTheme.text}">
              <strong>${currency} ${d.label}</strong><br/>
              Rate: ${d.rate.toFixed(3)}%<br/>
              Ticker: ${d.ticker}
            </div>
          `)
            .style('left', (event.pageX + 10) + 'px')
            .style('top', (event.pageY - 28) + 'px')
        })
        .on('mouseout', function() {
          d3.selectAll('.tooltip').remove()
        })
    })

    // Legend
    if (showLegend) {
      const legend = svg.append('g')
        .attr('transform', `translate(${width + margin.left + 20}, ${margin.top})`)

      let yOffset = 0
      curveData.forEach((points, currency) => {
        const color = currencyColors[currency]
        
        legend.append('rect')
          .attr('x', 0)
          .attr('y', yOffset)
          .attr('width', 12)
          .attr('height', 12)
          .attr('fill', color)

        legend.append('text')
          .attr('x', 18)
          .attr('y', yOffset + 9)
          .text(getCurveConfig(currency, curveType).title)
          .style('font-size', '12px')
          .style('fill', currentTheme.text)

        yOffset += 20
      })
    }

    // Axis labels
    svg.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('y', 0)
      .attr('x', 0 - (height / 2))
      .attr('dy', '1em')
      .style('text-anchor', 'middle')
      .style('fill', currentTheme.text)
      .style('font-size', '14px')
      .text('Yield (%)')

    svg.append('text')
      .attr('transform', `translate(${width / 2 + margin.left}, ${height + margin.top + 45})`)
      .style('text-anchor', 'middle')
      .style('fill', currentTheme.text)
      .style('font-size', '14px')
      .text('Maturity')
  }

  // Effects
  useEffect(() => {
    fetchCurveData()
  }, [selectedCurrencies, curveType])

  useEffect(() => {
    drawChart()
  }, [curveData, currentTheme, showGrid, showLegend])

  useEffect(() => {
    const handleResize = () => {
      drawChart()
    }
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [curveData])

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
      backgroundColor: currentTheme.background,
      color: currentTheme.text,
      height: '100%',
      display: 'flex',
      flexDirection: 'column'
    }}>
      {/* Header */}
      <div style={{
        borderBottom: `1px solid ${currentTheme.border}`,
        padding: '16px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <h2 style={{ margin: 0, color: currentTheme.text }}>
          Professional Rate Curves
        </h2>
        
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          {/* Curve Type Selector */}
          <div style={{ display: 'flex', gap: '8px' }}>
            {(['yield', 'swap', 'forward'] as CurveType[]).map(type => (
              <button
                key={type}
                onClick={() => setCurveType(type)}
                style={{
                  padding: '6px 16px',
                  backgroundColor: curveType === type ? currentTheme.primary : currentTheme.surface,
                  color: curveType === type ? 'white' : currentTheme.text,
                  border: `1px solid ${currentTheme.border}`,
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '13px',
                  fontWeight: curveType === type ? '600' : '400',
                  textTransform: 'capitalize'
                }}
              >
                {type}
              </button>
            ))}
          </div>

          {/* Display Options */}
          <div style={{ display: 'flex', gap: '12px' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px' }}>
              <input
                type="checkbox"
                checked={showGrid}
                onChange={(e) => setShowGrid(e.target.checked)}
              />
              Grid
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px' }}>
              <input
                type="checkbox"
                checked={showLegend}
                onChange={(e) => setShowLegend(e.target.checked)}
              />
              Legend
            </label>
          </div>
        </div>
      </div>

      {/* Currency Selector */}
      <div style={{
        padding: '12px 16px',
        borderBottom: `1px solid ${currentTheme.border}`,
        display: 'flex',
        gap: '8px',
        alignItems: 'center'
      }}>
        <span style={{ fontSize: '13px', marginRight: '8px' }}>Currencies:</span>
        {ALL_CURRENCIES.map(currency => (
          <button
            key={currency}
            onClick={() => toggleCurrency(currency)}
            style={{
              padding: '4px 12px',
              backgroundColor: selectedCurrencies.has(currency) ? currencyColors[currency] : currentTheme.surface,
              color: selectedCurrencies.has(currency) ? 'white' : currentTheme.text,
              border: `1px solid ${selectedCurrencies.has(currency) ? currencyColors[currency] : currentTheme.border}`,
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '12px',
              fontWeight: selectedCurrencies.has(currency) ? '600' : '400',
              opacity: selectedCurrencies.has(currency) ? 1 : 0.7
            }}
          >
            {currency}
          </button>
        ))}
      </div>

      {/* Chart Container */}
      <div style={{ flex: 1, padding: '16px', position: 'relative' }}>
        {loading && (
          <div style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            fontSize: '14px',
            color: currentTheme.textSecondary
          }}>
            Loading curve data...
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
        
        <div ref={chartContainerRef} style={{ width: '100%', height: '100%' }} />
      </div>

      {/* Info Bar */}
      <div style={{
        borderTop: `1px solid ${currentTheme.border}`,
        padding: '8px 16px',
        fontSize: '12px',
        color: currentTheme.textSecondary,
        display: 'flex',
        justifyContent: 'space-between'
      }}>
        <span>
          {curveData.size > 0 && `Showing ${Array.from(curveData.values()).flat().filter(p => !p.isInterpolated).length} market points`}
        </span>
        <span>
          {new Date().toLocaleString()}
        </span>
      </div>
    </div>
  )
}