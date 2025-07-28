import { useState, useEffect } from 'react'
import { bloombergAPI } from '../api/bloomberg'

export function DebugVolatilityData() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [rawData, setRawData] = useState<any>(null)
  const [processedData, setProcessedData] = useState<any>(null)

  useEffect(() => {
    async function testAPI() {
      try {
        console.log('🔍 DEBUG: Starting API test')
        
        // Test raw API call
        const rawResponse = await fetch('/api/bloomberg/reference', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            securities: [
              "EURUSDVON BGN Curncy",
              "EURUSDV1M BGN Curncy",
              "EURUSD25R1M BGN Curncy"
            ],
            fields: ["PX_BID", "PX_ASK", "PX_LAST"]
          })
        });
        
        const raw = await rawResponse.json();
        console.log('🔍 DEBUG: Raw API response:', raw);
        setRawData(raw);
        
        // Test bloomberg API wrapper
        const volatilityData = await bloombergAPI.getVolatilitySurface('EURUSD', ['ON', '1M']);
        console.log('🔍 DEBUG: Processed volatility data:', volatilityData);
        setProcessedData(volatilityData);
        
      } catch (err) {
        console.error('🔍 DEBUG: Error:', err);
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    }
    
    testAPI();
  }, []);

  return (
    <div style={{ padding: '20px', backgroundColor: '#1a1a1a', color: '#fff' }}>
      <h2>Debug Volatility Data</h2>
      
      {loading && <p>Loading...</p>}
      {error && <p style={{ color: 'red' }}>Error: {error}</p>}
      
      {rawData && (
        <div>
          <h3>Raw API Response:</h3>
          <pre style={{ backgroundColor: '#2a2a2a', padding: '10px', overflow: 'auto' }}>
            {JSON.stringify(rawData, null, 2)}
          </pre>
        </div>
      )}
      
      {processedData && (
        <div>
          <h3>Processed Data ({processedData.length} items):</h3>
          <pre style={{ backgroundColor: '#2a2a2a', padding: '10px', overflow: 'auto' }}>
            {JSON.stringify(processedData, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}