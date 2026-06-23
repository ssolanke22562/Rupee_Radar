import { useState, useEffect, useCallback } from 'react';
import { WifiOff, X } from 'lucide-react';

export function NetworkStatus() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [dismissed, setDismissed] = useState(false);

  const handleOnline = useCallback(() => setIsOnline(true), []);
  const handleOffline = useCallback(() => {
    setIsOnline(false);
    setDismissed(false);
  }, []);

  useEffect(() => {
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [handleOnline, handleOffline]);

  if (isOnline || dismissed) return null;

  return (
    <div
      style={{
        position: 'fixed',
        bottom: '1.5rem',
        right: '1.5rem',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        gap: '0.75rem',
        padding: '0.85rem 1.25rem',
        borderRadius: '12px',
        backgroundColor: '#fef2f2',
        border: '1px solid #fecaca',
        color: '#991b1b',
        boxShadow: '0 10px 25px rgba(0,0,0,0.15)',
        fontSize: '0.85rem',
        fontWeight: 600,
        animation: 'slideInUp 0.3s ease',
        maxWidth: '360px',
      }}
    >
      <WifiOff size={20} style={{ flexShrink: 0 }} />
      <span>You are currently offline. Save operations may fail until connection is restored.</span>
      <button
        onClick={() => setDismissed(true)}
        style={{
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          color: '#991b1b',
          padding: '0.25rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
        }}
        aria-label="Dismiss"
      >
        <X size={16} />
      </button>
    </div>
  );
}