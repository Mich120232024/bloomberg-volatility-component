import { useState } from 'react'
import { useTheme } from '../contexts/ThemeContext'
import { VolatilitySurfaceContainer } from './VolatilitySurfaceContainer'
import { VolatilityHistoricalTable } from './VolatilityHistoricalTable'
import { VolatilityAnalysisTab } from './VolatilityAnalysisTab'
import { YieldCurvesTab as RateCurvesTab } from './YieldCurvesTab'
import { FXForwardCurvesTab } from './FXForwardCurvesTab'
import { GZCOptionPricerTab } from './GZCOptionPricerTab'
import { PortfolioTab } from './PortfolioTab'

type TabType = 'surface' | 'historical' | 'analysis' | 'yield' | 'fx' | 'options' | 'portfolio'

export function MainAppContainer() {
  const { currentTheme } = useTheme()
  const [activeTab, setActiveTab] = useState<TabType>('surface')
  
  return (
    <div style={{
      backgroundColor: currentTheme.background,
      minHeight: '100vh',
      color: currentTheme.text
    }}>
      {/* Tab Navigation */}
      <div style={{
        backgroundColor: currentTheme.surface,
        borderBottom: `1px solid ${currentTheme.border}`,
        padding: '0 16px',
        display: 'flex',
        gap: '24px',
        overflowX: 'auto'
      }}>
        <button
          onClick={() => setActiveTab('surface')}
          style={{
            backgroundColor: 'transparent',
            border: 'none',
            padding: '16px 0',
            color: activeTab === 'surface' ? currentTheme.primary : currentTheme.textSecondary,
            fontSize: '14px',
            fontWeight: '600',
            cursor: 'pointer',
            borderBottom: activeTab === 'surface' ? `2px solid ${currentTheme.primary}` : '2px solid transparent',
            transition: 'all 0.2s ease'
          }}
        >
          Volatility Surface
        </button>
        <button
          onClick={() => setActiveTab('historical')}
          style={{
            backgroundColor: 'transparent',
            border: 'none',
            padding: '16px 0',
            color: activeTab === 'historical' ? currentTheme.primary : currentTheme.textSecondary,
            fontSize: '14px',
            fontWeight: '600',
            cursor: 'pointer',
            borderBottom: activeTab === 'historical' ? `2px solid ${currentTheme.primary}` : '2px solid transparent',
            transition: 'all 0.2s ease'
          }}
        >
          Historical Analysis
        </button>
        <button
          onClick={() => setActiveTab('analysis')}
          style={{
            backgroundColor: 'transparent',
            border: 'none',
            padding: '16px 0',
            color: activeTab === 'analysis' ? currentTheme.primary : currentTheme.textSecondary,
            fontSize: '14px',
            fontWeight: '600',
            cursor: 'pointer',
            borderBottom: activeTab === 'analysis' ? `2px solid ${currentTheme.primary}` : '2px solid transparent',
            transition: 'all 0.2s ease'
          }}
        >
          Volatility Analysis
        </button>
        <button
          onClick={() => setActiveTab('yield')}
          style={{
            backgroundColor: 'transparent',
            border: 'none',
            padding: '16px 0',
            color: activeTab === 'yield' ? currentTheme.primary : currentTheme.textSecondary,
            fontSize: '14px',
            fontWeight: '600',
            cursor: 'pointer',
            borderBottom: activeTab === 'yield' ? `2px solid ${currentTheme.primary}` : '2px solid transparent',
            transition: 'all 0.2s ease'
          }}
        >
          Yield Curves
        </button>
        <button
          onClick={() => setActiveTab('fx')}
          style={{
            backgroundColor: 'transparent',
            border: 'none',
            padding: '16px 0',
            color: activeTab === 'fx' ? currentTheme.primary : currentTheme.textSecondary,
            fontSize: '14px',
            fontWeight: '600',
            cursor: 'pointer',
            borderBottom: activeTab === 'fx' ? `2px solid ${currentTheme.primary}` : '2px solid transparent',
            transition: 'all 0.2s ease'
          }}
        >
          FX Forwards
        </button>
        <button
          onClick={() => setActiveTab('options')}
          style={{
            backgroundColor: 'transparent',
            border: 'none',
            padding: '16px 0',
            color: activeTab === 'options' ? currentTheme.primary : currentTheme.textSecondary,
            fontSize: '14px',
            fontWeight: '600',
            cursor: 'pointer',
            borderBottom: activeTab === 'options' ? `2px solid ${currentTheme.primary}` : '2px solid transparent',
            transition: 'all 0.2s ease'
          }}
        >
          Option Pricing
        </button>
        <button
          onClick={() => setActiveTab('portfolio')}
          style={{
            backgroundColor: 'transparent',
            border: 'none',
            padding: '16px 0',
            color: activeTab === 'portfolio' ? currentTheme.primary : currentTheme.textSecondary,
            fontSize: '14px',
            fontWeight: '600',
            cursor: 'pointer',
            borderBottom: activeTab === 'portfolio' ? `2px solid ${currentTheme.primary}` : '2px solid transparent',
            transition: 'all 0.2s ease'
          }}
        >
          Portfolio
        </button>
      </div>
      
      {/* Tab Content */}
      <div style={{ padding: '20px', height: 'calc(100vh - 120px)' }}>
        {activeTab === 'surface' ? (
          <VolatilitySurfaceContainer />
        ) : activeTab === 'historical' ? (
          <VolatilityHistoricalTable />
        ) : activeTab === 'analysis' ? (
          <VolatilityAnalysisTab />
        ) : activeTab === 'yield' ? (
          <RateCurvesTab />
        ) : activeTab === 'fx' ? (
          <FXForwardCurvesTab />
        ) : activeTab === 'options' ? (
          <GZCOptionPricerTab />
        ) : activeTab === 'portfolio' ? (
          <PortfolioTab />
        ) : null}
      </div>
    </div>
  )
}