import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileUpload } from '../components/FileUpload';
import { useUploadStatement } from '../api/hooks';
import { AlertCircle, Shield, Sparkles } from 'lucide-react';
import { ScrollAnimate } from '../components/ScrollAnimate';

export function Landing() {
  const navigate = useNavigate();
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  
  const uploadMutation = useUploadStatement();

  const handleUpload = (file: File, bankHint: string) => {
    setErrorMsg(null);
    uploadMutation.mutate(
      { file, bankHint: bankHint === 'auto' ? undefined : bankHint },
      {
        onSuccess: (data) => {
          navigate(`/analysis/${data.session_id}`);
        },
        onError: (err) => {
          setErrorMsg(err.message || 'Something went wrong during file upload.');
        },
      }
    );
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '3rem', padding: '2rem 0' }}>
      
      {/* Hero Section */}
      <ScrollAnimate animationClass="fade-in-up">
        <section style={{ textAlign: 'center', maxWidth: '800px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ display: 'inline-flex', alignSelf: 'center', alignItems: 'center', gap: '0.5rem', padding: '0.4rem 1rem', borderRadius: '20px', backgroundColor: 'var(--color-primary-hover)', color: '#ffffff', fontSize: '0.8rem', fontWeight: 600 }}>
            <Sparkles size={14} /> AI-Powered Transaction Processing
          </div>
          <h2 style={{ fontSize: '3rem', fontWeight: 900, lineHeight: 1.2, letterSpacing: '-0.02em' }}>
            De-clutter your <span style={{ color: 'var(--color-primary)' }}>bank statements</span> instantly
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '1.15rem', maxWidth: '600px', margin: '0 auto' }}>
            Upload your bank statement export files. Our pipelines clean UPI codes, classify merchants, flag recurring payments, and generate narrative spending insights.
          </p>
        </section>
      </ScrollAnimate>

      {/* Upload Zone */}
      <ScrollAnimate animationClass="zoom-in">
        <section>
          <FileUpload
            onUpload={handleUpload}
            isLoading={uploadMutation.isPending}
            error={errorMsg}
          />
        </section>
      </ScrollAnimate>

      {/* Feature Value Cards */}
      <ScrollAnimate animationClass="fade-in-up">
        <section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '2rem', maxWidth: '1000px', margin: '0 auto', width: '100%' }}>
          <div className="card card-3d" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <div style={{ color: 'var(--color-primary)' }}><Shield size={24} /></div>
            <h4 style={{ fontWeight: 700 }}>100% Secure & Private</h4>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
              Your transaction data is kept isolated within dynamic upload sessions and automatically purged within 24 hours. No cross-user persistence.
            </p>
          </div>
          
          <div className="card card-3d" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <div style={{ color: 'var(--color-success)' }}><Sparkles size={24} /></div>
            <h4 style={{ fontWeight: 700 }}>Smart UPI Cleaning</h4>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
              Strips transaction IDs, UPI codes, payment modes, and cryptic references to extract clean, recognizable merchant strings (e.g. Swiggy, Zomato, Rent).
            </p>
          </div>

          <div className="card card-3d" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <div style={{ color: 'var(--color-info)' }}><AlertCircle size={24} /></div>
            <h4 style={{ fontWeight: 700 }}>Recurring Payment Detection</h4>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
              Automatically detects regular interval transactions like subscriptions, EMIs, house rent, or SIP transfers using advanced interval clustering.
            </p>
          </div>
        </section>
      </ScrollAnimate>
    </div>
  );
}
