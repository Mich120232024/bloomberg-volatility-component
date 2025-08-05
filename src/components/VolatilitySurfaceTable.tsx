import React from 'react'
import { useTheme } from '../contexts/ThemeContext'
import { VolatilityData } from '../api/bloomberg'

interface Props {
  data: VolatilityData[]
}

export function VolatilitySurfaceTable({ data }: Props) {
  const { currentTheme } = useTheme()
  
  const formatValue = (value: number | null, isRR: boolean = false): string => {
    if (value === null) return '-'
    const formatted = value.toFixed(3)
    return isRR && value !== 0 ? (value > 0 ? `+${formatted}` : formatted) : formatted
  }
  
  const getCellColor = (value: number | null, isRR: boolean = false): string => {
    if (value === null) return currentTheme.textTertiary
    if (isRR) {
      return value > 0 ? currentTheme.success : value < 0 ? currentTheme.danger : currentTheme.text
    }
    return currentTheme.text
  }
  
  if (!data || data.length === 0) {
    return (
      <div style={{
        padding: '60px',
        textAlign: 'center',
        color: currentTheme.textSecondary
      }}>
        <div style={{ fontSize: '16px', marginBottom: '8px' }}>No Data Available</div>
        <div style={{ fontSize: '12px' }}>
          Bloomberg returned no volatility data for this currency pair
        </div>
      </div>
    )
  }
  
  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{
        width: '100%',
        borderCollapse: 'collapse',
        fontSize: '12px',
        fontFamily: 'monospace'
      }}>
        <thead>
          <tr>
            <th style={{
              backgroundColor: currentTheme.primary,
              color: currentTheme.background,
              padding: '12px',
              textAlign: 'left',
              fontWeight: '600',
              position: 'sticky',
              left: 0,
              zIndex: 2
            }}>
              Exp
            </th>
            <th colSpan={2} style={{
              backgroundColor: currentTheme.surfaceAlt,
              color: currentTheme.text,
              padding: '8px',
              textAlign: 'center',
              borderBottom: `1px solid ${currentTheme.border}`
            }}>
              ATM
            </th>
            {['5D', '10D', '15D', '25D', '35D'].map(delta => (
              <th key={delta} colSpan={4} style={{
                backgroundColor: currentTheme.surfaceAlt,
                color: currentTheme.text,
                padding: '8px',
                textAlign: 'center',
                borderBottom: `1px solid ${currentTheme.border}`
              }}>
                {delta} Strike
              </th>
            ))}
          </tr>
          <tr>
            <th style={{
              backgroundColor: currentTheme.surfaceAlt,
              borderBottom: `2px solid ${currentTheme.border}`,
              padding: '8px',
              position: 'sticky',
              left: 0,
              zIndex: 2
            }}></th>
            <th style={headerStyle(currentTheme)}>Bid</th>
            <th style={headerStyle(currentTheme)}>Ask</th>
            {['5D', '10D', '15D', '25D', '35D'].map(delta => (
              <React.Fragment key={delta}>
                <th key={`${delta}-rr-bid`} style={headerStyle(currentTheme)}>RR Bid</th>
                <th key={`${delta}-rr-ask`} style={headerStyle(currentTheme)}>RR Ask</th>
                <th key={`${delta}-bf-bid`} style={headerStyle(currentTheme)}>BF Bid</th>
                <th key={`${delta}-bf-ask`} style={headerStyle(currentTheme)}>BF Ask</th>
              </React.Fragment>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, index) => (
            <tr key={row.tenor} style={{
              backgroundColor: index % 2 === 0 ? currentTheme.surface : currentTheme.background
            }}>
              <td style={{
                backgroundColor: currentTheme.primary,
                color: currentTheme.background,
                padding: '10px',
                fontWeight: '500',
                position: 'sticky',
                left: 0,
                zIndex: 1
              }}>
                {row.tenor}
              </td>
              <td style={cellStyle(currentTheme, '#E6D690')}>{formatValue(row.atm_bid)}</td>
              <td style={cellStyle(currentTheme, '#E6D690')}>{formatValue(row.atm_ask)}</td>
              <td style={cellStyle(currentTheme, getCellColor(row.rr_5d_bid, true))}>{formatValue(row.rr_5d_bid, true)}</td>
              <td style={cellStyle(currentTheme, getCellColor(row.rr_5d_ask, true))}>{formatValue(row.rr_5d_ask, true)}</td>
              <td style={cellStyle(currentTheme)}>{formatValue(row.bf_5d_bid)}</td>
              <td style={cellStyle(currentTheme)}>{formatValue(row.bf_5d_ask)}</td>
              <td style={cellStyle(currentTheme, getCellColor(row.rr_10d_bid, true))}>{formatValue(row.rr_10d_bid, true)}</td>
              <td style={cellStyle(currentTheme, getCellColor(row.rr_10d_ask, true))}>{formatValue(row.rr_10d_ask, true)}</td>
              <td style={cellStyle(currentTheme)}>{formatValue(row.bf_10d_bid)}</td>
              <td style={cellStyle(currentTheme)}>{formatValue(row.bf_10d_ask)}</td>
              <td style={cellStyle(currentTheme, getCellColor(row.rr_15d_bid, true))}>{formatValue(row.rr_15d_bid, true)}</td>
              <td style={cellStyle(currentTheme, getCellColor(row.rr_15d_ask, true))}>{formatValue(row.rr_15d_ask, true)}</td>
              <td style={cellStyle(currentTheme)}>{formatValue(row.bf_15d_bid)}</td>
              <td style={cellStyle(currentTheme)}>{formatValue(row.bf_15d_ask)}</td>
              <td style={cellStyle(currentTheme, getCellColor(row.rr_25d_bid, true))}>{formatValue(row.rr_25d_bid, true)}</td>
              <td style={cellStyle(currentTheme, getCellColor(row.rr_25d_ask, true))}>{formatValue(row.rr_25d_ask, true)}</td>
              <td style={cellStyle(currentTheme)}>{formatValue(row.bf_25d_bid)}</td>
              <td style={cellStyle(currentTheme)}>{formatValue(row.bf_25d_ask)}</td>
              <td style={cellStyle(currentTheme, getCellColor(row.rr_35d_bid, true))}>{formatValue(row.rr_35d_bid, true)}</td>
              <td style={cellStyle(currentTheme, getCellColor(row.rr_35d_ask, true))}>{formatValue(row.rr_35d_ask, true)}</td>
              <td style={cellStyle(currentTheme)}>{formatValue(row.bf_35d_bid)}</td>
              <td style={cellStyle(currentTheme)}>{formatValue(row.bf_35d_ask)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

const headerStyle = (theme: any) => ({
  backgroundColor: theme.surfaceAlt,
  color: theme.textSecondary,
  padding: '6px',
  textAlign: 'center' as const,
  fontWeight: '500',
  fontSize: '10px',
  borderBottom: `2px solid ${theme.border}`
})

const cellStyle = (theme: any, color?: string) => ({
  padding: '8px 6px',
  textAlign: 'right' as const,
  borderRight: `1px solid ${theme.border}`,
  color: color || theme.text,
  fontSize: '11px'
})