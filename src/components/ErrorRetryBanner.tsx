import { useTheme } from '../contexts/ThemeContext'
// BloombergErrorRecovery removed - no fallbacks allowed

interface ErrorRetryBannerProps {
  error: Error | string
  onRetry: () => void
  retrying?: boolean
}

export function ErrorRetryBanner({ error, onRetry, retrying = false }: ErrorRetryBannerProps) {
  const { currentTheme } = useTheme()
  
  const errorMessage = error instanceof Error 
    ? error.message
    : error
    
  const isRetryable = true // Always allow retry
  
  return (
    <div style={{
      backgroundColor: currentTheme.danger + '10',
      border: `1px solid ${currentTheme.danger}40`,
      borderRadius: '8px',
      padding: '12px 16px',
      margin: '8px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: '16px'
    }}>
      <div style={{ flex: 1 }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          marginBottom: '4px'
        }}>
          <span style={{ fontSize: '16px' }}>⚠️</span>
          <span style={{
            fontSize: '13px',
            fontWeight: '600',
            color: currentTheme.danger
          }}>
            Data Fetch Error
          </span>
        </div>
        <div style={{
          fontSize: '12px',
          color: currentTheme.text,
          opacity: 0.9
        }}>
          {errorMessage}
        </div>
        {!isRetryable && (
          <div style={{
            fontSize: '11px',
            color: currentTheme.textSecondary,
            marginTop: '4px',
            fontStyle: 'italic'
          }}>
            This error may require manual intervention.
          </div>
        )}
      </div>
      
      {isRetryable && (
        <button
          onClick={onRetry}
          disabled={retrying}
          style={{
            backgroundColor: retrying ? currentTheme.surfaceAlt : currentTheme.primary,
            color: retrying ? currentTheme.textSecondary : currentTheme.background,
            border: 'none',
            borderRadius: '4px',
            padding: '8px 16px',
            fontSize: '12px',
            fontWeight: '500',
            cursor: retrying ? 'not-allowed' : 'pointer',
            opacity: retrying ? 0.6 : 1,
            minWidth: '80px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '6px'
          }}
        >
          {retrying ? (
            <>
              <div style={{
                width: '12px',
                height: '12px',
                border: `2px solid ${currentTheme.textSecondary}`,
                borderTopColor: 'transparent',
                borderRadius: '50%',
                animation: 'spin 1s linear infinite'
              }} />
              Retrying...
            </>
          ) : (
            'Retry'
          )}
        </button>
      )}
      
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  )
}