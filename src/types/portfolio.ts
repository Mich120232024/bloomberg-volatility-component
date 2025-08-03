// Portfolio Engine Types for FX Options

export interface FXOptionPosition {
  id: string
  ticker: string              // Bloomberg ticker (e.g., "EURUSD25R1M BGN Curncy")
  description?: string        // Human readable description
  quantity: number           // Position size (positive = long, negative = short)
  entryPrice?: number        // Entry price if available
  currentPrice?: number      // Current Bloomberg price
  currency: string           // Base currency for P&L calculation
  lastUpdated?: Date         // Last price update timestamp
  portfolioId: string        // Which portfolio this position belongs to
}

export interface Portfolio {
  id: string
  name: string
  description?: string
  baseCurrency: string       // Portfolio base currency for P&L aggregation
  positions: FXOptionPosition[]
  createdAt: Date
  updatedAt: Date
  type?: 'active' | 'virtual' // Portfolio type
}

export interface PortfolioValuation {
  portfolioId: string
  portfolioName: string
  baseCurrency: string
  totalPositions: number
  totalMarketValue: number
  totalUnrealizedPnL: number
  lastUpdated: Date
  positionValueSummary: PositionValuationSummary[]
}

export interface PositionValuationSummary {
  positionId: string
  ticker: string
  quantity: number
  entryPrice: number | null
  currentPrice: number | null
  marketValue: number | null
  unrealizedPnL: number | null
  pnlPercent: number | null
}

// For manual position entry form
export interface NewPositionForm {
  ticker: string
  description: string
  quantity: number
  entryPrice?: number
}

// Portfolio management operations
export interface PortfolioOperations {
  createPortfolio: (name: string, description?: string, baseCurrency?: string) => Portfolio
  addPosition: (portfolioId: string, position: NewPositionForm) => FXOptionPosition
  updatePosition: (positionId: string, updates: Partial<FXOptionPosition>) => void
  removePosition: (positionId: string) => void
  updatePrices: (portfolioId: string) => Promise<void>
  calculateValuation: (portfolioId: string) => PortfolioValuation
}

// Bloomberg ticker validation
export interface TickerValidationResult {
  isValid: boolean
  ticker: string
  normalizedTicker?: string  // Standardized format
  error?: string
  tickerType?: 'atm' | 'risk_reversal' | 'butterfly' | 'spot' | 'unknown'
  currencyPair?: string
  tenor?: string
  delta?: number
}