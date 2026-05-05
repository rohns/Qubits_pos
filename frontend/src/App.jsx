import { useState, useEffect } from 'react';
import api from './api';
import Login from './components/Login';
import Cashier from './components/Cashier';
import Reports from './components/Reports';
import Expenses from './components/Expenses';
import Products from './components/Products';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import logo from './assets/logo.svg';

const NAV = [
  { key: 'cashier',  label: 'Cashier',  icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="2" y="5" width="20" height="14" rx="2"/><line x1="2" y1="10" x2="22" y2="10"/></svg> },
  { key: 'reports',  label: 'Reports',  icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg> },
  { key: 'expenses', label: 'Expenses', icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg> },
];

export default function App() {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('user')) || null; } catch { return null; }
  });
  const [page, setPage]   = useState('cashier');
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'dark');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  useEffect(() => {
    const token = localStorage.getItem('accessToken');
    if (token && !user) {
      api.get('/auth/me/').then(r => setUser(r.data)).catch(handleLogout);
    }
  }, []);

  const handleLogin  = userData => { localStorage.setItem('user', JSON.stringify(userData)); setUser(userData); };
  const handleLogout = () => { localStorage.clear(); setUser(null); };

  if (!user) return <Login onLogin={handleLogin} logo={logo} theme={theme} setTheme={setTheme} />;

  const isStaff = user.is_staff || user.is_superuser;
  const nav = isStaff ? [...NAV, { key: 'products', label: 'Products', icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 01-8 0"/></svg> }] : NAV;

  return (
    <div className="pos-app">
      <header className="pos-header">
        <div className="pos-header-inner">
          <div className="pos-brand">
            <img src={logo} alt="Logo" className="pos-logo" />
            <div>
              <div className="pos-brand-name">Qubits Cyber Services</div>
              <div className="pos-brand-sub">Printing · Online Applications · Digital Support</div>
            </div>
          </div>

          <nav className="pos-nav">
            {nav.map(n => (
              <button key={n.key} className={`pos-nav-btn ${page === n.key ? 'active' : ''}`} onClick={() => setPage(n.key)}>
                {n.icon}{n.label}
              </button>
            ))}
          </nav>

          <div className="pos-user-area">
            <button className="theme-toggle" onClick={() => setTheme(t => t === 'dark' ? 'light' : 'dark')} title="Toggle theme">
              {theme === 'dark'
                ? <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
                : <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/></svg>}
            </button>
            <div className="pos-user-info">
              <div className="pos-user-avatar">{(user.username || 'U')[0].toUpperCase()}</div>
              <div>
                <div className="pos-user-name">{user.username}</div>
                <div className="pos-user-role">{user.is_superuser ? 'Super Admin' : user.is_staff ? 'Admin' : 'Cashier'}</div>
              </div>
            </div>
            <button className="pos-logout-btn" onClick={handleLogout} title="Logout">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
            </button>
          </div>
        </div>
      </header>

      <ToastContainer position="top-right" autoClose={2500} hideProgressBar={false} newestOnTop closeOnClick pauseOnHover theme={theme} />

      <main className="pos-main">
        {page === 'cashier'  && <Cashier user={user} />}
        {page === 'reports'  && <Reports />}
        {page === 'expenses' && <Expenses />}
        {page === 'products' && isStaff && <Products />}
      </main>
    </div>
  );
}
