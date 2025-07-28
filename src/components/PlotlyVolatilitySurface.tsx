import { useEffect, useState } from 'react'
import Plot from 'react-plotly.js'
import { useTheme } from '../contexts/ThemeContext'
import { ValidatedVolatilityData } from '../api/DataValidator'

interface PlotlyVolatilitySurfaceProps {
  surfaceData: ValidatedVolatilityData[]
  selectedPair?: string
}

export function PlotlyVolatilitySurface({ surfaceData, selectedPair }: PlotlyVolatilitySurfaceProps) {
  const [plotData, setPlotData] = useState<any>(null)
  const { currentTheme } = useTheme()

  useEffect(() => {
    console.log('PlotlyVolatilitySurface: surfaceData changed', { 
      dataLength: surfaceData.length, 
      selectedPair,
      firstTenor: surfaceData[0]?.tenor 
    })
    if (surfaceData.length === 0) {
      setPlotData(null)
      return
    }

    // FX Market conventions
    const deltaPoints = [5, 10, 15, 25, 35, 50, 65, 75, 85, 90, 95]
    const deltaLabels = ['5ΔP', '10ΔP', '15ΔP', '25ΔP', '35ΔP', 'ATM', '35ΔC', '25ΔC', '15ΔC', '10ΔC', '5ΔC']
    
    // Build volatility matrix
    const volMatrix: number[][] = []
    const tenorLabels: string[] = []
    
    surfaceData.forEach(tenor => {
      const row: number[] = []
      tenorLabels.push(tenor.tenor)
      
      // Get mid values
      const atmMid = tenor.raw?.atm_bid && tenor.raw?.atm_ask ? (tenor.raw.atm_bid + tenor.raw.atm_ask) / 2 : 0
      
      // Process each delta point
      deltaPoints.forEach(delta => {
        if (!atmMid) {
          row.push(0)
          return
        }
        
        // ATM case
        if (delta === 50) {
          row.push(atmMid)
          return
        }
        
        // Get RR/BF for this delta
        let rr = 0, bf = 0
        const isPut = delta < 50
        const deltaKey = isPut ? delta : (100 - delta)
        
        switch(deltaKey) {
          case 5:
            rr = tenor.raw?.rr_5d_bid && tenor.raw?.rr_5d_ask ? (tenor.raw.rr_5d_bid + tenor.raw.rr_5d_ask) / 2 : 0
            bf = tenor.raw?.bf_5d_bid && tenor.raw?.bf_5d_ask ? (tenor.raw.bf_5d_bid + tenor.raw.bf_5d_ask) / 2 : 0
            break
          case 10:
            rr = tenor.raw?.rr_10d_bid && tenor.raw?.rr_10d_ask ? (tenor.raw.rr_10d_bid + tenor.raw.rr_10d_ask) / 2 : 0
            bf = tenor.raw?.bf_10d_bid && tenor.raw?.bf_10d_ask ? (tenor.raw.bf_10d_bid + tenor.raw.bf_10d_ask) / 2 : 0
            break
          case 15:
            rr = tenor.raw?.rr_15d_bid && tenor.raw?.rr_15d_ask ? (tenor.raw.rr_15d_bid + tenor.raw.rr_15d_ask) / 2 : 0
            bf = tenor.raw?.bf_15d_bid && tenor.raw?.bf_15d_ask ? (tenor.raw.bf_15d_bid + tenor.raw.bf_15d_ask) / 2 : 0
            break
          case 25:
            rr = tenor.raw?.rr_25d_bid && tenor.raw?.rr_25d_ask ? (tenor.raw.rr_25d_bid + tenor.raw.rr_25d_ask) / 2 : 0
            bf = tenor.raw?.bf_25d_bid && tenor.raw?.bf_25d_ask ? (tenor.raw.bf_25d_bid + tenor.raw.bf_25d_ask) / 2 : 0
            break
          case 35:
            rr = tenor.raw?.rr_35d_bid && tenor.raw?.rr_35d_ask ? (tenor.raw.rr_35d_bid + tenor.raw.rr_35d_ask) / 2 : 0
            bf = tenor.raw?.bf_35d_bid && tenor.raw?.bf_35d_ask ? (tenor.raw.bf_35d_bid + tenor.raw.bf_35d_ask) / 2 : 0
            break
        }
        
        // Calculate volatility using FX convention
        const vol = isPut 
          ? atmMid - rr/2 + bf  // Put volatility
          : atmMid + rr/2 + bf  // Call volatility
          
        row.push(vol)
      })
      
      volMatrix.push(row)
    })

    // Create Plotly 3D surface
    const data: Plotly.Data[] = [{
      type: 'surface',
      x: deltaLabels,
      y: tenorLabels,
      z: volMatrix,
      colorscale: [
        [0, '#1a1a1a'],      // Deep carbon black (low vol)
        [0.25, '#2d4a3a'],   // Dark forest green  
        [0.5, '#7A9E65'],    // GZC theme primary green
        [0.75, '#a8c98a'],   // Clean light green
        [1, '#d4e7c5']       // Very light green (high vol)
      ],
      contours: {
        show: true,
        usecolormap: true,
        highlightcolor: "#7A9E65",
        project: { z: false }
      },
      lighting: {
        ambient: 0.7,
        diffuse: 0.9,
        specular: 0.05,
        roughness: 0.3,
        fresnel: 0.2
      },
      lightposition: {
        x: -10000,
        y: 10000,
        z: 5000
      },
      hovertemplate: 
        '<b>%{y}</b><br>' +
        'Strike: <b>%{x}</b><br>' +
        'IV: <b>%{z:.2f}%</b><br>' +
        '<extra></extra>'
    }]

    const layout = {
      showlegend: false,
      scene: {
        xaxis: {
          title: 'Delta',
          ticktext: deltaLabels,
          tickvals: deltaLabels,
          gridcolor: currentTheme.border,
          showbackground: true,
          backgroundcolor: currentTheme.surface,
          titlefont: { color: currentTheme.text },
          tickfont: { color: currentTheme.textSecondary }
        },
        yaxis: {
          title: 'Tenor',
          gridcolor: currentTheme.border,
          showbackground: true,
          backgroundcolor: currentTheme.surface,
          titlefont: { color: currentTheme.text },
          tickfont: { color: currentTheme.textSecondary }
        },
        zaxis: {
          title: 'Implied Volatility %',
          gridcolor: currentTheme.border,
          showbackground: true,
          backgroundcolor: currentTheme.surface,
          titlefont: { color: currentTheme.text },
          tickfont: { color: currentTheme.textSecondary }
        },
        camera: {
          eye: { x: 1.2, y: -1.2, z: 1.5 },
          center: { x: 0, y: 0, z: 0.2 },
          up: { x: 0, y: 0, z: 1 }
        },
        aspectmode: 'manual',
        aspectratio: { x: 1.0, y: 1.0, z: 0.5 }
      },
      paper_bgcolor: currentTheme.background,
      plot_bgcolor: currentTheme.surface,
      margin: { l: 50, r: 50, t: 20, b: 80 },
      font: { color: currentTheme.text }
    }

    const config = {
      displayModeBar: true,
      displaylogo: false,
      modeBarButtonsToRemove: ['toImage', 'sendDataToCloud'],
      modeBarButtons: [['zoom3d', 'pan3d', 'orbitRotation', 'tableRotation', 'resetCameraDefault3d']],
      toImageButtonOptions: {
        format: 'png',
        filename: `${selectedPair || 'volatility'}_surface`,
        height: 600,
        width: 800,
        scale: 1
      }
    }

    // Store data for rendering - ensure no circular references
    setPlotData({ 
      data: JSON.parse(JSON.stringify(data)),
      layout: JSON.parse(JSON.stringify(layout)),
      config: JSON.parse(JSON.stringify(config))
    })
  }, [surfaceData, currentTheme, selectedPair])

  // Debug logging
  console.log('PlotlyVolatilitySurface render:', {
    surfaceDataLength: surfaceData.length,
    hasPlotData: !!plotData,
    selectedPair
  })

  if (surfaceData.length === 0) {
    return <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: currentTheme.textSecondary }}>Loading volatility surface...</div>
  }

  if (!plotData) {
    return <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: currentTheme.textSecondary }}>Generating surface...</div>
  }

  return (
    <Plot
      key={`${selectedPair}-${surfaceData.length}`} // Force re-render on currency change
      data={plotData.data}
      layout={plotData.layout}
      config={plotData.config}
      style={{ width: '100%', height: '100%' }}
      useResizeHandler={true}
      onInitialized={() => {
        // Style the modebar after initialization
        setTimeout(() => {
          const modebar = document.querySelector('.modebar') as HTMLElement
          if (modebar) {
            modebar.style.position = 'absolute'
            modebar.style.left = '15px'
            modebar.style.bottom = '20px'
            modebar.style.top = 'auto'
            modebar.style.flexDirection = 'row'
            modebar.style.display = 'flex'
            modebar.style.gap = '4px'
            modebar.style.zIndex = '1000'
            modebar.style.backgroundColor = 'rgba(255, 255, 255, 0.1)'
            modebar.style.padding = '6px'
            modebar.style.borderRadius = '4px'
            modebar.style.backdropFilter = 'blur(10px)'
            
            const buttons = modebar.querySelectorAll('.modebar-btn path')
            buttons.forEach(button => {
              ;(button as SVGPathElement).style.fill = '#f5f5f5'
            })
            
            const btnElements = modebar.querySelectorAll('.modebar-btn')
            btnElements.forEach(btn => {
              ;(btn as HTMLElement).style.backgroundColor = 'transparent'
              ;(btn as HTMLElement).style.borderRadius = '3px'
              ;(btn as HTMLElement).style.margin = '0 2px'
              ;(btn as HTMLElement).style.padding = '4px'
              ;(btn as HTMLElement).onmouseover = () => {
                ;(btn as HTMLElement).style.backgroundColor = 'rgba(255, 255, 255, 0.2)'
              }
              ;(btn as HTMLElement).onmouseout = () => {
                ;(btn as HTMLElement).style.backgroundColor = 'transparent'
              }
            })
          }
        }, 100)
      }}
    />
  )
}