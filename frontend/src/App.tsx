import { type ReactNode } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useParams } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';
import { LoadingSpinner } from './components/ui/LoadingSpinner';

// Layouts
import { MainLayout } from './components/layout/MainLayout';

// Pages — Auth
import { Login } from './pages/auth/Login';
import { Register } from './pages/auth/Register';

// Pages — Dashboard
import { Dashboard } from './pages/dashboard/Dashboard';

// Pages — Clients
import { ClientsPage } from './pages/clients/ClientsPage';
import { ClientDetailPage } from './pages/clients/ClientDetailPage';
import { ClientFormPage } from './pages/clients/ClientFormPage';

// Pages — Plans
import { PlanEditorPage } from './pages/plans/PlanEditorPage';

// Pages — Articles
import { ArticlesPage } from './pages/articles/ArticlesPage';
import { ArticleEditorPage } from './pages/articles/ArticleEditorPage';

// Pages — Protocols
import { ProtocolsPage } from './pages/protocols/ProtocolsPage';

// Pages — Settings
import { SettingsPage } from './pages/settings/SettingsPage';

// Pages — Public
import { DietitianLandingPage } from './pages/public/DietitianLandingPage';
import { PublicArticlePage } from './pages/public/PublicArticlePage';

function ProtectedRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

function PublicRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return children;
}

function LegacyPublicRedirect({ withArticle = false }: { withArticle?: boolean }) {
  const { slug, articleSlug } = useParams<{ slug: string; articleSlug?: string }>();
  if (!slug) return <Navigate to="/" replace />;
  if (withArticle && articleSlug) {
    return <Navigate to={`/p/${slug}/${articleSlug}`} replace />;
  }
  return <Navigate to={`/p/${slug}`} replace />;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Auth Routes */}
        <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
        <Route path="/register" element={<PublicRoute><Register /></PublicRoute>} />

        {/* Public — Dietitian Landing Page & Articles */}
        <Route path="/p/:slug" element={<DietitianLandingPage />} />
        <Route path="/p/:slug/:articleSlug" element={<PublicArticlePage />} />
        <Route path="/d/:slug" element={<LegacyPublicRedirect />} />
        <Route path="/d/:slug/:articleSlug" element={<LegacyPublicRedirect withArticle />} />

        {/* Protected Dashboard Routes */}
        <Route path="/" element={<ProtectedRoute><MainLayout /></ProtectedRoute>}>
          <Route index element={<Dashboard />} />
          <Route path="clients" element={<ClientsPage />} />
          <Route path="clients/new" element={<ClientFormPage />} />
          <Route path="clients/:id" element={<ClientDetailPage />} />
          <Route path="clients/:id/edit" element={<ClientFormPage />} />
          <Route path="plans/:id" element={<PlanEditorPage />} />
          <Route path="protocols" element={<ProtocolsPage />} />
          <Route path="articles" element={<ArticlesPage />} />
          <Route path="articles/new" element={<ArticleEditorPage />} />
          <Route path="articles/:id/edit" element={<ArticleEditorPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
