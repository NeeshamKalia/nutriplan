import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../ui/Button';
import './TopBar.css';

interface TopBarProps {
  onMenuClick: () => void;
}

export function TopBar({ onMenuClick }: TopBarProps) {
  const { user, logout } = useAuth();

  return (
    <header className="topbar">
      <div className="topbar__left">
        <button className="topbar__menu-btn" onClick={onMenuClick} aria-label="Open menu">
          ☰
        </button>
      </div>

      <div className="topbar__right">
        {user && (
          <div className="topbar__user">
            <div className="topbar__user-info">
              <span className="topbar__user-name">{user.full_name}</span>
              <span className="topbar__user-email">{user.email}</span>
            </div>
            <div className="topbar__avatar">
              {user.full_name.charAt(0).toUpperCase()}
            </div>
            <Button variant="ghost" size="sm" onClick={logout}>
              Log out
            </Button>
          </div>
        )}
      </div>
    </header>
  );
}
