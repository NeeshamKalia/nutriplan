import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';
import './MainLayout.css';

export function MainLayout() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const toggleSidebar = () => setIsSidebarOpen(!isSidebarOpen);
  const closeSidebar = () => setIsSidebarOpen(false);

  return (
    <div className="main-layout">
      {/* Mobile overlay */}
      {isSidebarOpen && (
        <div className="main-layout__overlay" onClick={closeSidebar} />
      )}

      <Sidebar isOpen={isSidebarOpen} onClose={closeSidebar} />
      
      <div className="main-layout__content">
        <TopBar onMenuClick={toggleSidebar} />
        
        <main className="main-layout__main animate-fade-in">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
