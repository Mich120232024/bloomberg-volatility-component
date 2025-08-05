// NDF ticker mappings for restricted currencies
// Based on Bloomberg ticker discovery analysis

export interface NDFMapping {
  format: string
  coverage: string
  example: string
  pipFactor?: number
}

export const NDF_MAPPINGS: Record<string, NDFMapping> = {
  // Currencies that need NDF tickers for any forward data
  USDINR: { format: 'IRN', coverage: '1W-6M', example: 'IRN1M Curncy' },
  USDTWD: { format: 'NTN', coverage: '1W-5Y', example: 'NTN1M Curncy' },
  USDIDR: { format: 'IHN', coverage: '1W-9M', example: 'IHN1M Curncy' },
  USDBRL: { format: 'BCN', coverage: '1W-9M', example: 'BCN1M Curncy' },
  USDCLP: { format: 'CHN', coverage: '1W-9M', example: 'CHN1M Curncy' },
  USDPEN: { format: '', coverage: 'none', example: '' }, // No NDF data available
  USDARS: { format: '', coverage: 'none', example: '' }, // No NDF data available
  
  // Currencies that use NDF for extended coverage beyond standard forwards
  USDKRW: { format: 'KWN', coverage: '1W-5Y', example: 'KWN1M Curncy' },
  USDPHP: { format: 'PPN', coverage: '1W-9M', example: 'PPN1M Curncy' },
  USDMYR: { format: 'MRN', coverage: '1W-9M', example: 'MRN1M Curncy' },
  USDCOP: { format: 'CLN', coverage: '1W-3Y', example: 'CLN1M Curncy' }
}

// Check if a currency pair uses NDF tickers
export const usesNDF = (pair: string): boolean => {
  return pair in NDF_MAPPINGS && NDF_MAPPINGS[pair].format !== ''
}

// Get NDF ticker for a specific tenor
export const getNDFTicker = (pair: string, tenor: string): string | null => {
  const mapping = NDF_MAPPINGS[pair]
  if (!mapping || !mapping.format) return null
  
  // Check if tenor is within coverage
  const coverage = mapping.coverage
  if (coverage === 'none') return null
  
  // Parse coverage limits
  const maxTenor = getMaxNDFTenor(pair)
  if (maxTenor) {
    const tenorOrder = ['1W', '2W', '1M', '2M', '3M', '6M', '9M', '1Y', '18M', '2Y', '3Y', '4Y', '5Y']
    const maxIndex = tenorOrder.indexOf(maxTenor)
    const requestedIndex = tenorOrder.indexOf(tenor)
    
    // If requested tenor is beyond coverage, return null
    if (requestedIndex > maxIndex) return null
  }
  
  return `${mapping.format}${tenor} Curncy`
}

// Get maximum tenor available for NDF
export const getMaxNDFTenor = (pair: string): string | null => {
  const mapping = NDF_MAPPINGS[pair]
  if (!mapping || !mapping.coverage || mapping.coverage === 'none') return null
  
  const coverage = mapping.coverage.split('-')
  if (coverage.length > 1) {
    return coverage[1]
  }
  return null
}