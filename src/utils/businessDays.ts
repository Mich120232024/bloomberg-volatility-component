// Business day calculations for financial markets

// Major market holidays (US/UK/EUR) - can be expanded
const MARKET_HOLIDAYS_2025 = [
  '2025-01-01', // New Year's Day
  '2025-01-20', // MLK Day (US)
  '2025-02-17', // Presidents Day (US)
  '2025-04-18', // Good Friday
  '2025-04-21', // Easter Monday (EUR/UK)
  '2025-05-26', // Memorial Day (US)
  '2025-07-04', // Independence Day (US)
  '2025-09-01', // Labor Day (US)
  '2025-11-27', // Thanksgiving (US)
  '2025-12-25', // Christmas
  '2025-12-26', // Boxing Day (UK)
]

const MARKET_HOLIDAYS_2024 = [
  '2024-01-01', // New Year's Day
  '2024-01-15', // MLK Day (US)
  '2024-02-19', // Presidents Day (US)
  '2024-03-29', // Good Friday
  '2024-04-01', // Easter Monday (EUR/UK)
  '2024-05-27', // Memorial Day (US)
  '2024-07-04', // Independence Day (US)
  '2024-09-02', // Labor Day (US)
  '2024-11-28', // Thanksgiving (US)
  '2024-12-25', // Christmas
  '2024-12-26', // Boxing Day (UK)
]

// Combine all holidays
const ALL_HOLIDAYS = [...MARKET_HOLIDAYS_2024, ...MARKET_HOLIDAYS_2025]

export function isWeekend(date: Date): boolean {
  const day = date.getDay()
  return day === 0 || day === 6 // Sunday = 0, Saturday = 6
}

export function isHoliday(date: Date): boolean {
  const dateStr = date.toISOString().slice(0, 10)
  return ALL_HOLIDAYS.includes(dateStr)
}

export function isBusinessDay(date: Date): boolean {
  return !isWeekend(date) && !isHoliday(date)
}

export function getPreviousBusinessDay(date: Date): Date {
  const result = new Date(date)
  
  // Keep going back until we find a business day
  do {
    result.setDate(result.getDate() - 1)
  } while (!isBusinessDay(result))
  
  return result
}

export function getNextBusinessDay(date: Date): Date {
  const result = new Date(date)
  
  // Keep going forward until we find a business day
  do {
    result.setDate(result.getDate() + 1)
  } while (!isBusinessDay(result))
  
  return result
}

export function adjustToBusinessDay(date: Date, direction: 'previous' | 'next' = 'previous'): Date {
  if (isBusinessDay(date)) {
    return date
  }
  
  return direction === 'previous' 
    ? getPreviousBusinessDay(date)
    : getNextBusinessDay(date)
}

// Get T-n business days
export function getBusinessDaysAgo(n: number, fromDate: Date = new Date()): Date {
  let result = new Date(fromDate)
  let businessDaysCount = 0
  
  while (businessDaysCount < n) {
    result.setDate(result.getDate() - 1)
    if (isBusinessDay(result)) {
      businessDaysCount++
    }
  }
  
  return result
}