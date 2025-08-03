// Portfolio Service - Bloomberg Integration and Portfolio Management

import { bloombergAPI } from '../api/bloomberg'
import { portfolioLoader, type DatabaseTrade } from './portfolioLoader'
import { garmanKohlhagen } from '../utils/garmanKohlhagen'
import type { 
  Portfolio, 
  FXOptionPosition, 
  NewPositionForm, 
  PortfolioValuation, 
  PositionValuationSummary,
  TickerValidationResult 
} from '../types/portfolio'

class PortfolioService {
  private portfolios: Map<string, Portfolio> = new Map()
  
  // Helper Methods
  private parseMaturityDate(dateStr: string): Date {
    // Parse "17-Sep-25" format
    const [day, monthStr, year] = dateStr.split('-')
    const monthMap: { [key: string]: number } = {
      'Jan': 0, 'Feb': 1, 'Mar': 2, 'Apr': 3, 'May': 4, 'Jun': 5,
      'Jul': 6, 'Aug': 7, 'Sep': 8, 'Oct': 9, 'Nov': 10, 'Dec': 11
    }
    const month = monthMap[monthStr]
    const fullYear = parseInt(year) + 2000 // Convert 25 to 2025
    return new Date(fullYear, month, parseInt(day))
  }

  // Portfolio Management
  createPortfolio(name: string, description?: string, baseCurrency: string = 'USD', type: 'active' | 'virtual' = 'active'): Portfolio {
    const portfolio: Portfolio = {
      id: `portfolio_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      name,
      description,
      baseCurrency,
      positions: [],
      createdAt: new Date(),
      updatedAt: new Date(),
      type
    }
    
    this.portfolios.set(portfolio.id, portfolio)
    console.log(`✅ Created ${type} portfolio: ${name} (${portfolio.id})`)
    return portfolio
  }
  
  getPortfolio(portfolioId: string): Portfolio | null {
    return this.portfolios.get(portfolioId) || null
  }
  
  getAllPortfolios(): Portfolio[] {
    return Array.from(this.portfolios.values())
  }

  // Remove duplicate portfolios by name
  removeDuplicatesByName(): void {
    const seen = new Set<string>()
    const toDelete: string[] = []
    
    for (const [id, portfolio] of this.portfolios.entries()) {
      if (seen.has(portfolio.name)) {
        toDelete.push(id)
        console.log(`🗑️ Marking duplicate for deletion: ${portfolio.name} (${id.slice(-8)})`)
      } else {
        seen.add(portfolio.name)
      }
    }
    
    toDelete.forEach(id => this.portfolios.delete(id))
    if (toDelete.length > 0) {
      console.log(`🧹 Removed ${toDelete.length} duplicate portfolios`)
    }
  }

  // Clear all portfolios (for debugging)
  clearAllPortfolios(): void {
    this.portfolios.clear()
    console.log('🗑️ Cleared all portfolios')
  }
  
  deletePortfolio(portfolioId: string): boolean {
    const success = this.portfolios.delete(portfolioId)
    if (success) {
      console.log(`🗑️ Deleted portfolio: ${portfolioId}`)
    }
    return success
  }
  
  // Position Management
  async addPosition(portfolioId: string, positionForm: NewPositionForm): Promise<FXOptionPosition | null> {
    const portfolio = this.portfolios.get(portfolioId)
    if (!portfolio) {
      console.error(`Portfolio not found: ${portfolioId}`)
      return null
    }
    
    // Validate ticker format
    const validation = this.validateTicker(positionForm.ticker)
    if (!validation.isValid) {
      console.error(`Invalid ticker: ${positionForm.ticker} - ${validation.error}`)
      throw new Error(`Invalid ticker: ${validation.error}`)
    }
    
    const position: FXOptionPosition = {
      id: `pos_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      ticker: validation.normalizedTicker || positionForm.ticker,
      description: positionForm.description,
      quantity: positionForm.quantity,
      entryPrice: positionForm.entryPrice,
      currency: portfolio.baseCurrency,
      portfolioId: portfolioId,
      lastUpdated: new Date()
    }
    
    // Try to get current price from Bloomberg
    try {
      const currentPrice = await this.fetchTickerPrice(position.ticker)
      position.currentPrice = currentPrice || undefined
      console.log(`📈 Fetched price for ${position.ticker}: ${currentPrice}`)
    } catch (error) {
      console.warn(`⚠️ Could not fetch price for ${position.ticker}:`, error)
    }
    
    portfolio.positions.push(position)
    portfolio.updatedAt = new Date()
    
    console.log(`✅ Added position: ${position.ticker} (qty: ${position.quantity})`)
    return position
  }
  
  updatePosition(positionId: string, updates: Partial<FXOptionPosition>): void {
    for (const portfolio of this.portfolios.values()) {
      const positionIndex = portfolio.positions.findIndex(p => p.id === positionId)
      if (positionIndex !== -1) {
        portfolio.positions[positionIndex] = {
          ...portfolio.positions[positionIndex],
          ...updates,
          lastUpdated: new Date()
        }
        portfolio.updatedAt = new Date()
        console.log(`✅ Updated position: ${positionId}`)
        return
      }
    }
    console.error(`Position not found: ${positionId}`)
  }
  
  removePosition(positionId: string): void {
    for (const portfolio of this.portfolios.values()) {
      const positionIndex = portfolio.positions.findIndex(p => p.id === positionId)
      if (positionIndex !== -1) {
        const removedPosition = portfolio.positions.splice(positionIndex, 1)[0]
        portfolio.updatedAt = new Date()
        console.log(`🗑️ Removed position: ${removedPosition.ticker}`)
        return
      }
    }
    console.error(`Position not found: ${positionId}`)
  }
  
  // Bloomberg Integration
  validateTicker(ticker: string): TickerValidationResult {
    // Basic ticker validation for FX options
    const trimmedTicker = ticker.trim().toUpperCase()
    
    // Bloomberg FX option patterns
    const patterns = [
      // ATM: EURUSDV1M BGN Curncy, EURUSDVON Curncy
      /^([A-Z]{6})V(ON|\d+[DWMY])\s*(BGN\s*)?CURNCY?$/i,
      // Risk Reversal: EURUSD25R1M BGN Curncy
      /^([A-Z]{6})(\d+)R(\d+[DWMY])\s*(BGN\s*)?CURNCY?$/i,
      // Butterfly: EURUSD25B1M BGN Curncy  
      /^([A-Z]{6})(\d+)B(\d+[DWMY])\s*(BGN\s*)?CURNCY?$/i,
      // Spot rates: EURUSD Curncy
      /^([A-Z]{6})\s*CURNCY?$/i
    ]
    
    for (const pattern of patterns) {
      if (pattern.test(trimmedTicker)) {
        // Normalize the ticker format
        let normalized = trimmedTicker
        if (!normalized.endsWith(' CURNCY')) {
          normalized = normalized.replace(/CURNCY?$/i, ' CURNCY')
        }
        
        return {
          isValid: true,
          ticker: ticker,
          normalizedTicker: normalized,
          tickerType: this.classifyTicker(normalized)
        }
      }
    }
    
    return {
      isValid: false,
      ticker: ticker,
      error: 'Invalid Bloomberg FX option ticker format. Expected formats: EURUSDV1M BGN CURNCY, EURUSD25R1M BGN CURNCY, EURUSD25B1M BGN CURNCY'
    }
  }
  
  private classifyTicker(ticker: string): 'atm' | 'risk_reversal' | 'butterfly' | 'spot' | 'unknown' {
    if (ticker.includes('V') && (ticker.includes('BGN') || ticker.includes('VON'))) return 'atm'
    if (ticker.includes('R') && ticker.includes('BGN')) return 'risk_reversal'
    if (ticker.includes('B') && ticker.includes('BGN')) return 'butterfly'
    if (ticker.match(/^[A-Z]{6}\s+CURNCY$/)) return 'spot'
    return 'unknown'
  }
  
  async fetchTickerPrice(ticker: string): Promise<number | null> {
    try {
      console.log(`🔍 Fetching price for ticker: ${ticker}`)
      const response = await bloombergAPI.getReferenceData([ticker], ['PX_LAST', 'PX_BID', 'PX_ASK'])
      
      if (response.success && response.securities_data && response.securities_data.length > 0) {
        const securityData = response.securities_data[0]
        if (securityData.success && securityData.fields) {
          // Prefer PX_LAST, fallback to mid of bid/ask
          const price = securityData.fields.PX_LAST || 
                       (securityData.fields.PX_BID && securityData.fields.PX_ASK 
                        ? (securityData.fields.PX_BID + securityData.fields.PX_ASK) / 2 
                        : null)
          
          console.log(`📊 Price fetched for ${ticker}: ${price}`)
          return price
        }
      }
      
      console.warn(`⚠️ No price data returned for ${ticker}`)
      return null
    } catch (error) {
      console.error(`❌ Error fetching price for ${ticker}:`, error)
      throw error
    }
  }

  async calculateOptionPrice(trade: DatabaseTrade): Promise<number | null> {
    try {
      console.log(`🧮 Calculating option price for ${trade.underlying_trade_currency}/${trade.underlying_settlement_currency}`)
      console.log(`📋 Trade details:`, JSON.stringify(trade, null, 2))
      
      const currencyPair = `${trade.underlying_trade_currency}${trade.underlying_settlement_currency}`
      
      // Calculate time to expiry in years
      const maturityDate = new Date(trade.maturity_date)
      const now = new Date()
      const timeToExpiry = (maturityDate.getTime() - now.getTime()) / (365.25 * 24 * 60 * 60 * 1000)
      
      console.log(`📅 Time calculation: now=${now.toISOString()}, maturity=${maturityDate.toISOString()}, timeToExpiry=${timeToExpiry.toFixed(4)} years`)
      
      if (timeToExpiry <= 0) {
        console.error(`❌ Option expired: ${trade.maturity_date} (${timeToExpiry.toFixed(4)} years)`)
        return null
      }
      
      if (!trade.strike) {
        console.error(`❌ Missing strike price in trade data`)
        return null
      }
      
      // Use backend option pricing service with validated ticker repository
      const apiUrl = import.meta.env.DEV ? 'http://localhost:8000' : 'http://20.172.249.92:8080'
      
      const pricingRequest = {
        currency_pair: currencyPair,
        strike: trade.strike,
        time_to_expiry: timeToExpiry,
        option_type: trade.option_type === 'C' ? 'call' : 'put',
        notional: Math.abs(trade.quantity)
      }
      
      console.log(`🔗 Calling backend pricing service:`, pricingRequest)
      
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
        console.error(`❌ Backend pricing error: ${result.error}`)
        return null
      }
      
      if (result.status === 'success' && result.pricing) {
        const premium = result.pricing.premium
        console.log(`✅ Option priced via backend: ${premium} (${result.pricing.premium_percent?.toFixed(2)}%)`)
        console.log(`📊 Market data used:`, result.market_data)
        return premium
      }
      
      console.error(`❌ Unexpected backend response:`, result)
      return null
      
    } catch (error) {
      console.error(`❌ Error calculating option price for ${trade.underlying_trade_currency}/${trade.underlying_settlement_currency}:`, error)
      console.error(`❌ Stack trace:`, error.stack)
      return null
    }
  }
  
  async updateAllPrices(portfolioId: string): Promise<void> {
    const portfolio = this.portfolios.get(portfolioId)
    if (!portfolio) {
      throw new Error(`Portfolio not found: ${portfolioId}`)
    }
    
    console.log(`🔄 Updating prices for portfolio: ${portfolio.name}`)
    
    // Check if this is a real fund portfolio (has database trades)
    const isRealFund = portfolio.name.includes('GZC')
    
    if (isRealFund) {
      console.log('💰 Using option pricer for real fund positions')
      // For real funds, we need to re-fetch the trades and use option pricing
      await this.updateRealFundPrices(portfolio)
    } else {
      // For manual portfolios, use ticker-based pricing
      await this.updateManualPortfolioPrices(portfolio)
    }
    
    portfolio.updatedAt = new Date()
  }

  private async updateRealFundPrices(portfolio: Portfolio): Promise<void> {
    console.log('🔄 Pricing real fund options...')
    console.log(`📝 Portfolio: ${portfolio.name} (${portfolio.positions.length} positions)`)
    
    // For real funds, positions store trade metadata - we need to extract it
    const pricePromises = portfolio.positions.map(async (position) => {
      try {
        // Extract trade data from position description/ticker
        // Position ticker format: "USD/MXN 19.75 Call 17-Sep-25"
        const tickerParts = position.ticker.split(' ')
        if (tickerParts.length < 4) {
          console.error(`❌ Invalid position ticker format: ${position.ticker}`)
          return { success: false, error: 'Invalid ticker format' }
        }
        
        const [currencyPair, strikeStr, optionTypeStr, maturityStr] = tickerParts
        const [baseCurrency, quoteCurrency] = currencyPair.split('/')
        
        // Parse maturity date from "17-Sep-25" format to ISO date
        const maturityDate = this.parseMaturityDate(maturityStr)
        
        // Create trade object for pricing
        const trade = {
          underlying_trade_currency: baseCurrency,
          underlying_settlement_currency: quoteCurrency,
          strike: parseFloat(strikeStr),
          option_type: optionTypeStr.charAt(0).toUpperCase(), // 'C' or 'P'
          maturity_date: maturityDate.toISOString(),
          quantity: Math.abs(position.quantity)
        }
        
        console.log(`🧮 Pricing position: ${position.ticker}`)
        const optionPrice = await this.calculateOptionPrice(trade)
        
        if (optionPrice !== null) {
          position.currentPrice = optionPrice
          position.lastUpdated = new Date()
          console.log(`✅ Priced ${position.ticker}: ${optionPrice}`)
          return { success: true, price: optionPrice }
        }
        
        return { success: false, error: 'No price returned' }
        
      } catch (error) {
        console.error(`❌ Failed to price ${position.ticker}:`, error)
        return { success: false, error: error.message }
      }
    })
    
    const results = await Promise.all(pricePromises)
    const successful = results.filter(r => r.success).length
    console.log(`✅ Real fund pricing complete: ${successful}/${portfolio.positions.length} priced`)
  }

  private async updateManualPortfolioPrices(portfolio: Portfolio): Promise<void> {
    const updatePromises = portfolio.positions.map(async (position) => {
      try {
        const newPrice = await this.fetchTickerPrice(position.ticker)
        if (newPrice !== null) {
          position.currentPrice = newPrice
          position.lastUpdated = new Date()
        }
        return { ticker: position.ticker, success: true, price: newPrice }
      } catch (error) {
        console.error(`Failed to update price for ${position.ticker}:`, error)
        return { ticker: position.ticker, success: false, error }
      }
    })
    
    const results = await Promise.all(updatePromises)
    const successful = results.filter(r => r.success).length
    const failed = results.filter(r => !r.success).length
    
    console.log(`✅ Manual price update complete: ${successful} successful, ${failed} failed`)
  }
  
  // Portfolio Valuation
  // Database Loading Integration
  async loadPortfolioFromDatabase(fundId: number, portfolioName?: string): Promise<Portfolio> {
    try {
      console.log(`🔄 Loading portfolio from database for fund ${fundId}`)
      
      const { portfolio, positions } = await portfolioLoader.createPortfolioFromDatabase(fundId, portfolioName)
      
      // Create full portfolio object
      const fullPortfolio: Portfolio = {
        ...portfolio,
        id: `fund_${fundId}_${Date.now()}`,
        positions: positions
      }
      
      // Store in memory
      this.portfolios.set(fullPortfolio.id, fullPortfolio)
      
      console.log(`✅ Loaded portfolio: ${positions.length} positions from fund ${fundId}`)
      
      // Fetch Bloomberg prices for all positions
      await this.updateAllPrices(fullPortfolio.id)
      
      return fullPortfolio
    } catch (error) {
      console.error(`❌ Failed to load portfolio from database:`, error)
      throw error
    }
  }

  async syncDatabase(): Promise<{ status: string, message?: string, error?: string }> {
    try {
      console.log('🔄 Checking database synchronization...')
      
      const apiUrl = import.meta.env.DEV ? 'http://localhost:8000' : 'http://20.172.249.92:8080'
      
      const response = await fetch(`${apiUrl}/api/trades/sync-check`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const result = await response.json()
      
      if (result.status === 'error') {
        throw new Error(result.error)
      }
      
      console.log('✅ Database sync check completed')
      return result
      
    } catch (error) {
      console.error('❌ Database sync failed:', error)
      return {
        status: 'error',
        error: error instanceof Error ? error.message : 'Unknown error'
      }
    }
  }

  calculateValuation(portfolioId: string): PortfolioValuation {
    const portfolio = this.portfolios.get(portfolioId)
    if (!portfolio) {
      throw new Error(`Portfolio not found: ${portfolioId}`)
    }
    
    const positionSummaries: PositionValuationSummary[] = portfolio.positions.map(position => {
      const marketValue = position.currentPrice !== null && position.currentPrice !== undefined
        ? position.quantity * position.currentPrice
        : null
      
      const unrealizedPnL = position.entryPrice !== null && position.entryPrice !== undefined && 
                           position.currentPrice !== null && position.currentPrice !== undefined
        ? position.quantity * (position.currentPrice - position.entryPrice)
        : null
      
      const pnlPercent = position.entryPrice !== null && position.entryPrice !== undefined && 
                        position.currentPrice !== null && position.currentPrice !== undefined && 
                        position.entryPrice !== 0
        ? ((position.currentPrice - position.entryPrice) / position.entryPrice) * 100
        : null
      
      return {
        positionId: position.id,
        ticker: position.ticker,
        quantity: position.quantity,
        entryPrice: position.entryPrice || null,
        currentPrice: position.currentPrice || null,
        marketValue,
        unrealizedPnL,
        pnlPercent
      }
    })
    
    const totalMarketValue = positionSummaries
      .filter(p => p.marketValue !== null)
      .reduce((sum, p) => sum + (p.marketValue || 0), 0)
    
    const totalUnrealizedPnL = positionSummaries
      .filter(p => p.unrealizedPnL !== null)
      .reduce((sum, p) => sum + (p.unrealizedPnL || 0), 0)
    
    return {
      portfolioId: portfolio.id,
      portfolioName: portfolio.name,
      baseCurrency: portfolio.baseCurrency,
      totalPositions: portfolio.positions.length,
      totalMarketValue,
      totalUnrealizedPnL,
      lastUpdated: new Date(),
      positionValueSummary: positionSummaries
    }
  }
}

// Export singleton instance
export const portfolioService = new PortfolioService()