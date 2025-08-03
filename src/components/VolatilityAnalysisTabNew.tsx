import { useState, useEffect, useRef } from 'react'
import { useTheme } from '../contexts/ThemeContext'
import { bloombergAPI } from '../api/bloomberg'
import { ValidatedVolatilityData } from '../api/DataValidator'
import * as d3 from 'd3'
import { PlotlyVolatilitySurface } from './PlotlyVolatilitySurface'
import { ALL_FX_PAIRS } from '../constants/currencies'

const MAJOR_PAIRS = [...ALL_FX_PAIRS]

const TENORS = ['ON', '1W', '2W', '1M', '2M', '3M', '6M', '9M', '1Y', '18M', '2Y']

export function VolatilityAnalysisTabNew() {
  const { currentTheme } = useTheme()
  
  // State
  const [selectedPair, setSelectedPair] = useState('EURUSD')
  const [surfaceData, setSurfaceData] = useState<ValidatedVolatilityData[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)
  
  // Chart refs
  const smileChartRef = useRef<HTMLDivElement>(null)
  const termChartRef = useRef<HTMLDivElement>(null)
  
  // Fetch volatility data
  const fetchData = async () => {
    console.log('🚀 Fetching data for', selectedPair)
    setLoading(true)
    setError(null)
    
    try {
      const data = await bloombergAPI.getVolatilitySurface(selectedPair)
      console.log('✅ Data received:', data.length, 'tenors')
      setSurfaceData(data)
      setLastUpdate(new Date())
    } catch (err) {
      console.error('❌ Error fetching data:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch data')
    } finally {
      setLoading(false)
    }
  }
  
  // Draw volatility smile chart
  const drawSmileChart = () => {
    if (!smileChartRef.current || !surfaceData.length) return
    
    console.log('📊 Drawing smile chart')
    const container = smileChartRef.current
    d3.select(container).selectAll('*').remove()
    
    // Simple implementation - just show ATM volatilities
    const margin = { top: 20, right: 20, bottom: 40, left: 50 }
    const width = container.clientWidth - margin.left - margin.right
    const height = 250 - margin.top - margin.bottom
    
    const svg = d3.select(container)
      .append('svg')
      .attr('width', width + margin.left + margin.right)
      .attr('height', height + margin.top + margin.bottom)
    
    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`)
    
    // Extract ATM data for 1M tenor
    const atmData = surfaceData
      .filter(d => d.tenor === '1M')
      .map(d => ({ tenor: d.tenor, atm: d.atm_mid || 0 }))
    
    if (atmData.length === 0) {
      g.append('text')
        .attr('x', width/2)
        .attr('y', height/2)
        .attr('text-anchor', 'middle')
        .style('fill', currentTheme.textSecondary)
        .text('No ATM data available')
      return
    }
    
    // Simple text display
    g.append('text')
      .attr('x', width/2)
      .attr('y', height/2)
      .attr('text-anchor', 'middle')
      .style('fill', currentTheme.text)
      .style('font-size', '16px')
      .text(`${selectedPair} 1M ATM: ${atmData[0]?.atm.toFixed(2)}%`)
  }
  
  // Draw term structure chart
  const drawTermChart = () => {
    if (!termChartRef.current || !surfaceData.length) return
    
    console.log('📊 Drawing term structure chart')
    const container = termChartRef.current
    d3.select(container).selectAll('*').remove()
    
    const margin = { top: 20, right: 20, bottom: 40, left: 50 }
    const width = container.clientWidth - margin.left - margin.right
    const height = 250 - margin.top - margin.bottom
    
    const svg = d3.select(container)
      .append('svg')
      .attr('width', width + margin.left + margin.right)
      .attr('height', height + margin.top + margin.bottom)
    
    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`)
    
    // Convert tenor to days for x-axis
    const tenorToDays = (tenor: string): number => {
      const map: Record<string, number> = {
        'ON': 1, '1W': 7, '2W': 14, '1M': 30, '2M': 60, '3M': 90,
        '6M': 180, '9M': 270, '1Y': 365, '18M': 547, '2Y': 730
      }
      return map[tenor] || 30
    }
    
    // Prepare data
    const termData = surfaceData
      .filter(d => d.atm_mid && d.atm_mid > 0)
      .map(d => ({
        tenor: d.tenor,
        days: tenorToDays(d.tenor),
        volatility: d.atm_mid || 0
      }))
      .sort((a, b) => a.days - b.days)
    
    console.log('📈 Term structure data:', termData)
    
    if (termData.length === 0) {
      g.append('text')
        .attr('x', width/2)
        .attr('y', height/2)
        .attr('text-anchor', 'middle')
        .style('fill', currentTheme.textSecondary)
        .text('No term structure data available')
      return
    }
    
    // Scales
    const xScale = d3.scaleLinear()
      .domain(d3.extent(termData, d => d.days) as [number, number])
      .range([0, width])
    
    const yScale = d3.scaleLinear()
      .domain(d3.extent(termData, d => d.volatility) as [number, number])
      .range([height, 0])
    
    // Line generator
    const line = d3.line<typeof termData[0]>()
      .x(d => xScale(d.days))
      .y(d => yScale(d.volatility))
      .curve(d3.curveMonotoneX)
    
    // Draw line
    g.append('path')
      .datum(termData)
      .attr('fill', 'none')
      .attr('stroke', currentTheme.primary)
      .attr('stroke-width', 2)
      .attr('d', line)
    
    // Draw points
    g.selectAll('.point')
      .data(termData)
      .enter().append('circle')
      .attr('class', 'point')
      .attr('cx', d => xScale(d.days))
      .attr('cy', d => yScale(d.volatility))
      .attr('r', 3)
      .attr('fill', currentTheme.primary)
    
    // X-axis
    g.append('g')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(xScale))
      .selectAll('text')
      .style('fill', currentTheme.text)
    
    // Y-axis
    g.append('g')
      .call(d3.axisLeft(yScale))
      .selectAll('text')
      .style('fill', currentTheme.text)
    
    // Axis labels
    g.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('y', 0 - margin.left)
      .attr('x', 0 - (height / 2))
      .attr('dy', '1em')
      .style('text-anchor', 'middle')
      .style('fill', currentTheme.text)
      .text('Volatility (%)')
    
    g.append('text')
      .attr('transform', `translate(${width / 2}, ${height + margin.bottom - 5})`)
      .style('text-anchor', 'middle')
      .style('fill', currentTheme.text)
      .text('Days to Expiry')
  }
  
  // Effects
  useEffect(() => {
    fetchData()
  }, [selectedPair])
  
  useEffect(() => {
    if (surfaceData.length > 0 && !loading) {
      console.log('🎯 Drawing charts with data:', surfaceData.length)
      setTimeout(() => {
        drawSmileChart()
        drawTermChart()
      }, 100)
    }
  }, [surfaceData, loading, currentTheme])
  
  return (
    <div style={{
      backgroundColor: currentTheme.surface,
      borderRadius: '8px',
      border: `1px solid ${currentTheme.border}`,
      overflow: 'hidden',
      height: '100%'
    }}>
      {/* Header */}
      <div style={{
        padding: '16px',
        borderBottom: `1px solid ${currentTheme.border}`,
        backgroundColor: currentTheme.background,
        display: 'flex',
        gap: '16px',
        alignItems: 'center'
      }}>
        <div>
          <label style={{ fontSize: '12px', color: currentTheme.textSecondary, marginRight: '8px' }}>
            Currency Pair:
          </label>
          <select
            value={selectedPair}
            onChange={(e) => setSelectedPair(e.target.value)}
            style={{
              backgroundColor: currentTheme.background,
              color: currentTheme.text,
              border: `1px solid ${currentTheme.border}`,
              borderRadius: '4px',
              padding: '4px 8px',
              fontSize: '12px'
            }}
          >
            {MAJOR_PAIRS.map(pair => (
              <option key={pair} value={pair}>{pair}</option>
            ))}
          </select>
        </div>
        
        <button
          onClick={fetchData}
          disabled={loading}
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
        
        {lastUpdate && (
          <span style={{ fontSize: '11px', color: currentTheme.textSecondary }}>
            Updated: {lastUpdate.toLocaleTimeString()}
          </span>
        )}
      </div>
      
      {/* Content */}
      <div style={{ display: 'flex', height: 'calc(100% - 80px)' }}>
        {/* Left Column: 2D Charts */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '16px' }}>
          {/* Volatility Smile */}
          <div style={{
            flex: 1,
            backgroundColor: currentTheme.background,
            padding: '12px',
            borderRadius: '6px',
            border: `1px solid ${currentTheme.border}`,
            marginBottom: '8px'
          }}>
            <h3 style={{ 
              fontSize: '13px', 
              fontWeight: '600', 
              margin: '0 0 8px 0',
              color: currentTheme.text
            }}>
              Volatility Smile - {selectedPair}
            </h3>
            <div ref={smileChartRef} style={{ width: '100%', height: '250px' }} />
          </div>
          
          {/* Term Structure */}
          <div style={{
            flex: 1,
            backgroundColor: currentTheme.background,
            padding: '12px',
            borderRadius: '6px',
            border: `1px solid ${currentTheme.border}`
          }}>
            <h3 style={{ 
              fontSize: '13px', 
              fontWeight: '600', 
              margin: '0 0 8px 0',
              color: currentTheme.text
            }}>
              Term Structure - {selectedPair}
            </h3>
            <div ref={termChartRef} style={{ width: '100%', height: '250px' }} />
          </div>
        </div>
        
        {/* Right Column: 3D Surface */}
        <div style={{ flex: 1, padding: '16px' }}>
          <div style={{
            backgroundColor: currentTheme.background,
            padding: '12px',
            borderRadius: '6px',
            border: `1px solid ${currentTheme.border}`,
            height: '100%'
          }}>
            <h3 style={{ 
              fontSize: '13px', 
              fontWeight: '600', 
              margin: '0 0 8px 0',
              color: currentTheme.text
            }}>
              3D Volatility Surface - {selectedPair}
            </h3>
            <div style={{ height: 'calc(100% - 24px)' }}>
              {surfaceData.length > 0 ? (
                <PlotlyVolatilitySurface
                  surfaceData={surfaceData}
                  selectedPair={selectedPair}
                />
              ) : (
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  height: '100%',
                  color: currentTheme.textSecondary
                }}>
                  {loading ? 'Loading surface...' : error ? `Error: ${error}` : 'No data available'}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}