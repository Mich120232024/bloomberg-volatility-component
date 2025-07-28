import { BrowserRouter as Router } from 'react-router-dom'
import { ThemeProvider, useTheme } from './contexts/ThemeContext'
import { Header } from './components/Header'
import { MainAppContainer } from './components/MainAppContainer'

// Inner app component that uses theme
function AppContent() {
  const { currentTheme } = useTheme()
  
  return (
    <div className="min-h-screen flex flex-col" style={{ 
      backgroundColor: currentTheme.background, 
      color: currentTheme.text 
    }}>
      {/* Header */}
      <Header />
      
      {/* Main Content */}
      <main className="flex-1 overflow-hidden">
        <MainAppContainer />
      </main>
    </div>
  )
}

function App() {
  return (
    <ThemeProvider>
      <Router>
        <AppContent />
      </Router>
    </ThemeProvider>
  )
}

export default App