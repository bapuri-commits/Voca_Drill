import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Study from './pages/Study';
import Words from './pages/Words';
import Stats from './pages/Stats';
import PdfViewer from './pages/PdfViewer';

function Nav() {
  const loc = useLocation();
  const tabs = [
    { path: '/', label: 'Home', icon: '🏠' },
    { path: '/study', label: 'Study', icon: '📖' },
    { path: '/words', label: 'Words', icon: '📝' },
    { path: '/pdf', label: 'Book', icon: '📚' },
    { path: '/stats', label: 'Stats', icon: '📈' },
  ];

  if (loc.pathname === '/study') return null;

  return (
    <nav className="fixed bottom-0 left-0 right-0 flex justify-around py-2.5 px-1 z-50"
         style={{ background: 'var(--color-surface)', borderTop: '1px solid var(--color-surface-light)' }}>
      {tabs.map(t => (
        <Link key={t.path} to={t.path}
              className="flex flex-col items-center gap-0.5 text-xs no-underline transition-colors"
              style={{ color: loc.pathname === t.path ? 'var(--color-primary)' : 'var(--color-text-dim)' }}>
          <span className="text-lg">{t.icon}</span>
          <span>{t.label}</span>
        </Link>
      ))}
    </nav>
  );
}

function AuthGate() {
  const { authenticated, initializing, logout } = useAuth();
  const loc = useLocation();

  if (initializing) {
    return (
      <div className="fixed inset-0 flex items-center justify-center" style={{ background: 'var(--color-bg)' }}>
        <div className="w-8 h-8 rounded-full border-3 border-t-transparent animate-spin"
             style={{ borderColor: 'var(--color-primary)', borderTopColor: 'transparent' }} />
      </div>
    );
  }

  if (!authenticated) return <Login />;

  const isStudy = loc.pathname === '/study';

  return (
    <>
      <div className={isStudy ? '' : 'pb-16 min-h-screen'}>
        <Routes>
          <Route path="/" element={<Dashboard onLogout={logout} />} />
          <Route path="/study" element={<Study />} />
          <Route path="/words" element={<Words />} />
          <Route path="/pdf" element={<PdfViewer />} />
          <Route path="/stats" element={<Stats />} />
        </Routes>
      </div>
      <Nav />
    </>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AuthGate />
      </AuthProvider>
    </BrowserRouter>
  );
}
