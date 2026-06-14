import { Link, useLocation } from 'react-router-dom';
import './Sidebar.css';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

const NAV_ITEMS = [
  { label: 'Dashboard', path: '/', icon: '📊' },
  { label: 'Clients', path: '/clients', icon: '👥' },
  { label: 'Plans', path: '/plans', icon: '📝' },
  { label: 'Articles', path: '/articles', icon: '📰' },
];

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const location = useLocation();

  return (
    <aside className={`sidebar ${isOpen ? 'sidebar--open' : ''}`}>
      <div className="sidebar__header">
        <Link to="/" className="sidebar__brand" onClick={onClose}>
          NutriPlan
        </Link>
        <button className="sidebar__close" onClick={onClose} aria-label="Close menu">
          ×
        </button>
      </div>

      <nav className="sidebar__nav">
        {NAV_ITEMS.map((item) => {
          const isActive = location.pathname === item.path || 
                          (item.path !== '/' && location.pathname.startsWith(item.path));
          
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`sidebar__link ${isActive ? 'sidebar__link--active' : ''}`}
              onClick={onClose}
            >
              <span className="sidebar__icon">{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="sidebar__footer">
        <Link to="/settings" className="sidebar__link" onClick={onClose}>
          <span className="sidebar__icon">⚙️</span>
          Settings
        </Link>
      </div>
    </aside>
  );
}
