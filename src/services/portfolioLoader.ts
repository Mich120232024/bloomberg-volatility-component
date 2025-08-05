// Portfolio Loader - Load trades from PostgreSQL and aggregate positions
// Integrates with existing portfolio system

import type { Portfolio, FXOptionPosition } from '../types/portfolio'

export interface DatabaseTrade {
  trade_id: number
  trade_date: string
  maturity_date: string
  underlying_trade_currency: string
  underlying_settlement_currency: string
  strike?: number
  quantity: number
  premium?: number
  position: string
  option_type?: string
  fund_id: number
  trader?: string
  strategy_folder_id?: number
}

export interface AggregatedPosition {
  instrument: string
  netQuantity: number
  avgPrice: number
  trades: DatabaseTrade[]
  rollHistory: DatabaseTrade[]
  pnlRealized: number
  pnlUnrealized: number
  tags: string[]
}

export class PortfolioLoader {
  private apiBaseUrl: string

  constructor(apiBaseUrl: string = 'http://localhost:8000') {
    this.apiBaseUrl = apiBaseUrl
  }

  /**
   * Load trades from PostgreSQL for a specific fund
   */
  async loadTradesFromDatabase(fundId: number): Promise<DatabaseTrade[]> {
    try {
      const response = await fetch(`${this.apiBaseUrl}/api/trades/load-by-fund`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ fund_id: fundId })
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()
      if (data.status === 'error') {
        throw new Error(data.error)
      }

      return data.trades || []
    } catch (error) {
      console.error('Failed to load trades from database:', error)
      throw error
    }
  }

  /**
   * Aggregate trades into positions with roll detection
   */
  aggregatePositions(trades: DatabaseTrade[]): AggregatedPosition[] {
    const positionMap = new Map<string, AggregatedPosition>()

    // Group trades by instrument key
    for (const trade of trades) {
      const instrumentKey = this.createInstrumentKey(trade)
      
      if (!positionMap.has(instrumentKey)) {
        positionMap.set(instrumentKey, {
          instrument: instrumentKey,
          netQuantity: 0,
          avgPrice: 0,
          trades: [],
          rollHistory: [],
          pnlRealized: 0,
          pnlUnrealized: 0,
          tags: []
        })
      }

      const position = positionMap.get(instrumentKey)!
      position.trades.push(trade)
      
      // Accumulate net quantity
      const quantity = trade.position === 'SELL' ? -trade.quantity : trade.quantity
      position.netQuantity += quantity

      // Detect rolls (same instrument, different maturity dates)
      if (this.isRollTrade(trade, position.trades)) {
        position.rollHistory.push(trade)
        position.tags.push('ROLLED')
      }

      // Add strategy tags
      if (trade.strategy_folder_id) {
        position.tags.push(`STRATEGY_${trade.strategy_folder_id}`)
      }
    }

    // Calculate weighted average prices and P&L
    for (const position of positionMap.values()) {
      this.calculatePositionMetrics(position)
    }

    return Array.from(positionMap.values()).filter(p => Math.abs(p.netQuantity) > 0.001)
  }

  /**
   * Convert aggregated positions to portfolio format
   */
  convertToPortfolioPositions(aggregatedPositions: AggregatedPosition[]): FXOptionPosition[] {
    return aggregatedPositions.map((pos, index) => {
      // Use the first trade to build the option ticker
      const representativeTrade = pos.trades[0]
      const optionTicker = this.buildOptionTicker(representativeTrade)
      
      return {
        id: `db_pos_${index}`,
        ticker: optionTicker,
        description: `${pos.trades.length} trades${pos.rollHistory.length > 0 ? ` (${pos.rollHistory.length} rolls)` : ''}`,
        quantity: pos.netQuantity,
        entryPrice: pos.avgPrice,
        currentPrice: undefined, // Will be fetched from Bloomberg  
        currency: 'USD',
        portfolioId: 'active_db_portfolio',
        lastUpdated: new Date()
      }
    })
  }

  /**
   * Create a portfolio from database trades for a fund
   */
  async createPortfolioFromDatabase(fundId: number, portfolioName?: string): Promise<{
    portfolio: Omit<Portfolio, 'id'>,
    positions: FXOptionPosition[]
  }> {
    try {
      // Load trades from database
      const trades = await this.loadTradesFromDatabase(fundId)
      
      if (trades.length === 0) {
        throw new Error(`No trades found for fund ${fundId}`)
      }

      // Aggregate positions
      const aggregatedPositions = this.aggregatePositions(trades)
      
      // Convert to portfolio format
      const positions = this.convertToPortfolioPositions(aggregatedPositions)

      const portfolio: Omit<Portfolio, 'id'> = {
        name: portfolioName || `Fund ${fundId} Portfolio`,
        description: `Loaded from database: ${trades.length} trades → ${positions.length} positions (${(trades.length / positions.length).toFixed(1)}:1 compression)`,
        baseCurrency: 'USD',
        positions: [],
        createdAt: new Date(),
        updatedAt: new Date(),
        type: 'active'
      }

      console.log(`✅ Created portfolio from database: ${trades.length} trades → ${positions.length} positions`)
      
      return { portfolio, positions }
    } catch (error) {
      console.error('Failed to create portfolio from database:', error)
      throw error
    }
  }

  // Private helper methods
  private createInstrumentKey(trade: DatabaseTrade): string {
    const currencyPair = `${trade.underlying_trade_currency}${trade.underlying_settlement_currency}`
    const maturity = new Date(trade.maturity_date).toISOString().split('T')[0]
    
    if (trade.strike && trade.option_type) {
      // FX Option
      return `${currencyPair}_${trade.strike}_${trade.option_type}_${maturity}`
    } else {
      // FX Forward
      return `${currencyPair}_FORWARD_${maturity}`
    }
  }

  private isRollTrade(trade: DatabaseTrade, existingTrades: DatabaseTrade[]): boolean {
    // Check if this trade has the same instrument but different maturity
    for (const existing of existingTrades) {
      if (existing.trade_id !== trade.trade_id &&
          existing.underlying_trade_currency === trade.underlying_trade_currency &&
          existing.underlying_settlement_currency === trade.underlying_settlement_currency &&
          existing.strike === trade.strike &&
          existing.option_type === trade.option_type &&
          existing.maturity_date !== trade.maturity_date) {
        return true
      }
    }
    return false
  }

  private calculatePositionMetrics(position: AggregatedPosition): void {
    if (position.trades.length === 0) return

    let totalCost = 0
    let totalQuantity = 0

    for (const trade of position.trades) {
      const quantity = trade.position === 'SELL' ? -trade.quantity : trade.quantity
      const cost = (trade.premium || 0) * Math.abs(quantity)
      
      totalCost += cost
      totalQuantity += Math.abs(quantity)
    }

    position.avgPrice = totalQuantity > 0 ? totalCost / totalQuantity : 0
    
    // P&L calculation would require current market prices
    // For now, set to 0 - will be calculated when prices are fetched
    position.pnlRealized = 0
    position.pnlUnrealized = 0
  }

  private buildOptionTicker(trade: DatabaseTrade): string {
    // Build descriptive option ticker from trade fields
    // Example: USD/MXN 19.75 Call 17-Sep-25
    
    const currencyPair = `${trade.underlying_trade_currency}/${trade.underlying_settlement_currency}`
    const optionType = trade.option_type === 'C' ? 'Call' : trade.option_type === 'P' ? 'Put' : trade.option_type || 'Unknown'
    const strike = trade.strike || 'No Strike'
    
    // Format maturity date
    let maturityStr = 'No Date'
    if (trade.maturity_date) {
      const maturityDate = new Date(trade.maturity_date)
      maturityStr = maturityDate.toLocaleDateString('en-GB', { 
        day: '2-digit', 
        month: 'short', 
        year: '2-digit' 
      })
    }
    
    if (trade.strike && trade.option_type) {
      // FX Option: USD/MXN 19.75 Call 17-Sep-25
      return `${currencyPair} ${strike} ${optionType} ${maturityStr}`
    } else {
      // FX Forward: USD/MXN Forward 17-Sep-25  
      return `${currencyPair} Forward ${maturityStr}`
    }
  }
}

// Export singleton instance
export const portfolioLoader = new PortfolioLoader()