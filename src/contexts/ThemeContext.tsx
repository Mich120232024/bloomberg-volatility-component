import React, { createContext, useContext, useState, useEffect } from 'react'
import { themes, Theme } from '../theme/themes'

interface ThemeContextType {
  currentTheme: Theme
  themeName: string
  setTheme: (themeName: string) => void
  availableThemes: string[]
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export const useTheme = () => {
  const context = useContext(ThemeContext)
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}

interface ThemeProviderProps {
  children: React.ReactNode
  defaultTheme?: string
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ 
  children, 
  defaultTheme = 'gzc-dark' 
}) => {
  const [themeName, setThemeName] = useState<string>(() => {
    // Try to get theme from localStorage
    const savedTheme = localStorage.getItem('gzc-volatility-theme')
    return savedTheme && themes[savedTheme] ? savedTheme : defaultTheme
  })

  const setTheme = (newThemeName: string) => {
    if (themes[newThemeName]) {
      setThemeName(newThemeName)
      localStorage.setItem('gzc-volatility-theme', newThemeName)
      
      // Apply theme to document root for CSS variables
      const root = document.documentElement
      const theme = themes[newThemeName]
      
      // Set CSS variables
      root.style.setProperty('--theme-primary', theme.primary)
      root.style.setProperty('--theme-secondary', theme.secondary)
      root.style.setProperty('--theme-accent', theme.accent)
      root.style.setProperty('--theme-background', theme.background)
      root.style.setProperty('--theme-surface', theme.surface)
      root.style.setProperty('--theme-surface-alt', theme.surfaceAlt)
      root.style.setProperty('--theme-text', theme.text)
      root.style.setProperty('--theme-text-secondary', theme.textSecondary)
      root.style.setProperty('--theme-text-tertiary', theme.textTertiary)
      root.style.setProperty('--theme-border', theme.border)
      root.style.setProperty('--theme-border-light', theme.borderLight)
      root.style.setProperty('--theme-success', theme.success)
      root.style.setProperty('--theme-danger', theme.danger)
      root.style.setProperty('--theme-warning', theme.warning)
      root.style.setProperty('--theme-info', theme.info)
      
      // Set data attribute for theme-specific CSS
      root.setAttribute('data-theme', newThemeName)
    }
  }

  // Apply theme on mount and theme change
  useEffect(() => {
    setTheme(themeName)
  }, [themeName])

  const value: ThemeContextType = {
    currentTheme: themes[themeName],
    themeName,
    setTheme,
    availableThemes: Object.keys(themes)
  }

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  )
}