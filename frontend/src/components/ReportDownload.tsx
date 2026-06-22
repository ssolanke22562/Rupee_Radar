import React, { useState } from 'react';
import { FileText, Download, Loader } from 'lucide-react';

interface ReportDownloadProps {
  sessionId: string;
  filename: string;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export function ReportDownload({ sessionId, filename }: ReportDownloadProps) {
  const [loading, setLoading] = useState(false);

  const handleDownload = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/report`);
      if (!response.ok) throw new Error('Failed to generate report');
      
      const html = await response.text();
      const blob = new Blob([html], { type: 'text/html' });
      const url = URL.createObjectURL(blob);
      
      const a = document.createElement('a');
      a.href = url;
      a.download = `rupeeradar-report-${filename.replace(/\.[^/.]+$/, '')}.html`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Report download failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const handlePrint = () => {
    window.open(`${API_BASE_URL}/sessions/${sessionId}/report`, '_blank');
  };

  return (
    <div style={{ display: 'flex', gap: '0.5rem' }}>
      <button
        onClick={handleDownload}
        disabled={loading}
        className="btn btn-secondary"
        style={{ padding: '0.5rem 1rem', gap: '0.25rem', fontSize: '0.85rem' }}
        title="Download HTML Report"
      >
        {loading ? (
          <Loader size={16} className="spin" />
        ) : (
          <Download size={16} />
        )}
        <span>Report</span>
      </button>
      <button
        onClick={handlePrint}
        className="btn btn-secondary"
        style={{ padding: '0.5rem 1rem', gap: '0.25rem', fontSize: '0.85rem' }}
        title="Open Print-Friendly Report"
      >
        <FileText size={16} />
        <span>Print</span>
      </button>
    </div>
  );
}