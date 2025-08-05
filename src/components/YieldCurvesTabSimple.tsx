import { useState, useEffect, useRef } from 'react'
import { useTheme } from '../contexts/ThemeContext'
import * as d3 from 'd3'
import { Currency } from '../constants/currencies'

interface CurvePoint {
  tenor: number     // Days to maturity
  years: number     // Years to maturity for proper scaling
  rate: number      // Rate in %
  label: string     // Display label
  ticker: string    // Bloomberg ticker
  instrumentType: 'money_market' | 'swap' | 'bond'
}

// Test with JPY OIS curve we know works
const JPY_OIS_TICKERS = [
  "JYSO1Z BGN Curncy",  // 7 days
  "JYSO2Z BGN Curncy",  // 14 days
  "JYSO3Z BGN Curncy",  // 21 days
  "JYSOA BGN Curncy",   // 1M
  "JYSOB BGN Curncy",   // 2M
  "JYSOC BGN Curncy",   // 3M
  "JYSOD BGN Curncy",   // 4M
  "JYSOE BGN Curncy",   // 5M
  "JYSOF BGN Curncy",   // 6M
  "JYSOG BGN Curncy",   // 7M
  "JYSOH BGN Curncy",   // 8M
  "JYSOI BGN Curncy",   // 9M
  "JYSOJ BGN Curncy",   // 10M
  "JYSOK BGN Curncy",   // 11M
  "JYSO1 BGN Curncy",   // 1Y
  "JYSO1C BGN Curncy",  // 15M
  "JYSO1F BGN Curncy"   // 18M
]

export function YieldCurvesTabSimple() {
  const { currentTheme } = useTheme()
  const chartContainerRef = useRef<HTMLDivElement>(null)
  
  const [curveData, setCurveData] = useState<CurvePoint[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Fetch JPY OIS curve from Bloomberg
  const fetchCurveData = async () => {
    console.log('🚀 Fetching JPY OIS curve data...')
    setLoading(true)
    setError(null)
    
    try {
      const apiUrl = import.meta.env.DEV ? 'http://localhost:8000' : 'http://20.172.249.92:8080'
      
      const response = await fetch(`${apiUrl}/api/bloomberg/reference`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer test'
        },
        body: JSON.stringify({
          securities: JPY_OIS_TICKERS,
          fields: ['PX_LAST', 'DAYS_TO_MTY', 'MATURITY']
        })
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      
      const result = await response.json()
      console.log('📊 Bloomberg response:', result)
      
      if (result.data?.securities_data) {
        const points: CurvePoint[] = []
        
        result.data.securities_data.forEach((secData: any, index: number) => {
          if (secData.success) {
            const rate = secData.fields?.PX_LAST
            const days = secData.fields?.DAYS_TO_MTY || 0
            
            if (rate !== null && rate !== undefined) {
              const years = days / 365
              const label = formatLabel(days)
              
              points.push({
                tenor: days,
                years: years,
                rate: rate,
                label: label,
                ticker: JPY_OIS_TICKERS[index],
                instrumentType: 'swap'
              })
            }
          }
        })
        
        // Sort by days to maturity
        points.sort((a, b) => a.tenor - b.tenor)
        setCurveData(points)
        console.log(`✅ Got ${points.length} curve points`)
      }
    } catch (err) {
      console.error('❌ Curve data fetch error:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch curve data')
    } finally {
      setLoading(false)
    }
  }

  // Format label based on days
  const formatLabel = (days: number): string => {
    if (days < 30) return `${days}D`
    if (days < 365) return `${Math.round(days/30)}M`
    return `${(days/365).toFixed(1)}Y`
  }

  // Draw chart using D3
  const drawChart = () => {
    if (!chartContainerRef.current || curveData.length === 0) return

    // Clear previous chart
    d3.select(chartContainerRef.current).select('svg').remove()

    // Dimensions
    const margin = { top: 30, right: 60, bottom: 60, left: 70 }
    const width = chartContainerRef.current.clientWidth - margin.left - margin.right
    const height = 400 - margin.top - margin.bottom

    // Create SVG
    const svg = d3.select(chartContainerRef.current)
      .append('svg')
      .attr('width', width + margin.left + margin.right)
      .attr('height', height + margin.top + margin.bottom)

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`)

    // Scales
    const xScale = d3.scaleLinear()
      .domain([0, d3.max(curveData, d => d.years) || 2])
      .range([0, width])

    const yScale = d3.scaleLinear()
      .domain([
        d3.min(curveData, d => d.rate) || 0,
        d3.max(curveData, d => d.rate) || 1
      ])
      .nice()
      .range([height, 0])

    // Line generator
    const line = d3.line<CurvePoint>()
      .x(d => xScale(d.years))
      .y(d => yScale(d.rate))
      .curve(d3.curveCatmullRom.alpha(0.5))

    // Add line
    g.append('path')
      .datum(curveData)
      .attr('fill', 'none')
      .attr('stroke', '#7B1FA2')
      .attr('stroke-width', 2)
      .attr('d', line)

    // Add points
    g.selectAll('.point')
      .data(curveData)
      .enter().append('circle')
      .attr('cx', d => xScale(d.years))
      .attr('cy', d => yScale(d.rate))
      .attr('r', 4)
      .attr('fill', '#7B1FA2')

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
      .text('JPY OIS Yield Curve (Real Bloomberg Data)')
  }

  useEffect(() => {
    fetchCurveData()
  }, [])

  useEffect(() => {
    drawChart()
  }, [curveData, currentTheme])

  return (
    <div style={{
      backgroundColor: currentTheme.surface,
      borderRadius: '8px',
      border: `1px solid ${currentTheme.border}`,
      padding: '16px',
      height: '100%'
    }}>
      <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ margin: 0 }}>Yield Curves (Database Integration Test)</h3>
        <button
          onClick={fetchCurveData}
          disabled={loading}
          style={{
            padding: '8px 16px',
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

      {error && (
        <div style={{ color: '#ef4444', marginBottom: '16px' }}>
          Error: {error}
        </div>
      )}

      {curveData.length > 0 && (
        <div style={{ marginBottom: '16px' }}>
          <div style={{ fontSize: '14px', color: currentTheme.textSecondary }}>
            Data points: {curveData.length} | 
            Range: {curveData[0]?.rate.toFixed(3)}% - {curveData[curveData.length-1]?.rate.toFixed(3)}%
          </div>
        </div>
      )}

      <div ref={chartContainerRef} style={{ width: '100%', height: '400px' }} />
    </div>
  )
}