import React, { useState, useEffect } from 'react';
import { PieChart, Moon, Sun } from 'lucide-react';
import { Link } from 'react-router-dom';
import { NetworkStatus } from './NetworkStatus';

interface LayoutProps {
  children: React.ReactNode;
}

const THEME_STORAGE_KEY = 'rupeeradar-theme';

function safeGetLocalStorage(key: string, fallback: string): string {
  try {
    const saved = localStorage.getItem(key);
    return saved || fallback;
  } catch (e) {
    // Edge Case 5.3: QuotaExceededError or localStorage unavailable
    return fallback;
  }
}

function safeSetLocalStorage(key: string, value: string): void {
  try {
    localStorage.setItem(key, value);
  } catch (e) {
    // Edge Case 5.3: Silently fail if QuotaExceededError
    console.warn('localStorage quota exceeded or unavailable. Theme preference not saved.');
  }
}

export function Layout({ children }: LayoutProps) {
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    const saved = safeGetLocalStorage(THEME_STORAGE_KEY, 'dark');
    return (saved as 'light' | 'dark') || 'dark';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    safeSetLocalStorage(THEME_STORAGE_KEY, theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => (prev === 'light' ? 'dark' : 'light'));
  };

  return (
    <div className="app-container" style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Header */}
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-color)', paddingBottom: '1rem' }}>
        <div>
          <Link to="/" style={{ textDecoration: 'none' }}>
            <h1 style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--color-primary)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <PieChart size={32} /> RupeeRadar
            </h1>
          </Link>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '0.2rem' }}>AI-Powered Personal Finance Statement Ingestion Engine</p>
        </div>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', backgroundColor: 'var(--color-success)' }}></span>
            <span>API Server Online</span>
          </div>
          <button onClick={toggleTheme} className="btn btn-secondary" style={{ padding: '0.5rem', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }} aria-label="Toggle theme">
            {theme === 'light' ? <Moon size={18} /> : <Sun size={18} />}
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main style={{ display: 'flex', flexDirection: 'column', gap: '2rem', flex: 1 }}>
        {children}
      </main>

      {/* Footer */}
      <footer style={{ marginTop: 'auto', borderTop: '1px solid var(--border-color)', paddingTop: '1.5rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
        <p>© 2026 RupeeRadar Finance. All data is processed locally and privately. Session data purges automatically within 24 hours.</p>
      </footer>

      {/* Edge Case 5.4: Network loss banner */}
      <NetworkStatus />
    </div>
  );
}
