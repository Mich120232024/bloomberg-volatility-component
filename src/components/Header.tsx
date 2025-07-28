import { useState, useEffect } from 'react'
import { useTheme } from '../contexts/ThemeContext'
import { bloombergAPI } from '../api/bloomberg'

export function Header() {
  const { currentTheme } = useTheme()
  const [apiStatus, setApiStatus] = useState<'checking' | 'connected' | 'disconnected'>('checking')

  useEffect(() => {
    checkAPIStatus()
    // Check status every 30 seconds
    const interval = setInterval(checkAPIStatus, 30000)
    return () => clearInterval(interval)
  }, [])

  const checkAPIStatus = async () => {
    try {
      // Check Bloomberg Terminal health directly
      const health = await bloombergAPI.healthCheck()
      console.log('Health check response:', health)
      
      if (health.success && health.data?.bloomberg_terminal_running) {
        setApiStatus('connected')
      } else {
        console.warn('Health check failed - terminal not running:', health)
        setApiStatus('disconnected')
      }
    } catch (error) {
      console.error('Health check error:', error)
      setApiStatus('disconnected')
    }
  }

  const handleRefresh = async () => {
    setApiStatus('checking')
    await checkAPIStatus()
  }

  const getStatusColor = () => {
    switch (apiStatus) {
      case 'connected': return currentTheme.success
      case 'disconnected': return currentTheme.danger
      case 'checking': return currentTheme.warning
      default: return currentTheme.textSecondary
    }
  }

  const getStatusText = () => {
    switch (apiStatus) {
      case 'connected': return 'Bloomberg Connected'
      case 'disconnected': return 'Bloomberg Disconnected'
      case 'checking': return 'Checking Status...'
      default: return 'Unknown'
    }
  }
  
  return (
    <header style={{
      backgroundColor: currentTheme.surface,
      borderBottom: `1px solid ${currentTheme.border}`,
      padding: '12px 24px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      height: '60px'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
        {/* GZC Logo/Title */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {/* GZC Logo matching Intel app */}
          <svg 
            id="Layer_1" 
            data-name="Layer 1" 
            xmlns="http://www.w3.org/2000/svg" 
            viewBox="0 0 263.82 60.37"
            height={32}
            width={(32 / 60.37) * 263.82}
            style={{ color: currentTheme.text }}
          >
            <defs>
              <style>
                {`
                  .cls-1 {
                    fill: #add586;
                  }
                  .cls-1, .cls-2, .cls-3 {
                    stroke-width: 0px;
                  }
                  .cls-2 {
                    fill: currentColor;
                    opacity: 0.7;
                  }
                  .cls-3 {
                    fill: currentColor;
                  }
                `}
              </style>
            </defs>
            <g id="Layer_6" data-name="Layer 6">
              <rect className="cls-2" x="129.65" y="14.97" width="1.2" height="12.1"/>
              <polygon className="cls-2" points="136.25 27.17 136.25 14.97 136.45 14.97 144.55 24.27 144.55 14.97 145.75 14.97 145.75 27.17 145.45 27.17 137.45 17.97 137.45 27.17 136.25 27.17"/>
              <polygon className="cls-2" points="150.35 14.97 151.65 14.97 155.65 24.37 159.75 14.97 161.05 14.97 155.75 27.17 155.55 27.17 150.35 14.97"/>
              <polygon className="cls-2" points="165.65 14.97 172.65 14.97 172.65 16.17 166.85 16.17 166.85 19.97 172.55 19.97 172.55 21.17 166.85 21.17 166.85 25.97 172.55 25.97 172.55 27.17 165.65 27.17 165.65 14.97"/>
              <path className="cls-2" d="m177.15,24.87l1-.6c.7,1.3,1.6,2,2.5,2,.4,0,.8-.1,1.1-.3.4-.2.6-.4.8-.8.2-.3.3-.7.3-1,0-.4-.1-.8-.4-1.2-.4-.5-1.1-1.2-2.1-1.9-1-.8-1.6-1.3-1.9-1.7-.4-.6-.6-1.2-.6-1.9,0-.5.1-1,.4-1.4s.6-.8,1.1-1,1-.4,1.5-.4c.6,0,1.1.1,1.6.4s1,.8,1.6,1.6l-1,.7c-.5-.6-.8-1-1.2-1.2-.3-.2-.7-.3-1.1-.3-.5,0-.9.1-1.2.4-.3.3-.5.7-.5,1.1,0,.3.1.5.2.8.1.2.3.5.6.8.2.2.7.6,1.6,1.2,1,.8,1.8,1.5,2.2,2.1.4.6.6,1.2.6,1.8,0,.9-.3,1.6-1,2.3-.7.6-1.5,1-2.4,1-.7,0-1.4-.2-2-.6-.6-.3-1.2-1-1.7-1.9"/>
              <polygon className="cls-2" points="188.15 16.17 188.15 14.97 194.85 14.97 194.85 16.17 192.15 16.17 192.15 27.17 190.85 27.17 190.85 16.17 188.15 16.17"/>
              <polygon className="cls-2" points="198.55 27.17 200.35 14.97 200.55 14.97 205.45 24.97 210.35 14.97 210.55 14.97 212.25 27.17 211.05 27.17 209.85 18.47 205.55 27.17 205.25 27.17 200.95 18.37 199.75 27.17 198.55 27.17"/>
              <polygon className="cls-2" points="217.25 14.97 224.15 14.97 224.15 16.17 218.45 16.17 218.45 19.97 224.15 19.97 224.15 21.17 218.45 21.17 218.45 25.97 224.15 25.97 224.15 27.17 217.25 27.17 217.25 14.97"/>
              <polygon className="cls-2" points="229.95 27.17 229.95 14.97 230.25 14.97 238.35 24.27 238.35 14.97 239.55 14.97 239.55 27.17 239.25 27.17 231.25 17.97 231.25 27.17 229.95 27.17"/>
              <polygon className="cls-2" points="244.95 16.17 244.95 14.97 251.65 14.97 251.65 16.17 248.95 16.17 248.95 27.17 247.65 27.17 247.65 16.17 244.95 16.17"/>
            </g>
            <g id="Layer_7" data-name="Layer 7">
              <polygon className="cls-2" points="128.55 45.57 130.25 33.87 130.35 33.87 134.95 43.47 139.55 33.87 139.65 33.87 141.25 45.57 140.15 45.57 139.05 37.27 135.15 45.57 134.85 45.57 130.75 37.17 129.65 45.57 128.55 45.57"/>
              <path className="cls-2" d="m148.75,34.17l5.2,11.2h-1.2l-1.8-3.7h-4.8l-1.8,3.7h-1.3l5.3-11.2h.4Zm-.2,2.3l-1.9,4.1h3.8l-1.9-4.1Z"/>
              <polygon className="cls-2" points="155.75 45.37 155.75 34.17 155.95 34.17 163.45 42.77 163.45 34.17 164.55 34.17 164.55 45.37 164.35 45.37 156.85 36.87 156.85 45.37 155.75 45.37"/>
              <path className="cls-2" d="m172.95,34.17l5.2,11.2h-1.2l-1.8-3.7h-4.8l-1.8,3.7h-1.3l5.3-11.2h.4Zm-.2,2.3l-1.9,4.1h3.8l-1.9-4.1Z"/>
              <path className="cls-2" d="m190.65,35.97l-.9.8c-.6-.6-1.3-1.1-2.1-1.4-.7-.3-1.5-.5-2.2-.5-.9,0-1.7.2-2.5.6s-1.4,1-1.9,1.8c-.4.7-.7,1.5-.7,2.3s.2,1.6.7,2.4,1.1,1.4,1.9,1.8,1.7.7,2.6.7c1.2,0,2.1-.3,2.9-1s1.3-1.5,1.4-2.5h-3.6v-1.1h4.8c0,1.7-.5,3.1-1.5,4.1s-2.4,1.5-4.1,1.5c-2.1,0-3.7-.7-4.9-2.1-.9-1.1-1.4-2.4-1.4-3.8,0-1.1.3-2.1.8-3s1.3-1.6,2.2-2.1c.9-.5,2-.8,3.2-.8,1,0,1.8.2,2.7.5,1,.5,1.8,1.1,2.6,1.8"/>
              <polygon className="cls-2" points="205.25 45.37 206.85 34.17 207.05 34.17 211.55 43.37 216.15 34.17 216.25 34.17 217.85 45.37 216.75 45.37 215.65 37.37 211.75 45.37 211.45 45.37 207.45 37.27 206.35 45.37 205.25 45.37"/>
              <polygon className="cls-2" points="220.95 34.17 227.35 34.17 227.35 35.27 222.05 35.27 222.05 38.77 227.35 38.77 227.35 39.87 222.05 39.87 222.05 44.27 227.35 44.27 227.35 45.37 220.95 45.37 220.95 34.17"/>
              <polygon className="cls-2" points="232.35 45.37 232.35 34.17 232.55 34.17 240.05 42.77 240.05 34.17 241.15 34.17 241.15 45.37 240.95 45.37 233.55 36.87 233.55 45.37 232.35 45.37"/>
              <polygon className="cls-2" points="245.25 35.07 245.25 33.87 251.45 33.87 251.45 35.07 248.95 35.07 248.95 45.57 247.75 45.57 247.75 35.07 245.25 35.07"/>
              <polygon className="cls-2" points="194.75 34.17 201.15 34.17 201.15 35.27 195.85 35.27 195.85 38.77 201.15 38.77 201.15 39.87 195.85 39.87 195.85 44.27 201.15 44.27 201.15 45.37 194.75 45.37 194.75 34.17"/>
            </g>
            <g id="Layer_5" data-name="Layer 5">
              <rect className="cls-1" x="113.15" y="7.97" width="1.6" height="45.6"/>
            </g>
            <g id="Layer_2" data-name="Layer 2">
              <path className="cls-3" d="m37.85,28.87v16c-.8.5-1.7.9-2.7,1.3s-2.1.7-3.1.9c-1.1.3-2.2.5-3.3.6-1.1.1-2.2.2-3.1.2-2.8,0-5.2-.5-7.4-1.4-2.2-.9-4-2.2-5.5-3.7-1.5-1.6-2.6-3.4-3.4-5.4-.8-2.1-1.2-4.2-1.2-6.5s.4-4.7,1.3-6.8c.8-2.1,2-3.9,3.5-5.4s3.3-2.7,5.4-3.6,4.4-1.3,6.8-1.3c3,0,5.4.4,7.3,1.1,1.9.8,3.5,1.8,4.8,3.1l-3.1,3.4c-1.3-1.3-2.8-2.2-4.3-2.7s-3.1-.8-4.7-.8c-1.9,0-3.6.3-5.1,1s-2.8,1.6-3.9,2.8c-1.1,1.2-1.9,2.5-2.5,4.1s-.9,3.3-.9,5c0,1.8.3,3.5,1,5.1.6,1.6,1.5,2.9,2.7,4.1,1.1,1.2,2.5,2.1,4,2.7,1.5.7,3.2,1,5,1,1.6,0,3-.1,4.4-.4s2.6-.7,3.6-1.3v-9h-7.2v-4.1h11.6Z"/>
            </g>
            <g id="Layer_3" data-name="Layer 3">
              <polygon className="cls-3" points="44.25 42.87 62.75 18.67 44.75 18.67 44.75 14.47 68.25 14.47 68.25 18.67 49.85 42.87 68.55 42.87 68.55 46.97 44.25 46.97 44.25 42.87"/>
            </g>
            <g id="Layer_4" data-name="Layer 4">
              <path className="cls-3" d="m96.65,21.47c-.9-1.2-2.1-2.1-3.5-2.8-1.4-.6-2.9-1-4.4-1-1.8,0-3.5,.3-5,1s-2.8,1.6-3.8,2.8c-1.1,1.2-1.9,2.6-2.5,4.2s-.9,3.3-.9,5.2c0,1.7,.3,3.3,.8,4.9,.6,1.5,1.3,2.9,2.4,4,1,1.2,2.3,2.1,3.8,2.8,1.5,.7,3.2,1,5.1,1s3.5-.4,4.9-1.1c1.4-.8,2.6-1.8,3.6-3.2l3.7,2.8c-.2,.3-.7,.8-1.3,1.4-.6,.6-1.4,1.3-2.4,1.9s-2.2,1.2-3.7,1.7c-1.4,.5-3.1,.7-4.9,.7-2.6,0-4.9-.5-7-1.5s-3.8-2.3-5.3-3.9-2.6-3.4-3.3-5.4c-.8-2-1.1-4-1.1-6.1,0-2.5,.4-4.8,1.2-7,.8-2.1,2-4,3.5-5.5s3.3-2.7,5.3-3.6,2.1-.9,4.4-1.3s2.1,0,4.2,.4,3.8,1.2,5.1,2.1,2.1,2.1,2.1,3.8l-3.5,3Z"/>
            </g>
          </svg>
          <div>
            <h1 style={{ 
              fontSize: '16px', 
              fontWeight: '600', 
              color: currentTheme.text,
              margin: 0
            }}>
              Bloomberg Volatility Surface • Real-time FX Option Volatilities
            </h1>
          </div>
        </div>
      </div>
      
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        {/* Bloomberg API Status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: getStatusColor(),
            boxShadow: `0 0 4px ${getStatusColor()}`
          }} />
          <span style={{
            fontSize: '11px',
            color: currentTheme.textSecondary,
            fontWeight: '500'
          }}>
            {getStatusText()}
          </span>
          <span style={{
            fontSize: '10px',
            color: currentTheme.textTertiary,
            fontFamily: 'monospace'
          }}>
            API: 20.172.249.92:8080
          </span>
        </div>

      </div>
    </header>
  )
}