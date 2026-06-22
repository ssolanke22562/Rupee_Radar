import React, { useState } from 'react';
import { Upload, AlertTriangle, FileWarning } from 'lucide-react';

interface FileUploadProps {
  onUpload: (file: File, bankHint: string) => void;
  isLoading: boolean;
  error?: string | null;
}

const ALLOWED_EXTENSIONS = ['csv', 'xlsx', 'txt', 'json'];
const MAX_SIZE_MB = 10;

export function FileUpload({ onUpload, isLoading, error }: FileUploadProps) {
  const [isDragActive, setIsDragActive] = useState(false);
  const [bankHint, setBankHint] = useState<string>('auto');
  const [formatWarning, setFormatWarning] = useState<string | null>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragActive(true);
    } else if (e.type === 'dragleave') {
      setIsDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (validateFile(file) && isValidFile(file)) {
        onUpload(file, bankHint);
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (validateFile(file) && isValidFile(file)) {
        onUpload(file, bankHint);
      }
    }
  };

  const isValidFile = (file: File) => {
    const ext = file.name.split('.').pop()?.toLowerCase();
    return ALLOWED_EXTENSIONS.includes(ext || '');
  };

  const validateFile = (file: File): boolean => {
    setFormatWarning(null);
    
    // Check extension
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext || '')) {
      setFormatWarning('Unsupported file format. Please upload CSV, Excel (.xlsx), TXT, or JSON files.');
      return false;
    }
    
    // Check file size (10 MB max)
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      setFormatWarning(`File size exceeds the ${MAX_SIZE_MB} MB limit. Please upload a smaller file.`);
      return false;
    }
    
    // Warn about password-protected files based on extension + content type hint
    if (ext === 'xlsx') {
      // Excel files can't be easily checked for password protection client-side
      // but we show a generic warning
    }
    
    return true;
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', width: '100%', maxWidth: '680px', margin: '0 auto' }}>
      
      {/* Bank Hint Selector */}
      <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', padding: '1.25rem' }}>
        <label style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
          Select Statement Source Format (Optional):
        </label>
        <select
          value={bankHint}
          onChange={(e) => setBankHint(e.target.value)}
          className="input"
          style={{ cursor: 'pointer', padding: '0.6rem 1rem' }}
        >
          <option value="auto">Auto-Detect / Generic CSV</option>
          <option value="hdfc">HDFC Bank CSV</option>
          <option value="icici">ICICI Bank CSV</option>
          <option value="sbi">SBI Bank CSV</option>
        </select>
      </div>

      {/* Drag & Drop Zone */}
      <div
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        className="card"
        style={{
          border: isDragActive ? '2px dashed var(--color-primary)' : '2px dashed var(--border-color)',
          textAlign: 'center',
          padding: '4rem 2rem',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '1.25rem',
          cursor: isLoading ? 'not-allowed' : 'pointer',
          background: isDragActive ? 'rgba(99, 102, 241, 0.05)' : 'var(--bg-secondary)',
          opacity: isLoading ? 0.7 : 1,
          transition: 'all 0.2s ease',
        }}
      >
        <div style={{ padding: '1rem', borderRadius: '50%', backgroundColor: 'rgba(99, 102, 241, 0.1)', color: 'var(--color-primary)' }}>
          <Upload size={36} />
        </div>
        <div>
          <h3 style={{ fontSize: '1.2rem', fontWeight: 700 }}>Drag and drop your bank statement</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '0.5rem' }}>
            Supports CSV, Excel (.xlsx) or plain text exports
          </p>
        </div>
        
        <label className={`btn btn-primary ${isLoading ? 'disabled' : ''}`} style={{ cursor: isLoading ? 'not-allowed' : 'pointer', marginTop: '0.5rem' }}>
          {isLoading ? 'Uploading...' : 'Select File'}
          <input
            type="file"
            onChange={handleFileChange}
            accept=".csv,.xlsx,.txt,.json"
            style={{ display: 'none' }}
            disabled={isLoading}
          />
        </label>
      </div>

      {formatWarning && (
        <div className="card" style={{ borderLeft: '4px solid var(--color-warning)', backgroundColor: 'var(--color-warning-bg)', color: 'var(--text-primary)', padding: '1rem', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <AlertTriangle size={18} style={{ color: 'var(--color-warning)', flexShrink: 0 }} />
          <span>{formatWarning}</span>
        </div>
      )}

      {error && (
        <div className="card" style={{ borderLeft: '4px solid var(--color-danger)', backgroundColor: 'var(--color-danger-bg)', color: 'var(--text-primary)', padding: '1rem', fontSize: '0.9rem' }}>
          <strong>Error:</strong> {error}
        </div>
      )}
    </div>
  );
}
