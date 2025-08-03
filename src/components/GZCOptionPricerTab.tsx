import { useState, useEffect } from 'react'
import { useTheme } from '../contexts/ThemeContext'
import { adjustToBusinessDay, getBusinessDaysAgo, isBusinessDay } from '../utils/businessDays'
import { ALL_FX_PAIRS, G10_CURRENCIES, EMERGING_MARKET_CURRENCIES, PRECIOUS_METALS } from '../constants/currencies'

// All supported currencies
const SUPPORTED_CURRENCIES = [...G10_CURRENCIES, ...EMERGING_MARKET_CURRENCIES, ...PRECIOUS_METALS]

// FX pairs from constants
const SUPPORTED_FX_PAIRS = [...ALL_FX_PAIRS]

interface OVMLData {
  // Inputs
  priceDate: Date
  asset: string
  spot: number
  style: 'European' | 'American'
  direction: 'Buy' | 'Sell'
  optionType: 'Call' | 'Put'
  expiry: Date
  delivery: Date
  strike: number
  notional: number
  model: string
  
  // Market Data
  volatility: number
  points: number
  forward: number
  eurDepo: number
  usdDepo: number
  
  // Results
  premium: number
  premiumCurrency: string
  premiumPercent: number
  premiumPips: number
  
  // Greeks
  delta: number
  deltaNotional: number
  gamma: number
  gammaPct: number
  vega: number
  vegaNotional: number
  theta: number
  thetaNotional: number
  rho: number
  rhoNotional: number
}

export function GZCOptionPricerTab() {
  const { currentTheme } = useTheme()
  
  // Initialize with default values matching Bloomberg screen
  const [ovmlData, setOvmlData] = useState<OVMLData>({
    priceDate: new Date(),
    asset: 'EUR/USD',
    spot: 1.1750,
    style: 'European',
    direction: 'Buy',
    optionType: 'Put',
    expiry: new Date('2025-09-17'),
    delivery: new Date('2025-09-19'),
    strike: 1.15,
    notional: 10000000,
    model: 'Black-Scholes (OTC)',
    volatility: 8.562,
    points: 0,
    forward: 1.1750,
    eurDepo: 3.382,
    usdDepo: 4.960,
    premium: 43710.17,
    premiumCurrency: 'USD',
    premiumPercent: 0.437,
    premiumPips: 437,
    delta: -22.0440,
    deltaNotional: -2204400,
    gamma: 17.3584,
    gammaPct: 0.434,
    vega: 4345.41,
    vegaNotional: 4345.41,
    theta: -61.25,
    thetaNotional: -61.25,
    rho: -1735.89,
    rhoNotional: -1735.89
  })
  
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // Calculate time to expiry
  const calculateTimeToExpiry = (expiry: Date) => {
    const now = new Date()
    const diffTime = expiry.getTime() - now.getTime()
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    return { days: diffDays, years: diffDays / 365.25 }
  }
  
  // Fetch real Bloomberg data and calculate option price
  const calculateOption = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const apiUrl = import.meta.env.DEV ? 'http://localhost:8000' : 'http://20.172.249.92:8080'
      
      // Extract currencies from asset (e.g., "EUR/USD" -> "EURUSD")
      const currencyPair = ovmlData.asset.replace('/', '')
      const { years } = calculateTimeToExpiry(ovmlData.expiry)
      
      // Call backend option pricing service
      const pricingRequest: any = {
        currency_pair: currencyPair,
        strike: ovmlData.strike,
        time_to_expiry: years,
        option_type: ovmlData.optionType.toLowerCase(),
        notional: ovmlData.notional,
        price_date: ovmlData.priceDate.toISOString().slice(0, 10) // YYYY-MM-DD format
      }
      
      // Add spot override if user has manually changed it
      const spotOverride = document.querySelector<HTMLInputElement>('input[placeholder="Override"]')?.value
      if (spotOverride) {
        pricingRequest.spot_override = parseFloat(spotOverride)
      }
      
      console.log('🔗 Calling OVML pricing service:', pricingRequest)
      
      const response = await fetch(`${apiUrl}/api/option/price`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(pricingRequest)
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const result = await response.json()
      
      if (result.status === 'error') {
        throw new Error(result.error)
      }
      
      if (result.status === 'success' && result.pricing && result.market_data) {
        // Update OVML data with real Bloomberg values
        setOvmlData(prev => ({
          ...prev,
          spot: result.market_data.spot,
          volatility: result.market_data.volatility,
          eurDepo: result.market_data.base_currency === 'EUR' ? result.market_data.base_rate : result.market_data.quote_rate,
          usdDepo: result.market_data.quote_currency === 'USD' ? result.market_data.quote_rate : result.market_data.base_rate,
          forward: result.pricing.forward || prev.forward,
          points: ((result.pricing.forward || prev.forward) - result.market_data.spot) * 10000,
          premium: result.pricing.premium,
          premiumPercent: result.pricing.premium_percent,
          premiumPips: Math.round(result.pricing.premium_percent * 100),
          delta: result.pricing.delta,
          deltaNotional: result.pricing.delta_notional || (result.pricing.delta * ovmlData.notional / 100),
          gamma: result.pricing.gamma,
          gammaPct: result.pricing.gamma * 100,
          vega: result.pricing.vega,
          vegaNotional: result.pricing.vega_notional || result.pricing.vega,
          theta: result.pricing.theta,
          thetaNotional: result.pricing.theta_notional || result.pricing.theta,
          rho: result.pricing.rho || 0,
          rhoNotional: result.pricing.rho_notional || result.pricing.rho || 0
        }))
        
        console.log('✅ OVML pricing complete:', result)
      }
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
      console.error('❌ OVML pricing error:', err)
    } finally {
      setLoading(false)
    }
  }
  
  // Format date as Bloomberg style: 07/24/25
  const formatDate = (date: Date) => {
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    const year = String(date.getFullYear()).slice(-2)
    return `${month}/${day}/${year}`
  }
  
  // Auto-calculate on parameter changes
  useEffect(() => {
    calculateOption()
  }, [ovmlData.asset, ovmlData.strike, ovmlData.expiry, ovmlData.optionType, ovmlData.notional])
  
  // Bloomberg terminal style components
  const FieldLabel = ({ children }: { children: React.ReactNode }) => (
    <div style={{
      fontSize: '11px',
      color: currentTheme.textSecondary,
      fontFamily: 'monospace',
      marginBottom: '2px',
      fontWeight: '600',
      textTransform: 'uppercase'
    }}>
      {children}
    </div>
  )
  
  const FieldValue = ({ children, color = currentTheme.text }: { children: React.ReactNode, color?: string }) => (
    <div style={{
      fontSize: '12px',
      color,
      fontFamily: 'monospace',
      fontWeight: '500'
    }}>
      {children}
    </div>
  )
  
  return (
    <div style={{
      backgroundColor: currentTheme.background,
      color: currentTheme.text,
      height: '100%',
      padding: '12px',
      fontFamily: 'monospace',
      overflow: 'auto'
    }}>
      {/* Header */}
      <div style={{
        borderBottom: `1px solid ${currentTheme.border}`,
        paddingBottom: '8px',
        marginBottom: '12px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <h2 style={{ fontSize: '16px', color: currentTheme.primary, margin: 0, fontWeight: '600' }}>
          GZC Option Pricer
        </h2>
        <button
          onClick={calculateOption}
          disabled={loading}
          style={{
            backgroundColor: currentTheme.primary,
            color: 'white',
            border: 'none',
            padding: '4px 12px',
            fontSize: '11px',
            fontWeight: 'bold',
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading ? 0.5 : 1
          }}
        >
          {loading ? 'CALCULATING...' : 'REFRESH'}
        </button>
      </div>
      
      {/* Main Grid Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        {/* Left Column - Input Parameters */}
        <div>
          {/* Price Date */}
          <div style={{ marginBottom: '12px' }}>
            <FieldLabel>
              Price Date
              {!isBusinessDay(ovmlData.priceDate) && (
                <span style={{ 
                  marginLeft: '8px', 
                  color: '#ef4444', 
                  fontSize: '10px',
                  fontWeight: 'normal'
                }}>
                  (Weekend/Holiday)
                </span>
              )}
            </FieldLabel>
            <div style={{ display: 'flex', gap: '4px', marginBottom: '4px' }}>
              <button
                onClick={() => {
                  const today = adjustToBusinessDay(new Date())
                  setOvmlData(prev => ({ ...prev, priceDate: today }))
                }}
                style={{
                  padding: '2px 6px',
                  backgroundColor: currentTheme.background,
                  color: currentTheme.text,
                  border: `1px solid ${currentTheme.border}`,
                  borderRadius: '2px',
                  cursor: 'pointer',
                  fontSize: '9px',
                  fontWeight: '600'
                }}
              >
                TODAY
              </button>
              <button
                onClick={() => {
                  const t1 = getBusinessDaysAgo(1)
                  setOvmlData(prev => ({ ...prev, priceDate: t1 }))
                }}
                style={{
                  padding: '2px 6px',
                  backgroundColor: currentTheme.background,
                  color: currentTheme.text,
                  border: `1px solid ${currentTheme.border}`,
                  borderRadius: '2px',
                  cursor: 'pointer',
                  fontSize: '9px',
                  fontWeight: '600'
                }}
              >
                T-1
              </button>
              <button
                onClick={() => {
                  const t5 = getBusinessDaysAgo(5)
                  setOvmlData(prev => ({ ...prev, priceDate: t5 }))
                }}
                style={{
                  padding: '2px 6px',
                  backgroundColor: currentTheme.background,
                  color: currentTheme.text,
                  border: `1px solid ${currentTheme.border}`,
                  borderRadius: '2px',
                  cursor: 'pointer',
                  fontSize: '9px',
                  fontWeight: '600'
                }}
              >
                T-5
              </button>
            </div>
            <input
              type="date"
              value={ovmlData.priceDate.toISOString().slice(0, 10)}
              onChange={(e) => {
                const selectedDate = new Date(e.target.value)
                const adjustedDate = adjustToBusinessDay(selectedDate)
                setOvmlData(prev => ({ ...prev, priceDate: adjustedDate }))
                
                // Show warning if date was adjusted
                if (selectedDate.getTime() !== adjustedDate.getTime()) {
                  console.warn(`📅 ${e.target.value} is not a business day. Adjusted to ${adjustedDate.toISOString().slice(0, 10)}`)
                }
              }}
              style={{
                backgroundColor: currentTheme.background,
                color: currentTheme.text,
                border: `1px solid ${currentTheme.border}`,
                padding: '4px',
                fontSize: '12px',
                fontFamily: 'monospace',
                width: '100%'
              }}
            />
          </div>
          
          {/* Asset */}
          <div style={{ marginBottom: '12px' }}>
            <FieldLabel>Asset</FieldLabel>
            <select
              value={ovmlData.asset}
              onChange={(e) => setOvmlData(prev => ({ ...prev, asset: e.target.value }))}
              style={{
                backgroundColor: currentTheme.background,
                color: currentTheme.text,
                border: `1px solid ${currentTheme.border}`,
                padding: '4px',
                fontSize: '12px',
                fontFamily: 'monospace',
                width: '120px'
              }}
            >
              {SUPPORTED_FX_PAIRS.map(pair => {
                const formattedPair = pair.slice(0, 3) + '/' + pair.slice(3)
                return <option key={pair} value={formattedPair}>{formattedPair}</option>
              })}
            </select>
          </div>
          
          {/* Spot */}
          <div style={{ marginBottom: '12px' }}>
            <FieldLabel>Spot</FieldLabel>
            <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
              <FieldValue color={currentTheme.primary}>{ovmlData.spot.toFixed(4)}</FieldValue>
              <input
                type="number"
                step="0.0001"
                placeholder="Override"
                onChange={(e) => {
                  const value = e.target.value
                  if (value) {
                    setOvmlData(prev => ({ ...prev, spot: parseFloat(value) }))
                  }
                }}
                style={{
                  backgroundColor: currentTheme.background,
                  color: currentTheme.text,
                  border: `1px solid ${currentTheme.border}`,
                  padding: '2px 4px',
                  fontSize: '11px',
                  fontFamily: 'monospace',
                  width: '80px'
                }}
              />
            </div>
          </div>
          
          {/* Style */}
          <div style={{ marginBottom: '12px' }}>
            <FieldLabel>Style</FieldLabel>
            <select
              value={ovmlData.style}
              onChange={(e) => setOvmlData(prev => ({ ...prev, style: e.target.value as 'European' | 'American' }))}
              style={{
                backgroundColor: currentTheme.background,
                color: currentTheme.text,
                border: `1px solid ${currentTheme.border}`,
                padding: '4px',
                fontSize: '12px',
                fontFamily: 'monospace',
                width: '100px'
              }}
            >
              <option value="European">European</option>
              <option value="American">American</option>
            </select>
          </div>
          
          {/* Direction */}
          <div style={{ marginBottom: '12px' }}>
            <FieldLabel>Direction</FieldLabel>
            <select
              value={ovmlData.direction}
              onChange={(e) => setOvmlData(prev => ({ ...prev, direction: e.target.value as 'Buy' | 'Sell' }))}
              style={{
                backgroundColor: currentTheme.background,
                color: currentTheme.text,
                border: `1px solid ${currentTheme.border}`,
                padding: '4px',
                fontSize: '12px',
                fontFamily: 'monospace',
                width: '80px'
              }}
            >
              <option value="Buy">Buy</option>
              <option value="Sell">Sell</option>
            </select>
          </div>
          
          {/* Call/Put */}
          <div style={{ marginBottom: '12px' }}>
            <FieldLabel>Call/Put</FieldLabel>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                onClick={() => setOvmlData(prev => ({ ...prev, optionType: 'Call' }))}
                style={{
                  backgroundColor: ovmlData.optionType === 'Call' ? currentTheme.primary : currentTheme.background,
                  color: ovmlData.optionType === 'Call' ? 'white' : currentTheme.text,
                  border: `1px solid ${currentTheme.border}`,
                  padding: '4px 12px',
                  fontSize: '11px',
                  cursor: 'pointer'
                }}
              >
                Call
              </button>
              <button
                onClick={() => setOvmlData(prev => ({ ...prev, optionType: 'Put' }))}
                style={{
                  backgroundColor: ovmlData.optionType === 'Put' ? currentTheme.primary : currentTheme.background,
                  color: ovmlData.optionType === 'Put' ? 'white' : currentTheme.text,
                  border: `1px solid ${currentTheme.border}`,
                  padding: '4px 12px',
                  fontSize: '11px',
                  cursor: 'pointer'
                }}
              >
                Put
              </button>
            </div>
          </div>
          
          {/* Expiry with Tenor Shortcuts */}
          <div style={{ marginBottom: '12px' }}>
            <FieldLabel>Expiry</FieldLabel>
            <div style={{ display: 'flex', gap: '4px', marginBottom: '4px' }}>
              <button
                onClick={() => {
                  const date = new Date()
                  date.setMonth(date.getMonth() + 1)
                  setOvmlData(prev => ({ ...prev, expiry: date }))
                }}
                style={{
                  padding: '2px 6px',
                  backgroundColor: currentTheme.background,
                  color: currentTheme.text,
                  border: `1px solid ${currentTheme.border}`,
                  borderRadius: '2px',
                  cursor: 'pointer',
                  fontSize: '9px',
                  fontWeight: '600'
                }}
              >
                1M
              </button>
              <button
                onClick={() => {
                  const date = new Date()
                  date.setMonth(date.getMonth() + 3)
                  setOvmlData(prev => ({ ...prev, expiry: date }))
                }}
                style={{
                  padding: '2px 6px',
                  backgroundColor: currentTheme.background,
                  color: currentTheme.text,
                  border: `1px solid ${currentTheme.border}`,
                  borderRadius: '2px',
                  cursor: 'pointer',
                  fontSize: '9px',
                  fontWeight: '600'
                }}
              >
                3M
              </button>
              <button
                onClick={() => {
                  const date = new Date()
                  date.setMonth(date.getMonth() + 6)
                  setOvmlData(prev => ({ ...prev, expiry: date }))
                }}
                style={{
                  padding: '2px 6px',
                  backgroundColor: currentTheme.background,
                  color: currentTheme.text,
                  border: `1px solid ${currentTheme.border}`,
                  borderRadius: '2px',
                  cursor: 'pointer',
                  fontSize: '9px',
                  fontWeight: '600'
                }}
              >
                6M
              </button>
              <button
                onClick={() => {
                  const date = new Date()
                  date.setFullYear(date.getFullYear() + 1)
                  setOvmlData(prev => ({ ...prev, expiry: date }))
                }}
                style={{
                  padding: '2px 6px',
                  backgroundColor: currentTheme.background,
                  color: currentTheme.text,
                  border: `1px solid ${currentTheme.border}`,
                  borderRadius: '2px',
                  cursor: 'pointer',
                  fontSize: '9px',
                  fontWeight: '600'
                }}
              >
                1Y
              </button>
            </div>
            <input
              type="date"
              value={ovmlData.expiry.toISOString().slice(0, 10)}
              onChange={(e) => setOvmlData(prev => ({ ...prev, expiry: new Date(e.target.value) }))}
              style={{
                backgroundColor: currentTheme.background,
                color: currentTheme.text,
                border: `1px solid ${currentTheme.border}`,
                padding: '4px',
                fontSize: '12px',
                fontFamily: 'monospace',
                width: '100%'
              }}
            />
          </div>
          
          {/* Delivery */}
          <div style={{ marginBottom: '12px' }}>
            <FieldLabel>Delivery</FieldLabel>
            <input
              type="date"
              value={ovmlData.delivery.toISOString().slice(0, 10)}
              onChange={(e) => {
                const newDelivery = new Date(e.target.value)
                setOvmlData(prev => ({ ...prev, delivery: newDelivery }))
              }}
              style={{
                backgroundColor: currentTheme.background,
                color: currentTheme.text,
                border: `1px solid ${currentTheme.border}`,
                padding: '4px',
                fontSize: '12px',
                fontFamily: 'monospace'
              }}
            />
          </div>
          
          {/* Strike */}
          <div style={{ marginBottom: '12px' }}>
            <FieldLabel>Strike</FieldLabel>
            <div style={{ display: 'flex', gap: '4px', marginBottom: '4px' }}>
              <button
                onClick={() => setOvmlData(prev => ({ ...prev, strike: prev.spot }))}
                style={{
                  padding: '2px 6px',
                  backgroundColor: Math.abs(ovmlData.strike - ovmlData.spot) < 0.0001 ? currentTheme.primary : currentTheme.background,
                  color: Math.abs(ovmlData.strike - ovmlData.spot) < 0.0001 ? 'white' : currentTheme.text,
                  border: `1px solid ${currentTheme.border}`,
                  borderRadius: '2px',
                  cursor: 'pointer',
                  fontSize: '9px',
                  fontWeight: '600'
                }}
              >
                ATM
              </button>
              <button
                onClick={() => setOvmlData(prev => ({ ...prev, strike: prev.forward }))}
                style={{
                  padding: '2px 6px',
                  backgroundColor: Math.abs(ovmlData.strike - ovmlData.forward) < 0.0001 ? currentTheme.primary : currentTheme.background,
                  color: Math.abs(ovmlData.strike - ovmlData.forward) < 0.0001 ? 'white' : currentTheme.text,
                  border: `1px solid ${currentTheme.border}`,
                  borderRadius: '2px',
                  cursor: 'pointer',
                  fontSize: '9px',
                  fontWeight: '600'
                }}
              >
                ATMF
              </button>
              <button
                onClick={() => setOvmlData(prev => ({ ...prev, strike: prev.spot * 0.975 }))}
                style={{
                  padding: '2px 6px',
                  backgroundColor: currentTheme.background,
                  color: currentTheme.text,
                  border: `1px solid ${currentTheme.border}`,
                  borderRadius: '2px',
                  cursor: 'pointer',
                  fontSize: '9px',
                  fontWeight: '600'
                }}
              >
                25Δ PUT
              </button>
              <button
                onClick={() => setOvmlData(prev => ({ ...prev, strike: prev.spot * 1.025 }))}
                style={{
                  padding: '2px 6px',
                  backgroundColor: currentTheme.background,
                  color: currentTheme.text,
                  border: `1px solid ${currentTheme.border}`,
                  borderRadius: '2px',
                  cursor: 'pointer',
                  fontSize: '9px',
                  fontWeight: '600'
                }}
              >
                25Δ CALL
              </button>
            </div>
            <input
              type="number"
              step="0.0001"
              value={ovmlData.strike}
              onChange={(e) => setOvmlData(prev => ({ ...prev, strike: parseFloat(e.target.value) || 0 }))}
              style={{
                backgroundColor: currentTheme.background,
                color: currentTheme.text,
                border: `1px solid ${currentTheme.border}`,
                padding: '4px',
                fontSize: '12px',
                fontFamily: 'monospace',
                width: '100%'
              }}
            />
          </div>
          
          {/* Notional */}
          <div style={{ marginBottom: '12px' }}>
            <FieldLabel>Notional</FieldLabel>
            <input
              type="number"
              step="1000000"
              value={ovmlData.notional}
              onChange={(e) => setOvmlData(prev => ({ ...prev, notional: parseFloat(e.target.value) || 0 }))}
              style={{
                backgroundColor: currentTheme.background,
                color: currentTheme.text,
                border: `1px solid ${currentTheme.border}`,
                padding: '4px',
                fontSize: '12px',
                fontFamily: 'monospace',
                width: '120px'
              }}
            />
          </div>
          
          {/* Model */}
          <div style={{ marginBottom: '12px' }}>
            <FieldLabel>Model</FieldLabel>
            <select
              value={ovmlData.model}
              onChange={(e) => setOvmlData(prev => ({ ...prev, model: e.target.value }))}
              style={{
                backgroundColor: currentTheme.background,
                color: currentTheme.text,
                border: `1px solid ${currentTheme.border}`,
                padding: '4px',
                fontSize: '12px',
                fontFamily: 'monospace',
                width: '180px'
              }}
            >
              <option value="Black-Scholes (OTC)">Black-Scholes (OTC)</option>
              <option value="Garman-Kohlhagen">Garman-Kohlhagen</option>
              <option value="SABR">SABR</option>
              <option value="Local Volatility">Local Volatility</option>
            </select>
          </div>
        </div>
        
        {/* Right Column - Market Data and Results */}
        <div>
          {/* Market Data Section */}
          <div style={{
            border: `1px solid ${currentTheme.border}`,
            padding: '8px',
            marginBottom: '16px'
          }}>
            <div style={{ color: currentTheme.textSecondary, fontSize: '12px', marginBottom: '8px', fontWeight: '600' }}>
              MARKET DATA
            </div>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
              <div>
                <FieldLabel>Vol</FieldLabel>
                <FieldValue color={currentTheme.primary}>{ovmlData.volatility.toFixed(3)}%</FieldValue>
              </div>
              <div>
                <FieldLabel>Points</FieldLabel>
                <FieldValue color={ovmlData.points > 0 ? '#4ade80' : '#ef4444'}>
                  {ovmlData.points > 0 ? '+' : ''}{ovmlData.points.toFixed(2)}
                </FieldValue>
              </div>
              <div>
                <FieldLabel>Forward</FieldLabel>
                <FieldValue>{ovmlData.forward.toFixed(4)}</FieldValue>
              </div>
              <div>
                <FieldLabel>Days to Expiry</FieldLabel>
                <FieldValue>{calculateTimeToExpiry(ovmlData.expiry).days}</FieldValue>
              </div>
            </div>
            
            <div style={{ marginTop: '12px', borderTop: `1px solid ${currentTheme.border}`, paddingTop: '8px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                <div>
                  <FieldLabel>EUR Depo</FieldLabel>
                  <FieldValue>{ovmlData.eurDepo.toFixed(3)}%</FieldValue>
                </div>
                <div>
                  <FieldLabel>USD Depo</FieldLabel>
                  <FieldValue>{ovmlData.usdDepo.toFixed(3)}%</FieldValue>
                </div>
              </div>
            </div>
          </div>
          
          {/* Results Section */}
          <div style={{
            border: `1px solid ${currentTheme.border}`,
            padding: '8px',
            marginBottom: '16px'
          }}>
            <div style={{ color: currentTheme.textSecondary, fontSize: '12px', marginBottom: '8px', fontWeight: '600' }}>
              RESULTS
            </div>
            
            <div style={{ marginBottom: '12px' }}>
              <FieldLabel>Premium</FieldLabel>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '12px' }}>
                <FieldValue color={currentTheme.primary}>
                  {ovmlData.premiumCurrency} {ovmlData.premium.toLocaleString(undefined, {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                  })}
                </FieldValue>
                <FieldValue>
                  ({ovmlData.premiumPercent.toFixed(3)}%)
                </FieldValue>
                <FieldValue color={currentTheme.textSecondary}>
                  {ovmlData.premiumPips} pips
                </FieldValue>
              </div>
            </div>
          </div>
          
          {/* Greeks Section */}
          <div style={{
            border: `1px solid ${currentTheme.border}`,
            padding: '8px'
          }}>
            <div style={{ color: currentTheme.textSecondary, fontSize: '12px', marginBottom: '8px', fontWeight: '600' }}>
              GREEKS
            </div>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
              <div>
                <FieldLabel>Delta</FieldLabel>
                <FieldValue color={ovmlData.delta < 0 ? '#ef4444' : '#4ade80'}>
                  {ovmlData.delta.toFixed(4)}%
                </FieldValue>
                <div style={{ fontSize: '10px', color: currentTheme.textSecondary }}>
                  {ovmlData.deltaNotional.toLocaleString()} {ovmlData.asset.slice(0, 3)}
                </div>
              </div>
              
              <div>
                <FieldLabel>Gamma</FieldLabel>
                <FieldValue>{ovmlData.gamma.toFixed(4)}</FieldValue>
                <div style={{ fontSize: '10px', color: currentTheme.textSecondary }}>
                  {ovmlData.gammaPct.toFixed(3)}%
                </div>
              </div>
              
              <div>
                <FieldLabel>Vega</FieldLabel>
                <FieldValue>{ovmlData.vega.toFixed(2)}</FieldValue>
                <div style={{ fontSize: '10px', color: currentTheme.textSecondary }}>
                  {ovmlData.premiumCurrency} {ovmlData.vegaNotional.toFixed(2)}
                </div>
              </div>
              
              <div>
                <FieldLabel>Theta</FieldLabel>
                <FieldValue color="#ef4444">{ovmlData.theta.toFixed(2)}</FieldValue>
                <div style={{ fontSize: '10px', color: currentTheme.textSecondary }}>
                  {ovmlData.premiumCurrency} {ovmlData.thetaNotional.toFixed(2)}
                </div>
              </div>
              
              <div>
                <FieldLabel>Rho</FieldLabel>
                <FieldValue>{ovmlData.rho.toFixed(2)}</FieldValue>
                <div style={{ fontSize: '10px', color: currentTheme.textSecondary }}>
                  {ovmlData.premiumCurrency} {ovmlData.rhoNotional.toFixed(2)}
                </div>
              </div>
            </div>
          </div>
          
          {/* Error Display */}
          {error && (
            <div style={{
              backgroundColor: '#ef4444',
              color: 'white',
              padding: '8px',
              marginTop: '12px',
              fontSize: '11px'
            }}>
              ERROR: {error}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}