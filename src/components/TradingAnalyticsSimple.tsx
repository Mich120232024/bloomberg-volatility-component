import { useState, useEffect } from 'react'
import { useTheme } from '../contexts/ThemeContext'
import { bloombergAPI } from '../api/bloomberg'

export function TradingAnalyticsSimple() {
  const { currentTheme } = useTheme()
  const [status, setStatus] = useState('Initializing...')
  const [data, setData] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  
  useEffect(() => {
    async function testFetch() {
      try {
        setStatus('Testing Bloomberg API...')
        
        // Simple test - just fetch EURUSD spot
        const response = await bloombergAPI.getReferenceData(['EURUSD Curncy'], ['PX_LAST'])
        console.log('Test response:', response)
        
        if (response.success) {
          setData(response.data)
          setStatus('Success! Data received.')
        } else {
          setError('API returned unsuccessful response')
        }
      } catch (err) {
        console.error('Test error:', err)
        setError(err instanceof Error ? err.message : String(err))
        setStatus('Failed')
      }
    }
    
    testFetch()
  }, [])
  
  return (
    <div style={{
      padding: '20px',
      backgroundColor: currentTheme.surface,
      borderRadius: '8px',
      margin: '20px'
    }}>
      <h2 style={{ color: currentTheme.text }}>Trading Analytics Simple Test</h2>
      
      <div style={{ marginTop: '16px' }}>
        <p style={{ color: currentTheme.textSecondary }}>Status: {status}</p>
        
        {error && (
          <div style={{
            marginTop: '8px',
            padding: '12px',
            backgroundColor: currentTheme.danger + '20',
            color: currentTheme.danger,
            borderRadius: '4px'
          }}>
            Error: {error}
          </div>
        )}
        
        {data && (
          <div style={{
            marginTop: '8px',
            padding: '12px',
            backgroundColor: currentTheme.success + '20',
            borderRadius: '4px'
          }}>
            <pre style={{ color: currentTheme.text, fontSize: '12px' }}>
              {JSON.stringify(data, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  )
}