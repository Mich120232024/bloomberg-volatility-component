import { ValidatedVolatilityData, DataQualityMetrics, getQualityColor } from '../utils/dataValidation'
import { useTheme } from '../contexts/ThemeContext'

interface DataQualityIndicatorProps {
  data: ValidatedVolatilityData[]
  expanded?: boolean
  onRetry?: () => void
}

export function DataQualityIndicator({ data, expanded = false, onRetry }: DataQualityIndicatorProps) {
  const { currentTheme } = useTheme()
  
  if (!data || data.length === 0) {
    return null
  }
  
  // Calculate aggregate metrics
  const totalFields = data.reduce((sum, d) => sum + d.quality.totalFields, 0)
  const validFields = data.reduce((sum, d) => sum + d.quality.validFields, 0)
  const overallScore = Math.round((validFields / totalFields) * 100)
  
  const warnings = data.flatMap(d => d.quality.warnings)
  const uniqueWarnings = [...new Set(warnings)]
  const criticalWarnings = uniqueWarnings.filter(w => 
    w.includes('Critical') || w.includes('error') || w.includes('missing')
  )
  
  const staleCount = data.filter(d => d.quality.isStale).length
  const incompleteCount = data.filter(d => !d.isComplete).length
  
  if (!expanded) {
    // Compact view - just a badge
    return (
      <div style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '4px',
        padding: '2px 8px',
        borderRadius: '12px',
        backgroundColor: getQualityColor(overallScore) + '20',
        border: `1px solid ${getQualityColor(overallScore)}40`,
        fontSize: '11px'
      }}>
        <div style={{
          width: '6px',
          height: '6px',
          borderRadius: '50%',
          backgroundColor: getQualityColor(overallScore)
        }} />
        <span style={{ 
          color: getQualityColor(overallScore),
          fontWeight: '600'
        }}>
          {overallScore}%
        </span>
        {criticalWarnings.length > 0 && (
          <span style={{ color: currentTheme.danger }}>⚠</span>
        )}
      </div>
    )
  }
  
  // Expanded view - detailed breakdown
  return (
    <div style={{
      backgroundColor: currentTheme.surface,
      border: `1px solid ${currentTheme.border}`,
      borderRadius: '8px',
      padding: '12px',
      fontSize: '11px'
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '8px'
      }}>
        <h4 style={{ 
          margin: 0, 
          fontSize: '12px', 
          fontWeight: '600',
          color: currentTheme.text 
        }}>
          Data Quality Report
        </h4>
        {onRetry && (
          <button
            onClick={onRetry}
            style={{
              backgroundColor: currentTheme.primary,
              color: currentTheme.background,
              border: 'none',
              borderRadius: '4px',
              padding: '4px 8px',
              fontSize: '10px',
              cursor: 'pointer'
            }}
          >
            Retry Failed
          </button>
        )}
      </div>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ color: currentTheme.textSecondary }}>Overall Score:</span>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px'
          }}>
            <div style={{
              width: '100px',
              height: '4px',
              backgroundColor: currentTheme.border,
              borderRadius: '2px',
              position: 'relative',
              overflow: 'hidden'
            }}>
              <div style={{
                width: `${overallScore}%`,
                height: '100%',
                backgroundColor: getQualityColor(overallScore),
                transition: 'width 0.3s ease'
              }} />
            </div>
            <span style={{ 
              color: getQualityColor(overallScore),
              fontWeight: '600',
              minWidth: '35px',
              textAlign: 'right'
            }}>
              {overallScore}%
            </span>
          </div>
        </div>
        
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ color: currentTheme.textSecondary }}>Complete Records:</span>
          <span style={{ color: currentTheme.text }}>
            {data.length - incompleteCount}/{data.length}
          </span>
        </div>
        
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ color: currentTheme.textSecondary }}>Valid Fields:</span>
          <span style={{ color: currentTheme.text }}>
            {validFields}/{totalFields} ({Math.round((validFields / totalFields) * 100)}%)
          </span>
        </div>
        
        {staleCount > 0 && (
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: currentTheme.textSecondary }}>Stale Data:</span>
            <span style={{ color: currentTheme.warning }}>
              {staleCount} records
            </span>
          </div>
        )}
        
        {criticalWarnings.length > 0 && (
          <div style={{
            marginTop: '6px',
            padding: '6px',
            backgroundColor: currentTheme.danger + '10',
            border: `1px solid ${currentTheme.danger}20`,
            borderRadius: '4px'
          }}>
            <div style={{ 
              fontSize: '10px', 
              fontWeight: '600',
              color: currentTheme.danger,
              marginBottom: '4px'
            }}>
              Warnings ({criticalWarnings.length})
            </div>
            {criticalWarnings.slice(0, 3).map((warning, i) => (
              <div key={i} style={{ 
                fontSize: '10px',
                color: currentTheme.danger,
                opacity: 0.8
              }}>
                • {warning}
              </div>
            ))}
            {criticalWarnings.length > 3 && (
              <div style={{ 
                fontSize: '10px',
                color: currentTheme.danger,
                opacity: 0.6,
                fontStyle: 'italic'
              }}>
                ...and {criticalWarnings.length - 3} more
              </div>
            )}
          </div>
        )}
        
        <div style={{
          marginTop: '6px',
          padding: '6px',
          backgroundColor: currentTheme.surfaceAlt,
          borderRadius: '4px',
          fontSize: '10px',
          color: currentTheme.textSecondary
        }}>
          <div>
            <strong>Data Freshness:</strong> Real-time from Bloomberg Terminal
          </div>
          <div>
            <strong>Last Update:</strong> {new Date().toLocaleTimeString()}
          </div>
        </div>
      </div>
    </div>
  )
}