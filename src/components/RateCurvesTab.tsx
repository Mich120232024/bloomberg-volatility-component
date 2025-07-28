import { useState, useEffect, useRef, useCallback } from 'react'
import { useTheme } from '../contexts/ThemeContext'
import * as d3 from 'd3'

type CurveType = 'yield' | 'forward'
type Currency = 'USD' | 'EUR' | 'GBP' | 'JPY' | 'CHF' | 'AUD' | 'CAD' | 'NZD'

interface CurvePoint {
  tenor: number // Days to maturity
  rate: number  // Rate in %
  label: string // Display label
}

export function RateCurvesTab() {
  const { currentTheme } = useTheme()
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const seriesRefs = useRef<Map<Currency, ISeriesApi<'Line'>>>(new Map())
  
  // Controls
  const [curveType, setCurveType] = useState<CurveType>('yield')
  const [selectedCurrencies, setSelectedCurrencies] = useState<Set<Currency>>(new Set(['USD']))
  const [selectedDate, setSelectedDate] = useState<string>('2025-07-24')
  const [isAnimating, setIsAnimating] = useState(false)
  const [animationSpeed, setAnimationSpeed] = useState(1500) // ms between frames
  
  // Data
  const [curvePointsByCurrency, setCurvePointsByCurrency] = useState<Map<Currency, CurvePoint[]>>(new Map())
  const [availableDates, setAvailableDates] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [historicalDataCache, setHistoricalDataCache] = useState<Map<string, Map<Currency, CurvePoint[]>>>(new Map())

  // Animation
  const animationRef = useRef<NodeJS.Timeout>()
  const currentDateIndex = useRef(0)

  // Curve configuration based on type and currency
  const getCurveConfig = (currency: Currency) => {
    if (curveType === 'yield') {
      const configs = {
        USD: { 
          title: 'USD Treasury Yield Curve',
          instruments: [
            { ticker: 'SOFRRATE Index', tenor: 1, label: 'SOFR' },
            { ticker: 'US0001M Index', tenor: 30, label: '1M' },
            { ticker: 'USGG3M Index', tenor: 90, label: '3M' },
            { ticker: 'USGG6M Index', tenor: 180, label: '6M' },
            { ticker: 'USGG12M Index', tenor: 365, label: '1Y' },
            { ticker: 'USGG2YR Index', tenor: 730, label: '2Y' },
            { ticker: 'USGG3YR Index', tenor: 1095, label: '3Y' },
            { ticker: 'USGG5YR Index', tenor: 1825, label: '5Y' },
            { ticker: 'USGG7YR Index', tenor: 2555, label: '7Y' },
            { ticker: 'USGG10YR Index', tenor: 3650, label: '10Y' },
            { ticker: 'USGG20YR Index', tenor: 7300, label: '20Y' },
            { ticker: 'USGG30YR Index', tenor: 10950, label: '30Y' }
          ]
        },
        EUR: {
          title: 'EUR Government Bond Yield Curve', 
          instruments: [
            { ticker: 'EUR001W Index', tenor: 7, label: '1W' },
            { ticker: 'EUR001M Index', tenor: 30, label: '1M' },
            { ticker: 'EUR002M Index', tenor: 60, label: '2M' },
            { ticker: 'EUR003M Index', tenor: 90, label: '3M' },
            { ticker: 'EUR006M Index', tenor: 180, label: '6M' },
            { ticker: 'EUR012M Index', tenor: 365, label: '1Y' },
            { ticker: 'GDBR2 Index', tenor: 730, label: '2Y' },
            { ticker: 'GDBR3 Index', tenor: 1095, label: '3Y' },
            { ticker: 'GDBR4 Index', tenor: 1460, label: '4Y' },
            { ticker: 'GDBR5 Index', tenor: 1825, label: '5Y' },
            { ticker: 'GDBR6 Index', tenor: 2190, label: '6Y' },
            { ticker: 'GDBR7 Index', tenor: 2555, label: '7Y' },
            { ticker: 'GDBR8 Index', tenor: 2920, label: '8Y' },
            { ticker: 'GDBR9 Index', tenor: 3285, label: '9Y' },
            { ticker: 'GDBR10 Index', tenor: 3650, label: '10Y' },
            { ticker: 'GDBR15 Index', tenor: 5475, label: '15Y' },
            { ticker: 'GDBR20 Index', tenor: 7300, label: '20Y' },
            { ticker: 'GDBR30 Index', tenor: 10950, label: '30Y' }
          ]
        },
        GBP: {
          title: 'GBP Gilt Yield Curve',
          instruments: [
            { ticker: 'BP0001M Index', tenor: 30, label: '1M' },
            { ticker: 'BP0003M Index', tenor: 90, label: '3M' },
            { ticker: 'BP0006M Index', tenor: 180, label: '6M' },
            { ticker: 'BP0012M Index', tenor: 365, label: '1Y' },
            { ticker: 'GUKG2 Index', tenor: 730, label: '2Y' },
            { ticker: 'GUKG3 Index', tenor: 1095, label: '3Y' },
            { ticker: 'GUKG5 Index', tenor: 1825, label: '5Y' },
            { ticker: 'GUKG7 Index', tenor: 2555, label: '7Y' },
            { ticker: 'GUKG10 Index', tenor: 3650, label: '10Y' },
            { ticker: 'GUKG15 Index', tenor: 5475, label: '15Y' },
            { ticker: 'GUKG20 Index', tenor: 7300, label: '20Y' },
            { ticker: 'GUKG30 Index', tenor: 10950, label: '30Y' }
          ]
        },
        JPY: {
          title: 'JPY Government Bond Yield Curve',
          instruments: [
            { ticker: 'GJGB3M Index', tenor: 90, label: '3M' },
            { ticker: 'GJGB6M Index', tenor: 180, label: '6M' },
            { ticker: 'GJGB1 Index', tenor: 365, label: '1Y' },
            { ticker: 'GJGB2 Index', tenor: 730, label: '2Y' },
            { ticker: 'GJGB3 Index', tenor: 1095, label: '3Y' },
            { ticker: 'GJGB4 Index', tenor: 1460, label: '4Y' },
            { ticker: 'GJGB5 Index', tenor: 1825, label: '5Y' },
            { ticker: 'GJGB6 Index', tenor: 2190, label: '6Y' },
            { ticker: 'GJGB7 Index', tenor: 2555, label: '7Y' },
            { ticker: 'GJGB8 Index', tenor: 2920, label: '8Y' },
            { ticker: 'GJGB9 Index', tenor: 3285, label: '9Y' },
            { ticker: 'GJGB10 Index', tenor: 3650, label: '10Y' },
            { ticker: 'GJGB20 Index', tenor: 7300, label: '20Y' },
            { ticker: 'GJGB30 Index', tenor: 10950, label: '30Y' }
          ]
        },
        CHF: {
          title: 'CHF Swiss Government Bond Yield Curve',
          instruments: [
            { ticker: 'SF0001M Index', tenor: 30, label: '1M' },
            { ticker: 'SF0003M Index', tenor: 90, label: '3M' },
            { ticker: 'SF0006M Index', tenor: 180, label: '6M' },
            { ticker: 'SF0012M Index', tenor: 365, label: '1Y' },
            { ticker: 'GSWISS2 Index', tenor: 730, label: '2Y' },
            { ticker: 'GSWISS3 Index', tenor: 1095, label: '3Y' },
            { ticker: 'GSWISS10 Index', tenor: 3650, label: '10Y' },
            { ticker: 'GSWISS15 Index', tenor: 5475, label: '15Y' },
            { ticker: 'GSWISS20 Index', tenor: 7300, label: '20Y' },
            { ticker: 'GSWISS30 Index', tenor: 10950, label: '30Y' }
          ]
        },
        AUD: {
          title: 'AUD Government Bond Yield Curve',
          instruments: [
            { ticker: 'GACGB3M Index', tenor: 90, label: '3M' },
            { ticker: 'GACGB6M Index', tenor: 180, label: '6M' },
            { ticker: 'GACGB1 Index', tenor: 365, label: '1Y' },
            { ticker: 'GACGB2 Index', tenor: 730, label: '2Y' },
            { ticker: 'GACGB3 Index', tenor: 1095, label: '3Y' },
            { ticker: 'GACGB5 Index', tenor: 1825, label: '5Y' },
            { ticker: 'GACGB7 Index', tenor: 2555, label: '7Y' },
            { ticker: 'GACGB10 Index', tenor: 3650, label: '10Y' },
            { ticker: 'GACGB15 Index', tenor: 5475, label: '15Y' },
            { ticker: 'GACGB20 Index', tenor: 7300, label: '20Y' },
            { ticker: 'GACGB30 Index', tenor: 10950, label: '30Y' }
          ]
        },
        CAD: {
          title: 'CAD Government Bond Yield Curve',
          instruments: [
            { ticker: 'GCAN3M Index', tenor: 90, label: '3M' },
            { ticker: 'GCAN6M Index', tenor: 180, label: '6M' },
            { ticker: 'GCAN1YR Index', tenor: 365, label: '1Y' },
            { ticker: 'GCAN2YR Index', tenor: 730, label: '2Y' },
            { ticker: 'GCAN5YR Index', tenor: 1825, label: '5Y' },
            { ticker: 'GCAN10YR Index', tenor: 3650, label: '10Y' },
            { ticker: 'GCAN30YR Index', tenor: 10950, label: '30Y' }
          ]
        },
        NZD: {
          title: 'NZD Government Bond Yield Curve',
          instruments: [
            { ticker: 'GNZGB3M Index', tenor: 90, label: '3M' },
            { ticker: 'GNZGB6M Index', tenor: 180, label: '6M' },
            { ticker: 'GNZGB1 Index', tenor: 365, label: '1Y' },
            { ticker: 'GNZGB2 Index', tenor: 730, label: '2Y' },
            { ticker: 'GNZGB3 Index', tenor: 1095, label: '3Y' },
            { ticker: 'GNZGB5 Index', tenor: 1825, label: '5Y' },
            { ticker: 'GNZGB7 Index', tenor: 2555, label: '7Y' },
            { ticker: 'GNZGB10 Index', tenor: 3650, label: '10Y' },
            { ticker: 'GNZGB15 Index', tenor: 5475, label: '15Y' },
            { ticker: 'GNZGB20 Index', tenor: 7300, label: '20Y' }
          ]
        }
      }
      return configs[currency] || {
        title: `${currency} Yield Curve (Not Available)`,
        instruments: []
      }
    } else {
      // Forward curves use production-verified Bloomberg tickers from RESEARCH_MANAGER
      // Based on s002.groundzero.local GZCDB production database extraction
      // NOTE: CHF rates are negative (normal for Swiss market), swap tickers unavailable on this Bloomberg Terminal
      const configs = {
        USD: {
          title: 'USD Forward Rate Curve (SOFR-based)',
          instruments: [
            { ticker: 'SOFRRATE Index', tenor: 1, label: 'SOFR' },
            { ticker: 'US0001M Index', tenor: 30, label: '1M' },
            { ticker: 'US0003M Index', tenor: 90, label: '3M' },
            { ticker: 'USSO1 Curncy', tenor: 365, label: '1Y OIS' },
            { ticker: 'USSO2 Curncy', tenor: 730, label: '2Y OIS' },
            { ticker: 'USSO5 Curncy', tenor: 1825, label: '5Y OIS' }
          ]
        },
        EUR: {
          title: 'EUR Forward Rate Curve (ESTR-based)',
          instruments: [
            { ticker: 'EUR001M Index', tenor: 30, label: '1M' },
            { ticker: 'EUR003M Index', tenor: 90, label: '3M' },
            { ticker: 'EUR006M Index', tenor: 180, label: '6M' },
            { ticker: 'EUFR0F1 Curncy', tenor: 365, label: '6x12 FRA' },
            { ticker: 'EUSA2 BGN Curncy', tenor: 730, label: '2Y' },
            { ticker: 'EUSA5 BGN Curncy', tenor: 1825, label: '5Y' }
          ]
        },
        GBP: {
          title: 'GBP Forward Rate Curve (SONIA-based)',
          instruments: [
            { ticker: 'BP0006M Index', tenor: 180, label: '6M' },
            { ticker: 'BPSWS1 Curncy', tenor: 365, label: '1Y OIS' },
            { ticker: 'BPSWS2 Curncy', tenor: 730, label: '2Y OIS' },
            { ticker: 'BPSWS5 Curncy', tenor: 1825, label: '5Y OIS' }
          ]
        },
        JPY: {
          title: 'JPY Forward Rate Curve (TONA-based)',
          instruments: [
            { ticker: 'JY0001M Index', tenor: 30, label: '1M' },
            { ticker: 'JY0003M Index', tenor: 90, label: '3M' },
            { ticker: 'JY0006M Index', tenor: 180, label: '6M' },
            { ticker: 'JYSO1 Curncy', tenor: 365, label: '1Y OIS' },
            { ticker: 'JYSO2 Curncy', tenor: 730, label: '2Y OIS' },
            { ticker: 'JYSO5 Curncy', tenor: 1825, label: '5Y OIS' }
          ]
        },
        CHF: {
          title: 'CHF Forward Rate Curve (SARON-based)',
          instruments: [
            { ticker: 'SSARON Index', tenor: 1, label: 'SARON ON' },
            { ticker: 'SRFXON1 Index', tenor: 1, label: 'SARON 12pm Fix' },
            { ticker: 'SRFXON2 Index', tenor: 1, label: 'SARON 4pm Fix' },
            { ticker: 'SRFXON3 Index', tenor: 1, label: 'SARON 6pm Fix' },
            { ticker: 'SF0001M Index', tenor: 30, label: '1M' },
            { ticker: 'SF0003M Index', tenor: 90, label: '3M' },
            { ticker: 'SF0006M Index', tenor: 180, label: '6M' },
            { ticker: 'SF0012M Index', tenor: 365, label: '12M' }
          ]
        },
        AUD: {
          title: 'AUD Forward Rate Curve (Bank bills + swaps)',
          instruments: [
            { ticker: 'ADBB1M Curncy', tenor: 30, label: '1M' },
            { ticker: 'ADBB3M Curncy', tenor: 90, label: '3M' },
            { ticker: 'ADBB6M Curncy', tenor: 180, label: '6M' },
            { ticker: 'ADSWAP2 Curncy', tenor: 730, label: '2Y' },
            { ticker: 'ADSWAP5 Curncy', tenor: 1825, label: '5Y' }
          ]
        },
        CAD: {
          title: 'CAD Forward Rate Curve (CDOR-based, Limited)',
          instruments: [
            { ticker: 'CDOR01 Index', tenor: 30, label: '1M CDOR' },
            { ticker: 'CDOR03 Index', tenor: 90, label: '3M CDOR' }
          ]
        },
        NZD: {
          title: 'NZD Forward Rate Curve (Limited)',
          instruments: [
            { ticker: 'NZOCRS Index', tenor: 30, label: '1M OCR' },
            { ticker: 'NZOCRS Index', tenor: 90, label: '3M OCR' }
          ]
        }
      }
      return configs[currency] || {
        title: `${currency} Forward Rate Curve (Not Available)`,
        instruments: []
      }
    }
  }

  // Fetch curve data from Bloomberg API for multiple currencies
  const fetchCurveData = async (date: string, useHistorical: boolean = false) => {
    console.log(`Fetching curve data for ${Array.from(selectedCurrencies)} on ${date}, historical: ${useHistorical}`)
    setLoading(true)
    setError(null)
    
    try {
      const newCurveData = new Map<Currency, CurvePoint[]>()
      
      // Fetch data for each selected currency
      for (const currency of selectedCurrencies) {
        const config = getCurveConfig(currency)
        const tickers = config.instruments.map(inst => inst.ticker)
        
        let endpoint = 'http://localhost:8000/api/bloomberg/reference'
        let body: any = {
          securities: tickers,
          fields: ['PX_LAST', 'PX_BID', 'PX_ASK']
        }
        
        // Use historical endpoint for past dates
        if (useHistorical && date !== new Date().toISOString().split('T')[0]) {
          // Historical endpoint requires fetching each security separately
          const historicalPromises = tickers.map(async (ticker) => {
            const histEndpoint = 'http://localhost:8000/api/bloomberg/historical'
          const histResponse = await fetch(histEndpoint, {
              method: 'POST',
              headers: {
                'Authorization': 'Bearer test',
                'Content-Type': 'application/json'
              },
              body: JSON.stringify({
                security: ticker,
                fields: ['PX_LAST'],
                start_date: date.replace(/-/g, ''),
                end_date: date.replace(/-/g, ''),
                periodicity: 'DAILY'
              })
            })
            const histData = await histResponse.json()
            return { ticker, data: histData }
          })
          
          const historicalResults = await Promise.all(historicalPromises)
          console.log(`Historical data for ${currency}: fetched ${historicalResults.length} securities`)
          
          // Process historical data with fallback to current data for missing points
          const points: CurvePoint[] = []
          const missingTickers: string[] = []
          
          historicalResults.forEach((result, index) => {
            const instrument = config.instruments[index]
            if (!instrument) return
            
            if (result.data?.success && result.data?.data?.data?.[0]) {
              const value = result.data.data.data[0].PX_LAST
              if (value !== null && value !== undefined) {
                let rate = value
                
                if (instrument.ticker.includes('Govt') && rate > 50) {
                  const yearsToMaturity = instrument.tenor / 365
                  rate = ((100 - rate) / rate) * (100 / yearsToMaturity)
                }
                
                points.push({
                  tenor: instrument.tenor,
                  rate: rate,
                  label: instrument.label
                })
              }
            } else {
              // Track missing tickers for fallback
              missingTickers.push(instrument.ticker)
              console.warn(`Historical data missing for ${instrument.ticker}, will try current data`)
            }
          })
          
          // Fallback: fetch current data for missing historical points
          if (missingTickers.length > 0) {
            console.log(`Fetching current data for ${missingTickers.length} missing historical tickers`)
            try {
              const fallbackResponse = await fetch('http://20.172.249.92:8080/api/bloomberg/reference', {
                method: 'POST',
                headers: {
                  'Authorization': 'Bearer test',
                  'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                  securities: missingTickers,
                  fields: ['PX_LAST']
                })
              })
              
              const fallbackData = await fallbackResponse.json()
              if (fallbackData.success && fallbackData.data?.securities_data) {
                fallbackData.data.securities_data.forEach((item: any) => {
                  if (item.success && item.fields?.PX_LAST) {
                    const instrument = config.instruments.find(inst => inst.ticker === item.security)
                    if (instrument) {
                      points.push({
                        tenor: instrument.tenor,
                        rate: item.fields.PX_LAST,
                        label: instrument.label
                      })
                    }
                  }
                })
              }
            } catch (fallbackError) {
              console.error('Fallback current data fetch failed:', fallbackError)
            }
          }
          
          points.sort((a, b) => a.tenor - b.tenor)
          newCurveData.set(currency, points)
        } else {
          // Current data
          const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
              'Authorization': 'Bearer test',
              'Content-Type': 'application/json'
            },
            body: JSON.stringify(body)
          })
          
          if (!response.ok) {
            throw new Error(`Bloomberg API error: ${response.status}`)
          }
          
          const data = await response.json()
          
          if (data.success && data.data) {
            const points: CurvePoint[] = []
            const securities = data.data.securities_data
            
            securities?.forEach((item: any, index: number) => {
              const instrument = config.instruments[index]
              if (!instrument) return
              
              if (!item.success || !item.fields?.PX_LAST) {
                console.warn(`No data for ${item.security}`)
                return
              }
              
              let rate = item.fields.PX_LAST
              
              if (item.security.includes('Govt') && rate > 50) {
                const yearsToMaturity = instrument.tenor / 365
                rate = ((100 - rate) / rate) * (100 / yearsToMaturity)
              }
              
              points.push({
                tenor: instrument.tenor,
                rate: rate,
                label: instrument.label
              })
            })
            
            points.sort((a, b) => a.tenor - b.tenor)
            newCurveData.set(currency, points)
          } else {
            console.warn(`No data for ${currency}`)
            newCurveData.set(currency, [])
          }
        }
      }
      
      setCurvePointsByCurrency(newCurveData)
      updateMultiCurrencyChart(newCurveData)
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      setError(`Failed to fetch curve data: ${errorMessage}`)
      console.error('Curve data fetch error:', error)
    } finally {
      setLoading(false)
    }
  }

  // Initialize chart
  useEffect(() => {
    if (!chartContainerRef.current) return

    // Create tooltip element
    const toolTip = document.createElement('div')
    toolTip.style.cssText = `
      position: absolute;
      display: none;
      padding: 10px;
      box-sizing: border-box;
      font-size: 11px;
      text-align: left;
      z-index: 1000;
      pointer-events: none;
      background: ${currentTheme.surface};
      color: ${currentTheme.text};
      border: 1px solid ${currentTheme.border};
      border-radius: 6px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.15);
      backdrop-filter: blur(10px);
    `
    chartContainerRef.current.appendChild(toolTip)

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: currentTheme.surface },
        textColor: currentTheme.text,
      },
      grid: {
        vertLines: { 
          color: currentTheme.border,
          style: 1, // Dashed
          visible: true
        },
        horzLines: { 
          color: currentTheme.border,
          style: 1, // Dashed  
          visible: true
        },
      },
      rightPriceScale: {
        borderColor: currentTheme.border,
        borderVisible: false,
        title: curveType === 'yield' ? 'Yield (%)' : 'Forward Points',
        scaleMargins: {
          top: 0.1,
          bottom: 0.1,
        },
      },
      timeScale: {
        borderColor: currentTheme.border,
        borderVisible: false,
        rightOffset: 12,
        barSpacing: 10,
        fixLeftEdge: true,
        fixRightEdge: true,
        lockVisibleTimeRangeOnResize: true,
        timeVisible: false,
        secondsVisible: false,
      },
      crosshair: {
        mode: 1,
        vertLine: {
          width: 1,
          color: currentTheme.textSecondary,
          style: 2, // Dotted
          labelBackgroundColor: currentTheme.surface,
        },
        horzLine: {
          width: 1,
          color: currentTheme.textSecondary,
          style: 2, // Dotted
          labelBackgroundColor: currentTheme.surface,
        },
      },
    })

    chartRef.current = chart
    
    // Clear existing series
    seriesRefs.current.clear()

    // Store current data for tooltip access
    let currentCurveData: Map<Currency, CurvePoint[]> = new Map()

    // Tooltip handler
    chart.subscribeCrosshairMove((param) => {
      if (
        param.point === undefined ||
        !param.time ||
        param.point.x < 0 ||
        param.point.y < 0
      ) {
        toolTip.style.display = 'none'
        return
      }

      // Get data from all series at this point
      const seriesData: { currency: string; value: number | null }[] = []
      seriesRefs.current.forEach((series, currency) => {
        const data = param.seriesData.get(series)
        if (data) {
          seriesData.push({
            currency,
            value: (data as any).value || null
          })
        }
      })

      if (seriesData.length === 0) {
        toolTip.style.display = 'none'
        return
      }

      // Get tenor label from current data
      let tenorLabel = ''
      const timeIndex = param.time as number
      
      // Find the first series that has data to get the label
      const storedData = (window as any).__currentCurveData as Map<Currency, CurvePoint[]>
      if (storedData) {
        storedData.forEach((points) => {
          if (points[timeIndex]) {
            tenorLabel = points[timeIndex].label
          }
        })
      }
      
      if (!tenorLabel) {
        tenorLabel = `Index ${timeIndex}`
      }

      toolTip.innerHTML = `
        <div style="font-weight: 600; margin-bottom: 6px;">
          ${tenorLabel}
        </div>
        ${seriesData.map(({ currency, value }) => `
          <div style="display: flex; justify-content: space-between; gap: 20px; margin: 2px 0;">
            <span style="color: ${currentTheme.textSecondary}">${currency}:</span>
            <span style="font-weight: 500">${value !== null ? value.toFixed(3) + '%' : 'N/A'}</span>
          </div>
        `).join('')}
        <div style="margin-top: 6px; padding-top: 6px; border-top: 1px solid ${currentTheme.border}; font-size: 10px; color: ${currentTheme.textSecondary}">
          ${selectedDate}
        </div>
      `

      const coordinate = chart.priceToCoordinate(seriesData[0].value || 0)
      let top = param.point.y
      
      if (coordinate !== null) {
        top = coordinate
      }

      toolTip.style.display = 'block'
      toolTip.style.left = param.point.x + 15 + 'px'
      toolTip.style.top = top - 50 + 'px'
    })

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ 
          width: chartContainerRef.current.clientWidth,
          height: chartContainerRef.current.clientHeight 
        })
      }
    }
    
    window.addEventListener('resize', handleResize)
    handleResize() // Initial sizing

    return () => {
      window.removeEventListener('resize', handleResize)
      chart.remove()
    }
  }, [currentTheme, curveType])

  // Update chart data for multiple currencies
  const updateMultiCurrencyChart = (currencyData: Map<Currency, CurvePoint[]>) => {
    if (!chartRef.current) return
    
    // Store data for tooltip access
    ;(window as any).__currentCurveData = currencyData
    
    // Clear existing series
    seriesRefs.current.forEach(series => {
      chartRef.current?.removeSeries(series)
    })
    seriesRefs.current.clear()
    
    // Modern color scheme for different currencies
    const currencyColors: { [key in Currency]: string } = {
      USD: currentTheme.primary || '#7A9E65',  // Green
      EUR: '#4ECDC4',  // Teal
      GBP: '#F39C12',  // Orange
      JPY: '#E74C3C',  // Red
      CHF: '#9B59B6',  // Purple
      AUD: '#3498DB',  // Blue
      CAD: '#E91E63',  // Pink
      NZD: '#00BCD4'   // Cyan
    }
    
    let allPoints: CurvePoint[] = []
    
    // Create a series for each currency
    currencyData.forEach((points, currency) => {
      if (points.length === 0) return
      
      const color = currencyColors[currency]
      
      const lineSeries = chartRef.current!.addSeries(LineSeries, {
        color,
        lineWidth: 1.5,
        lineStyle: 0, // LineStyle.Solid = 0
        crosshairMarkerVisible: true,
        crosshairMarkerRadius: 4,
        crosshairMarkerBorderWidth: 1.5,
        crosshairMarkerBackgroundColor: currentTheme.background,
        title: currency,
        lastValueVisible: true,
        priceLineVisible: false
      })
      
      // Convert to lightweight-charts format using index as time
      // This prevents the chart from interpreting tenor days as Unix timestamps
      const chartData = points.map((point, index) => ({
        time: index, // Use index instead of tenor to avoid date interpretation
        value: point.rate
      }))
      
      lineSeries.setData(chartData)
      seriesRefs.current.set(currency, lineSeries)
      
      // Collect all points for axis formatting (use the first currency's points for labels)
      if (allPoints.length === 0) {
        allPoints = points
      }
    })
    
    // Set custom formatter for x-axis labels after data is loaded
    if (chartRef.current && allPoints.length > 0) {
      // Create index-based mapping for labels
      const indexToLabel: { [key: number]: string } = {}
      allPoints.forEach((point, index) => {
        indexToLabel[index] = point.label
      })
      
      // Apply custom formatter
      chartRef.current.timeScale().applyOptions({
        tickMarkFormatter: (time: any) => {
          return indexToLabel[time] || ''
        },
        visible: true,
        borderVisible: false
      })
      
      // Fit content to show all data
      chartRef.current.timeScale().fitContent()
    }
  }

  // Animation controls
  const startAnimation = () => {
    if (availableDates.length === 0) {
      console.log('No available dates for animation')
      return
    }
    
    console.log(`Starting animation with ${availableDates.length} dates`)
    setIsAnimating(true)
    currentDateIndex.current = 0
    
    animationRef.current = setInterval(() => {
      const nextDate = availableDates[currentDateIndex.current]
      console.log(`Animation: fetching date ${nextDate} (${currentDateIndex.current + 1}/${availableDates.length})`)
      setSelectedDate(nextDate)
      fetchCurveData(nextDate, true) // Use historical data for animation
      
      currentDateIndex.current = (currentDateIndex.current + 1) % availableDates.length
    }, animationSpeed)
  }

  const stopAnimation = () => {
    console.log('Stopping animation')
    setIsAnimating(false)
    if (animationRef.current) {
      clearInterval(animationRef.current)
      animationRef.current = undefined
    }
  }

  // Initialize with historical dates and current data
  useEffect(() => {
    const dates = []
    const today = new Date()
    
    // Get last 12 Wednesdays for weekly animation
    for (let i = 12; i >= 0; i--) {
      const targetDate = new Date(today)
      targetDate.setDate(today.getDate() - (i * 7))
      
      // Adjust to nearest Wednesday (day 3)
      const dayOfWeek = targetDate.getDay()
      const daysToWednesday = (3 - dayOfWeek + 7) % 7
      if (daysToWednesday !== 0) {
        targetDate.setDate(targetDate.getDate() + daysToWednesday - 7)
      }
      
      dates.push(targetDate.toISOString().split('T')[0])
    }
    
    setAvailableDates(dates)
    fetchCurveData(selectedDate)
  }, [curveType, selectedCurrencies]) // eslint-disable-line react-hooks/exhaustive-deps

  // Cleanup animation
  useEffect(() => {
    return () => {
      if (animationRef.current) {
        clearInterval(animationRef.current)
      }
    }
  }, [])

  const config = getCurveConfig()

  return (
    <div style={{ 
      backgroundColor: currentTheme.surface,
      borderRadius: '8px',
      border: `1px solid ${currentTheme.border}`,
      height: '100%',
      overflow: 'hidden',
      display: 'flex',
      flexDirection: 'column'
    }}>
      {/* Header */}
      <div style={{
        padding: '16px',
        borderBottom: `1px solid ${currentTheme.border}`,
        backgroundColor: currentTheme.surface
      }}>
        <h3 style={{ 
          margin: 0, 
          fontSize: '16px', 
          fontWeight: '600',
          color: currentTheme.text 
        }}>
          {curveType === 'yield' ? 'Yield Curves' : 'Forward Rate Curves'}
        </h3>
      </div>

      {/* Main Content Area */}
      <div style={{ 
        flex: 1, 
        display: 'flex', 
        gap: '16px',
        padding: '16px',
        overflow: 'hidden'
      }}>
        {/* Chart Container */}
        <div style={{ 
          flex: 1, 
          position: 'relative',
          minHeight: '400px'
        }}>
          <div 
            ref={chartContainerRef}
            style={{
              width: '100%',
              height: '100%',
              backgroundColor: currentTheme.background,
              borderRadius: '6px',
              border: `1px solid ${currentTheme.border}`
            }}
          />
          {loading && (
            <div style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: currentTheme.background + 'dd',
              borderRadius: '6px'
            }}>
              <div style={{ color: currentTheme.textSecondary }}>
                Loading rate curves...
              </div>
            </div>
          )}
          {error && (
            <div style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              color: '#e74c3c',
              textAlign: 'center'
            }}>
              {error}
            </div>
          )}
        </div>

        {/* Controls Panel - Right Side */}
        <div style={{
          width: '280px',
          backgroundColor: currentTheme.background,
          padding: '16px',
          borderRadius: '6px',
          border: `1px solid ${currentTheme.border}`,
          display: 'flex',
          flexDirection: 'column',
          gap: '16px',
          overflowY: 'auto'
        }}>
          {/* Curve Type Selector */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={{ fontSize: '12px', fontWeight: '600', color: currentTheme.textSecondary }}>
              Curve Type
            </label>
            <select
              value={curveType}
              onChange={(e) => setCurveType(e.target.value as CurveType)}
              style={{
                backgroundColor: currentTheme.background,
                color: currentTheme.text,
                border: `1px solid ${currentTheme.border}`,
                borderRadius: '4px',
                padding: '8px 12px',
                fontSize: '12px'
              }}
            >
              <option value="yield">Yield Curve</option>
              <option value="forward">Forward Curve</option>
            </select>
          </div>

          {/* Currency Multi-Selector */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <label style={{ fontSize: '12px', fontWeight: '600', color: currentTheme.textSecondary }}>
              Currencies ({selectedCurrencies.size} selected)
            </label>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(2, 1fr)',
              gap: '4px'
            }}>
              {(['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'AUD', 'CAD', 'NZD'] as Currency[]).map(curr => (
                <label key={curr} style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '8px 10px',
                  cursor: 'pointer',
                  fontSize: '12px',
                  backgroundColor: selectedCurrencies.has(curr) ? currentTheme.primary + '20' : currentTheme.surface,
                  border: `1px solid ${selectedCurrencies.has(curr) ? currentTheme.primary : currentTheme.border}`,
                  borderRadius: '6px',
                  transition: 'all 0.2s ease',
                  ':hover': {
                    backgroundColor: currentTheme.primary + '10'
                  }
                }}>
                  <div style={{
                    width: '12px',
                    height: '12px',
                    borderRadius: '2px',
                    backgroundColor: selectedCurrencies.has(curr) ? currentTheme.primary : 'transparent',
                    border: `2px solid ${selectedCurrencies.has(curr) ? currentTheme.primary : currentTheme.border}`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '8px',
                    color: 'white'
                  }}>
                    {selectedCurrencies.has(curr) ? '✓' : ''}
                  </div>
                  <input
                    type="checkbox"
                    checked={selectedCurrencies.has(curr)}
                    onChange={(e) => {
                      const newCurrencies = new Set(selectedCurrencies)
                      if (e.target.checked) {
                        newCurrencies.add(curr)
                      } else {
                        newCurrencies.delete(curr)
                      }
                      // Ensure at least one currency is selected
                      if (newCurrencies.size > 0) {
                        setSelectedCurrencies(newCurrencies)
                      }
                    }}
                    style={{ display: 'none' }}
                  />
                  <span style={{ 
                    color: selectedCurrencies.has(curr) ? currentTheme.primary : currentTheme.text,
                    fontWeight: selectedCurrencies.has(curr) ? '600' : '400'
                  }}>
                    {curr}
                  </span>
                </label>
              ))}
            </div>
            <div style={{ 
              fontSize: '10px', 
              color: currentTheme.textSecondary,
              fontStyle: 'italic',
              lineHeight: '1.3'
            }}>
              {Array.from(selectedCurrencies).slice(0, 2).map(curr => getCurveConfig(curr).title).join(', ')}
              {selectedCurrencies.size > 2 && ` +${selectedCurrencies.size - 2} more`}
            </div>
          </div>

          {/* Date Selector */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={{ fontSize: '12px', fontWeight: '600', color: currentTheme.textSecondary }}>
              Date
            </label>
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => {
                setSelectedDate(e.target.value)
                fetchCurveData(e.target.value, true)
              }}
              style={{
                backgroundColor: currentTheme.background,
                color: currentTheme.text,
                border: `1px solid ${currentTheme.border}`,
                borderRadius: '4px',
                padding: '8px 12px',
                fontSize: '12px'
              }}
            />
          </div>

          {/* Currency Legend */}
          {selectedCurrencies.size > 0 && (
            <div style={{ 
              display: 'flex', 
              flexDirection: 'column', 
              gap: '4px',
              marginTop: 'auto'
            }}>
              <label style={{ fontSize: '11px', fontWeight: '600', color: currentTheme.textSecondary }}>
                Active Curves
              </label>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
                {Array.from(selectedCurrencies).map(currency => {
                  const color = {
                    USD: currentTheme.primary || '#7A9E65',
                    EUR: '#4ECDC4',
                    GBP: '#F39C12',
                    JPY: '#E74C3C',
                    CHF: '#9B59B6',
                    AUD: '#3498DB',
                    CAD: '#E91E63',
                    NZD: '#00BCD4'
                  }[currency]
                  
                  return (
                    <div key={currency} style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      gap: '8px',
                      fontSize: '11px'
                    }}>
                      <div style={{
                        width: '12px',
                        height: '2px',
                        backgroundColor: color,
                        borderRadius: '1px'
                      }} />
                      <span style={{ color: currentTheme.text }}>{currency}</span>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Market Notes */}
          {curveType === 'forward' && selectedCurrencies.has('CHF') && (
            <div style={{
              backgroundColor: currentTheme.background,
              border: `1px solid ${currentTheme.border}`,
              borderRadius: '4px',
              padding: '8px',
              fontSize: '10px',
              color: currentTheme.textSecondary,
              lineHeight: '1.4'
            }}>
              <div style={{ fontWeight: '600', marginBottom: '4px', color: currentTheme.text }}>
                ℹ️ CHF Market Note
              </div>
              Negative CHF rates (-0.70%) are normal for Swiss Franc money market. 
              Full SFSNT OIS curve unavailable on this Bloomberg Terminal - showing available money market rates only.
            </div>
          )}

        </div>
      </div>


    </div>
  )
}