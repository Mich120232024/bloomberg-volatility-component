import { Outlet } from 'react-router-dom'
// import Sidebar from '../Sidebar'  // Component doesn't exist
import { Header } from '../Header'

const Layout = () => {
  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      {/* <Sidebar /> Component doesn't exist */}
      
      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <Header />
        
        {/* Page Content */}
        <main className="flex-1 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default Layout