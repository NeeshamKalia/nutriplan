import { type ReactNode, Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useParams } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';
import { LoadingSpinner } from './components/ui/LoadingSpinner';

// Layouts (always needed)
import { MainLayout } from './components/layout/MainLayout';

// Auth pages — eagerly loaded (entry point for unauthenticated users)
import { Login } from './pages/auth/Login';
import { Register } from './pages/auth/Register';

// All other pages — lazy loaded for route-level code splitting.
// This reduces the initial JS bundle so users only download what they navigate to.
const Dashboard = lazy(() => import('./pages/dashboard/Dashboard').then(m => ({ default: m.Dashboard })));
const ClientsPage = lazy(() => import('./pages/clients/ClientsPage').then(m => ({ default: m.ClientsPage })));
const ClientDetailPage = lazy(() => import('./pages/clients/ClientDetailPage').then(m => ({ default: m.ClientDetailPage })));
const ClientFormPage = lazy(() => import('./pages/clients/ClientFormPage').then(m => ({ default: m.ClientFormPage })));
const PlanEditorPage = lazy(() => import('./pages/plans/PlanEditorPage').then(m => ({ default: m.PlanEditorPage })));
const ArticlesPage = lazy(() => import('./pages/articles/ArticlesPage').then(m => ({ default: m.ArticlesPage })));
const ArticleEditorPage = lazy(() => import('./pages/articles/ArticleEditorPage').then(m => ({ default: m.ArticleEditorPage })));
const ProtocolsPage = lazy(() => import('./pages/protocols/ProtocolsPage').then(m => ({ default: m.ProtocolsPage })));
const SettingsPage = lazy(() => import('./pages/settings/SettingsPage').then(m => ({ default: m.SettingsPage })));
const DietitianLandingPage = lazy(() => import('./pages/public/DietitianLandingPage').then(m => ({ default: m.DietitianLandingPage })));
const PublicArticlePage = lazy(() => import('./pages/public/PublicArticlePage').then(m => ({ default: m.PublicArticlePage })));

/** Full-page loading spinner shown while lazy chunks are being fetched. */
function PageLoader() {
  return (
    <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <LoadingSpinner size="lg" />
    </div>
  );
}

function ProtectedRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <PageLoader />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

function PublicRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <PageLoader />;
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
      <Suspense fallback={<PageLoader />}>
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
      </Suspense>
    </BrowserRouter>
  );
}

export default App;
