// GZC Volatility Surface Theme System
export interface Theme {
  name: string
  // Core colors
  primary: string
  secondary: string
  accent: string
  
  // Backgrounds
  background: string
  surface: string
  surfaceAlt: string
  
  // Text colors
  text: string
  textSecondary: string
  textTertiary: string
  
  // Borders
  border: string
  borderLight: string
  
  // Status colors
  success: string
  danger: string
  warning: string
  info: string
  muted: string
  
  // Special effects
  gradient: string
  headerColor: string
}

// Standardized GZC Green System - matching the main app
const GZC_GREEN = {
  base: '#7A9E65',      // Primary institutional green
  light: '#95BD78',     // 20% lighter
  lighter: '#ABD38F',   // 40% lighter
  dark: '#5B7C4B',      // 20% darker
  darker: '#436138',    // 40% darker
  // Opacity variants
  opacity90: 'E6',      // 90% opacity
  opacity80: 'CC',      // 80% opacity
  opacity60: '99',      // 60% opacity
  opacity40: '66',      // 40% opacity
  opacity20: '33',      // 20% opacity
  opacity10: '1A'       // 10% opacity
}

export const themes: Record<string, Theme> = {
  // GZC Dark - Default theme matching main app
  'gzc-dark': {
    name: 'GZC Dark',
    primary: GZC_GREEN.base,
    secondary: GZC_GREEN.light,
    accent: GZC_GREEN.lighter,
    background: '#1A1A1A',
    surface: '#2A2A2A',
    surfaceAlt: '#3A3A3A',
    text: '#f8f6f0',
    textSecondary: '#c8c0b0',
    textTertiary: '#9a9488',
    border: '#3a3632',
    borderLight: '#3a3632' + GZC_GREEN.opacity40,
    success: GZC_GREEN.light,
    danger: '#D69A82',
    warning: '#E6D690',
    info: '#8BB4DD',
    muted: '#9a9488',
    gradient: `linear-gradient(135deg, ${GZC_GREEN.base} 0%, ${GZC_GREEN.light} 100%)`,
    headerColor: GZC_GREEN.base
  }
}

export const defaultTheme = themes['gzc-dark']