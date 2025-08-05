/**
 * Production-ready Yield Curve Database Service
 * Last validated: 2025-01-31
 * Based on Bloomberg Terminal data and external validation
 */

export interface YieldCurveTicker {
  ticker: string
  tenor: number  // Days to maturity
  label: string  // Display label
  type: 'money_market' | 'ois' | 'government_bond' | 'swap'
}

export interface YieldCurveConfig {
  title: string
  currency: string
  instruments: YieldCurveTicker[]
}

// Production OIS curves validated against Bloomberg Terminal
const DATABASE_CURVES: Record<string, YieldCurveConfig> = {
  USD: {
    title: 'USD SOFR OIS Curve',
    currency: 'USD',
    instruments: [
      { ticker: 'SOFRRATE Index', tenor: 1, label: 'ON', type: 'money_market' },
      { ticker: 'USOSFR1 Curncy', tenor: 365, label: '1Y', type: 'ois' },
      { ticker: 'USOSFR2 Curncy', tenor: 730, label: '2Y', type: 'ois' },
      { ticker: 'USOSFR3 Curncy', tenor: 1095, label: '3Y', type: 'ois' },
      { ticker: 'USOSFR4 Curncy', tenor: 1460, label: '4Y', type: 'ois' },
      { ticker: 'USOSFR5 Curncy', tenor: 1825, label: '5Y', type: 'ois' },
      { ticker: 'USOSFR6 Curncy', tenor: 2190, label: '6Y', type: 'ois' },
      { ticker: 'USOSFR7 Curncy', tenor: 2555, label: '7Y', type: 'ois' },
      { ticker: 'USOSFR8 Curncy', tenor: 2920, label: '8Y', type: 'ois' },
      { ticker: 'USOSFR9 Curncy', tenor: 3285, label: '9Y', type: 'ois' },
      { ticker: 'USOSFR10 Curncy', tenor: 3650, label: '10Y', type: 'ois' },
      { ticker: 'USOSFR12 Curncy', tenor: 4380, label: '12Y', type: 'ois' },
      { ticker: 'USOSFR15 Curncy', tenor: 5475, label: '15Y', type: 'ois' },
      { ticker: 'USOSFR20 Curncy', tenor: 7300, label: '20Y', type: 'ois' },
      { ticker: 'USOSFR25 Curncy', tenor: 9125, label: '25Y', type: 'ois' },
      { ticker: 'USOSFR30 Curncy', tenor: 10950, label: '30Y', type: 'ois' }
    ]
  },

  EUR: {
    title: 'EUR €STR OIS Curve',
    currency: 'EUR',
    instruments: [
      { ticker: 'ESTRON Index', tenor: 1, label: 'ON', type: 'money_market' },
      { ticker: 'EESWE1 Curncy', tenor: 365, label: '1Y', type: 'ois' },
      { ticker: 'EESWE2 Curncy', tenor: 730, label: '2Y', type: 'ois' },
      { ticker: 'EESWE3 Curncy', tenor: 1095, label: '3Y', type: 'ois' },
      { ticker: 'EESWE5 Curncy', tenor: 1825, label: '5Y', type: 'ois' },
      { ticker: 'EESWE7 Curncy', tenor: 2555, label: '7Y', type: 'ois' },
      { ticker: 'EESWE10 Curncy', tenor: 3650, label: '10Y', type: 'ois' },
      { ticker: 'EESWE15 Curncy', tenor: 5475, label: '15Y', type: 'ois' },
      { ticker: 'EESWE20 Curncy', tenor: 7300, label: '20Y', type: 'ois' },
      { ticker: 'EESWE25 Curncy', tenor: 9125, label: '25Y', type: 'ois' },
      { ticker: 'EESWE30 Curncy', tenor: 10950, label: '30Y', type: 'ois' }
    ]
  },

  GBP: {
    title: 'GBP SONIA OIS Curve',
    currency: 'GBP',
    instruments: [
      { ticker: 'SONIO/N Index', tenor: 1, label: 'ON', type: 'money_market' },
      { ticker: 'BPSO12 Curncy', tenor: 365, label: '1Y', type: 'ois' },
      { ticker: 'BPSOA Curncy', tenor: 730, label: '2Y', type: 'ois' },
      { ticker: 'BPSOB Curncy', tenor: 1095, label: '3Y', type: 'ois' },
      { ticker: 'BPSO4 Curncy', tenor: 1460, label: '4Y', type: 'ois' },
      { ticker: 'BPSO5 Curncy', tenor: 1825, label: '5Y', type: 'ois' },
      { ticker: 'BPSO6 Curncy', tenor: 2190, label: '6Y', type: 'ois' },
      { ticker: 'BPSO7 Curncy', tenor: 2555, label: '7Y', type: 'ois' },
      { ticker: 'BPSO8 Curncy', tenor: 2920, label: '8Y', type: 'ois' },
      { ticker: 'BPSO9 Curncy', tenor: 3285, label: '9Y', type: 'ois' },
      { ticker: 'BPSO10 Curncy', tenor: 3650, label: '10Y', type: 'ois' },
      { ticker: 'BPSO15 Curncy', tenor: 5475, label: '15Y', type: 'ois' },
      { ticker: 'BPSO20 Curncy', tenor: 7300, label: '20Y', type: 'ois' },
      { ticker: 'BPSO25 Curncy', tenor: 9125, label: '25Y', type: 'ois' },
      { ticker: 'BPSO30 Curncy', tenor: 10950, label: '30Y', type: 'ois' }
    ]
  },

  JPY: {
    title: 'JPY TONAR OIS Curve',
    currency: 'JPY',
    instruments: [
      { ticker: 'MUTKCALM Index', tenor: 1, label: 'ON', type: 'money_market' },
      { ticker: 'JYSO1 BGN Curncy', tenor: 365, label: '1Y', type: 'ois' },
      { ticker: 'JYSO2 Curncy', tenor: 730, label: '2Y', type: 'ois' },
      { ticker: 'JYSO3 Curncy', tenor: 1095, label: '3Y', type: 'ois' },
      { ticker: 'JYSO5 Curncy', tenor: 1825, label: '5Y', type: 'ois' },
      { ticker: 'JYSO7 Curncy', tenor: 2555, label: '7Y', type: 'ois' },
      { ticker: 'JYSO10 Curncy', tenor: 3650, label: '10Y', type: 'ois' },
      { ticker: 'JYSO12 Curncy', tenor: 4380, label: '12Y', type: 'ois' },
      { ticker: 'JYSO15 Curncy', tenor: 5475, label: '15Y', type: 'ois' },
      { ticker: 'JYSO20 Curncy', tenor: 7300, label: '20Y', type: 'ois' },
      { ticker: 'JYSO30 Curncy', tenor: 10950, label: '30Y', type: 'ois' }
    ]
  },

  CHF: {
    title: 'CHF SARON OIS Curve',
    currency: 'CHF',
    instruments: [
      { ticker: 'SSARON Index', tenor: 1, label: 'ON', type: 'money_market' },
      { ticker: 'SFSNT1 BGNL Curncy', tenor: 365, label: '1Y', type: 'ois' },
      { ticker: 'SFSNT2 BGNL Curncy', tenor: 730, label: '2Y', type: 'ois' },
      { ticker: 'SFSNT3 BGNL Curncy', tenor: 1095, label: '3Y', type: 'ois' },
      { ticker: 'SFSNT5 BGNL Curncy', tenor: 1825, label: '5Y', type: 'ois' },
      { ticker: 'SFSNT10 BGNL Curncy', tenor: 3650, label: '10Y', type: 'ois' }
    ]
  },

  CAD: {
    title: 'CAD CORRA OIS Curve',
    currency: 'CAD',
    instruments: [
      { ticker: 'CAONREPO Index', tenor: 1, label: 'ON', type: 'money_market' },
      { ticker: 'CDSO1 Curncy', tenor: 365, label: '1Y', type: 'ois' },
      { ticker: 'CDSO2 Curncy', tenor: 730, label: '2Y', type: 'ois' },
      { ticker: 'CDSO3 Curncy', tenor: 1095, label: '3Y', type: 'ois' },
      { ticker: 'CDSO10 Curncy', tenor: 3650, label: '10Y', type: 'ois' },
      { ticker: 'CDSO12 Curncy', tenor: 4380, label: '12Y', type: 'ois' },
      { ticker: 'CDSO15 Curncy', tenor: 5475, label: '15Y', type: 'ois' },
      { ticker: 'CDSO20 Curncy', tenor: 7300, label: '20Y', type: 'ois' },
      { ticker: 'CDSO30 Curncy', tenor: 10950, label: '30Y', type: 'ois' }
    ]
  },

  AUD: {
    title: 'AUD AONIA OIS Curve',
    currency: 'AUD',
    instruments: [
      { ticker: 'RBACOR Index', tenor: 1, label: 'ON', type: 'money_market' },
      { ticker: 'ADSO1 Curncy', tenor: 365, label: '1Y', type: 'ois' },
      { ticker: 'ADSO2 Curncy', tenor: 730, label: '2Y', type: 'ois' },
      { ticker: 'ADSO3 Curncy', tenor: 1095, label: '3Y', type: 'ois' },
      { ticker: 'ADSO10 Curncy', tenor: 3650, label: '10Y', type: 'ois' },
      { ticker: 'ADSO12 Curncy', tenor: 4380, label: '12Y', type: 'ois' },
      { ticker: 'ADSO15 Curncy', tenor: 5475, label: '15Y', type: 'ois' },
      { ticker: 'ADSO20 Curncy', tenor: 7300, label: '20Y', type: 'ois' },
      { ticker: 'ADSO30 Curncy', tenor: 10950, label: '30Y', type: 'ois' }
    ]
  },

  NZD: {
    title: 'NZD OCR OIS Curve',
    currency: 'NZD',
    instruments: [
      { ticker: 'NZOCRS Index', tenor: 1, label: 'ON', type: 'money_market' },
      { ticker: 'NDSO1 Curncy', tenor: 365, label: '1Y', type: 'ois' },
      { ticker: 'NDSO2 Curncy', tenor: 730, label: '2Y', type: 'ois' },
      { ticker: 'NDSO10 Curncy', tenor: 3650, label: '10Y', type: 'ois' },
      { ticker: 'NDSO12 Curncy', tenor: 4380, label: '12Y', type: 'ois' },
      { ticker: 'NDSO15 Curncy', tenor: 5475, label: '15Y', type: 'ois' },
      { ticker: 'NDSO20 Curncy', tenor: 7300, label: '20Y', type: 'ois' },
      { ticker: 'NDSO25 Curncy', tenor: 9125, label: '25Y', type: 'ois' }
    ]
  },

  SGD: {
    title: 'SGD SORA OIS Curve',
    currency: 'SGD',
    instruments: [
      { ticker: 'SORA Index', tenor: 1, label: 'ON', type: 'money_market' },
      { ticker: 'SDSOA1 BGN Curncy', tenor: 365, label: '1Y', type: 'ois' },
      { ticker: 'SDSOA1F BGN Curncy', tenor: 456, label: '15M', type: 'ois' },
      { ticker: 'SDSOA2 BGN Curncy', tenor: 730, label: '2Y', type: 'ois' },
      { ticker: 'SDSOA3 BGN Curncy', tenor: 1095, label: '3Y', type: 'ois' },
      { ticker: 'SDSOA4 BGN Curncy', tenor: 1460, label: '4Y', type: 'ois' },
      { ticker: 'SDSOA5 BGN Curncy', tenor: 1825, label: '5Y', type: 'ois' },
      { ticker: 'SDSOA7 BGN Curncy', tenor: 2555, label: '7Y', type: 'ois' },
      { ticker: 'SDSOA10 BGN Curncy', tenor: 3650, label: '10Y', type: 'ois' },
      { ticker: 'SDSOA12 BGN Curncy', tenor: 4380, label: '12Y', type: 'ois' }
    ]
  },

  BRL: {
    title: 'BRL CDI OIS Curve',
    currency: 'BRL',
    instruments: [
      { ticker: 'BZDIOVER Index', tenor: 1, label: 'ON', type: 'money_market' },
      { ticker: 'BZDI1 Curncy', tenor: 365, label: '1Y', type: 'ois' },
      { ticker: 'BZDI2 Curncy', tenor: 730, label: '2Y', type: 'ois' },
      { ticker: 'BZDI3 Curncy', tenor: 1095, label: '3Y', type: 'ois' },
      { ticker: 'BZDI5 Curncy', tenor: 1825, label: '5Y', type: 'ois' },
      { ticker: 'BZDI7 Curncy', tenor: 2555, label: '7Y', type: 'ois' },
      { ticker: 'BZDI10 Curncy', tenor: 3650, label: '10Y', type: 'ois' }
    ]
  },

  TRY: {
    title: 'TRY TLREF OIS Curve',
    currency: 'TRY',
    instruments: [
      { ticker: 'TLREFFIX Index', tenor: 1, label: 'ON', type: 'money_market' },
      { ticker: 'TYSO1 BGN Curncy', tenor: 365, label: '1Y', type: 'ois' },
      { ticker: 'TYSO1F BGN Curncy', tenor: 456, label: '15M', type: 'ois' },
      { ticker: 'TYSO1Z BGN Curncy', tenor: 548, label: '18M', type: 'ois' },
      { ticker: 'TYSO2 BGN Curncy', tenor: 730, label: '2Y', type: 'ois' },
      { ticker: 'TYSO2Z BGN Curncy', tenor: 912, label: '30M', type: 'ois' },
      { ticker: 'TYSO3 BGN Curncy', tenor: 1095, label: '3Y', type: 'ois' },
      { ticker: 'TYSO4 BGN Curncy', tenor: 1460, label: '4Y', type: 'ois' },
      { ticker: 'TYSO5 BGN Curncy', tenor: 1825, label: '5Y', type: 'ois' }
    ]
  },

  CZK: {
    title: 'CZK CZEONIA OIS Curve',
    currency: 'CZK',
    instruments: [
      { ticker: 'CZEONIA Index', tenor: 1, label: 'ON', type: 'money_market' },
      { ticker: 'CKSO1 BGN Curncy', tenor: 365, label: '1Y', type: 'ois' },
      { ticker: 'CKSO1Z BGN Curncy', tenor: 548, label: '18M', type: 'ois' },
      { ticker: 'CKSO2 BGN Curncy', tenor: 730, label: '2Y', type: 'ois' },
      { ticker: 'CKSO2Z BGN Curncy', tenor: 912, label: '30M', type: 'ois' },
      { ticker: 'CKSOA BGN Curncy', tenor: 1095, label: '3Y', type: 'ois' },
      { ticker: 'CKSOB BGN Curncy', tenor: 1460, label: '4Y', type: 'ois' },
      { ticker: 'CKSOC BGN Curncy', tenor: 1825, label: '5Y', type: 'ois' }
    ]
  },

  PLN: {
    title: 'PLN WIBOR OIS Curve',
    currency: 'PLN',
    instruments: [
      { ticker: 'WIBOON Index', tenor: 1, label: 'ON', type: 'money_market' },
      { ticker: 'WIBOR1M Index', tenor: 30, label: '1M', type: 'money_market' },
      { ticker: 'WIBOR3M Index', tenor: 90, label: '3M', type: 'money_market' },
      { ticker: 'WIBOR6M Index', tenor: 180, label: '6M', type: 'money_market' }
    ]
  },

  HUF: {
    title: 'HUF BUBOR OIS Curve',
    currency: 'HUF',
    instruments: [
      { ticker: 'BUBORON Index', tenor: 1, label: 'ON', type: 'money_market' },
      { ticker: 'BUBOR01M Index', tenor: 30, label: '1M', type: 'money_market' },
      { ticker: 'BUBOR03M Index', tenor: 90, label: '3M', type: 'money_market' },
      { ticker: 'BUBOR06M Index', tenor: 180, label: '6M', type: 'money_market' }
    ]
  }
}

// Currency categories for UI organization
export const G10_CURRENCIES = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD']
export const EM_CURRENCIES = ['SGD', 'BRL', 'TRY', 'CZK', 'PLN', 'HUF']

export function getYieldCurveConfig(currency: string): YieldCurveConfig | null {
  return DATABASE_CURVES[currency] || null
}

export function getAvailableCurrencies(): string[] {
  return Object.keys(DATABASE_CURVES).sort()
}

export function getAllTickers(): string[] {
  const allTickers: string[] = []
  Object.values(DATABASE_CURVES).forEach(config => {
    config.instruments.forEach(instrument => {
      allTickers.push(instrument.ticker)
    })
  })
  return [...new Set(allTickers)].sort()
}

export function getCurrencyTitle(currency: string): string {
  const config = DATABASE_CURVES[currency]
  return config ? config.title : `${currency} Yield Curve`
}

// Helper to convert days to years for scaling
export function tenorToYears(days: number): number {
  return days / 365
}
