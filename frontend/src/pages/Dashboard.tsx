import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  useSessionStatus, 
  useTransactions, 
  useAnalytics, 
  useInsights, 
  useRecurringPayments, 
  useOverrideCategory,
  useDeleteSession 
} from '../api/hooks';
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Percent, 
  FileText, 
  Search, 
  Filter, 
  RefreshCw, 
  AlertCircle, 
  CheckCircle,
  Trash2,
  Calendar,
  AlertTriangle
} from 'lucide-react';
import { AnalyticsCharts } from '../components/AnalyticsCharts';
import { ScrollAnimate } from '../components/ScrollAnimate';
import { ReportDownload } from '../components/ReportDownload';

export function Dashboard() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();

  // Search & Filter state
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [page, setPage] = useState(1);
  const limit = 50;

  // React Query Hooks
  const { data: session, isLoading: sessionLoading, error: sessionError } = useSessionStatus(sessionId || null);
  const { data: txnData, isLoading: txnsLoading } = useTransactions(sessionId || null, {
    page,
    limit,
    category: categoryFilter,
    search
  });
  const { data: analytics } = useAnalytics(sessionId || null);
  const { data: insights } = useInsights(sessionId || null);
  const { data: recurring } = useRecurringPayments(sessionId || null);

  const overrideMutation = useOverrideCategory();
  const deleteMutation = useDeleteSession();

  const handleClear = () => {
    if (sessionId) {
      deleteMutation.mutate(sessionId, {
        onSettled: () => {
          navigate('/');
        }
      });
    } else {
      navigate('/');
    }
  };

  const handleCategoryChange = (txnId: string, newCategory: string) => {
    if (sessionId) {
      overrideMutation.mutate({ sessionId, transactionId: txnId, category: newCategory });
    }
  };

  // Loading state
  if (sessionLoading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '50vh', gap: '1rem' }}>
        <RefreshCw className="spin" size={48} style={{ color: 'var(--color-primary)' }} />
        <p style={{ color: 'var(--text-secondary)' }}>Loading session details...</p>
      </div>
    );
  }

  // Error/Missing Session state
  if (sessionError || !session) {
    return (
      <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem', padding: '3rem', maxWidth: '600px', margin: '2rem auto', textAlign: 'center' }}>
        <AlertTriangle size={48} style={{ color: 'var(--color-danger)' }} />
        <h3 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Analysis Session Not Found</h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
          This session may have expired (24-hour retention policy) or the URL is invalid.
        </p>
        <button onClick={() => navigate('/')} className="btn btn-primary" style={{ marginTop: '1rem' }}>
          Return to Upload
        </button>
      </div>
    );
  }

  // Pipeline In-Progress / Processing state
  if (session.status !== 'ready' && session.status !== 'failed') {
    return (
      <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '2rem', padding: '4rem 2rem', maxWidth: '600px', margin: '2rem auto', textAlign: 'center' }}>
        <RefreshCw className="spin" size={48} style={{ color: 'var(--color-warning)' }} />
        <div>
          <h3 style={{ fontSize: '1.25rem', fontWeight: 700, textTransform: 'capitalize' }}>Status: Processing Statement</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '0.5rem' }}>
            We are cleaning UPI strings, mapping categories, and parsing raw details. This takes a few seconds...
          </p>
        </div>
        
        {/* Step indicator */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', width: '100%', maxWidth: '320px', textAlign: 'left' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', color: session.status === 'pending' ? 'var(--color-warning)' : 'var(--color-success)' }}>
            <span style={{ display: 'inline-block', width: 6, height: 6, borderRadius: '50%', backgroundColor: 'currentColor' }}></span>
            <span>1. File Ingestion ({session.status === 'pending' ? 'In Progress' : 'Completed'})</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', color: session.status === 'parsing' ? 'var(--color-warning)' : (session.status === 'pending' ? 'var(--text-muted)' : 'var(--color-success)') }}>
            <span style={{ display: 'inline-block', width: 6, height: 6, borderRadius: '50%', backgroundColor: 'currentColor' }}></span>
            <span>2. Clean & Normalize Descriptions</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', color: session.status === 'processing' ? 'var(--color-warning)' : 'var(--text-muted)' }}>
            <span style={{ display: 'inline-block', width: 6, height: 6, borderRadius: '50%', backgroundColor: 'currentColor' }}></span>
            <span>3. Hybrid Categorization & Metrics</span>
          </div>
        </div>
      </div>
    );
  }

  // Processing Failed state
  if (session.status === 'failed') {
    return (
      <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem', padding: '3rem', maxWidth: '600px', margin: '2rem auto', textAlign: 'center', borderColor: 'var(--color-danger)' }}>
        <AlertTriangle size={48} style={{ color: 'var(--color-danger)' }} />
        <h3 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Processing Failed</h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
          {session.error_message || 'An error occurred while parsing the bank statement export.'}
        </p>
        <button onClick={handleClear} className="btn btn-secondary" style={{ marginTop: '1rem' }}>
          Try Another File
        </button>
      </div>
    );
  }

  // Ready State: Render Full Dashboard
  const metrics = analytics?.metrics || {
    total_income: 0,
    total_spend: 0,
    savings: 0,
    savings_rate: 0
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      
      {/* Session Metadata Panel */}
      <ScrollAnimate animationClass="zoom-in">
        <div className="card card-3d" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderColor: 'var(--color-primary)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{ padding: '0.75rem', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--bg-surface)', color: 'var(--color-primary)' }}>
              <FileText size={24} />
            </div>
            <div>
              <h4 style={{ fontWeight: 600 }}>{session.filename}</h4>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span>Session ID:</span>
                <code style={{ backgroundColor: 'var(--bg-surface)', padding: '0.1rem 0.3rem', borderRadius: '4px' }}>{session.id}</code>
                <span>• Expires in 24h</span>
              </p>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--color-success)' }}>
              <CheckCircle size={18} />
              <span style={{ fontSize: '0.9rem', fontWeight: 600 }}>Analysis Completed</span>
            </div>
            <ReportDownload sessionId={sessionId!} filename={session.filename} />
            <button 
              onClick={handleClear} 
              disabled={deleteMutation.isPending} 
              className="btn btn-secondary" 
              style={{ padding: '0.5rem 1rem', color: 'var(--color-danger)', gap: '0.25rem' }}
            >
              <Trash2 size={16} />
              <span>{deleteMutation.isPending ? 'Purging...' : 'Delete Session'}</span>
            </button>
          </div>
        </div>
      </ScrollAnimate>

      {/* Analytics Summary Cards */}
      <ScrollAnimate animationClass="fade-in-up">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.5rem' }}>
          
          <div className="card card-3d" style={{ borderLeft: '4px solid var(--color-success)', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)' }}>
              <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>Total Income</span>
              <TrendingUp size={18} style={{ color: 'var(--color-success)' }} />
            </div>
            <h2 style={{ fontWeight: 800 }}>₹{metrics.total_income.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</h2>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>From credits inside statement</span>
          </div>

          <div className="card card-3d" style={{ borderLeft: '4px solid var(--color-danger)', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)' }}>
              <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>Total Spends</span>
              <TrendingDown size={18} style={{ color: 'var(--color-danger)' }} />
            </div>
            <h2 style={{ fontWeight: 800 }}>₹{metrics.total_spend.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</h2>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>From withdrawals/debits</span>
          </div>

          <div className="card card-3d" style={{ borderLeft: '4px solid var(--color-primary)', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)' }}>
              <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>Net Savings</span>
              <DollarSign size={18} style={{ color: 'var(--color-primary)' }} />
            </div>
            <h2 style={{ fontWeight: 800 }}>₹{metrics.savings.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</h2>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Income minus spend total</span>
          </div>

          <div className="card card-3d" style={{ borderLeft: '4px solid var(--color-info)', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)' }}>
              <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>Savings Rate</span>
              <Percent size={18} style={{ color: 'var(--color-info)' }} />
            </div>
            <h2 style={{ fontWeight: 800 }}>{metrics.savings_rate.toFixed(1)}%</h2>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Percent of income retained</span>
          </div>

        </div>
      </ScrollAnimate>

      {/* Visualizations Section */}
      <ScrollAnimate animationClass="fade-in-up">
        <AnalyticsCharts 
          topCategories={analytics?.top_categories || []} 
          totalSpend={metrics.total_spend} 
        />
      </ScrollAnimate>

      {/* Main Panels Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '3fr 1fr', gap: '2rem' }}>
        
        {/* Left Side: Transactions List */}
        <ScrollAnimate animationClass="fade-in-up" style={{ display: 'flex', flexDirection: 'column' }}>
          <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem', height: '100%' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
            <h3 style={{ fontWeight: 700 }}>Transactions List</h3>
            
            <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
              {/* Search Bar */}
              <div className="search-container">
                <Search size={16} style={{ color: 'var(--text-secondary)' }} />
                <input 
                  type="text" 
                  placeholder="Search transactions..." 
                  value={search}
                  onChange={e => { setSearch(e.target.value); setPage(1); }}
                  style={{ border: 'none', background: 'transparent', outline: 'none', padding: '0.5rem 0', color: 'var(--text-primary)', fontSize: '0.85rem', width: '150px' }} 
                />
              </div>

              {/* Category Filter */}
              <div className="select-container">
                <Filter size={16} style={{ color: 'var(--text-secondary)' }} />
                <select 
                  value={categoryFilter}
                  onChange={e => { setCategoryFilter(e.target.value); setPage(1); }}
                  style={{ border: 'none', background: 'transparent', outline: 'none', padding: '0.5rem 0', color: 'var(--text-primary)', fontSize: '0.85rem', cursor: 'pointer' }}
                >
                  <option value="all">All Categories</option>
                  <option value="Food">Food</option>
                  <option value="Travel">Travel</option>
                  <option value="Shopping">Shopping</option>
                  <option value="Bills">Bills</option>
                  <option value="EMI">EMI</option>
                  <option value="Subscriptions">Subscriptions</option>
                  <option value="Salary">Salary</option>
                  <option value="Rent">Rent</option>
                  <option value="Investments">Investments</option>
                  <option value="Other">Other</option>
                </select>
              </div>
            </div>
          </div>

          {/* Transactions Table */}
          <div style={{ overflowX: 'auto' }}>
            {txnsLoading ? (
              <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
                <RefreshCw className="spin" size={24} style={{ display: 'inline', marginRight: '0.5rem' }} />
                Loading transactions...
              </div>
            ) : !txnData || txnData.transactions.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                No matching transactions found
              </div>
            ) : (
              <>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--border-color)', textAlign: 'left', color: 'var(--text-secondary)' }}>
                      <th style={{ padding: '0.75rem 0.5rem' }}>Date</th>
                      <th style={{ padding: '0.75rem 0.5rem' }}>Description (Raw)</th>
                      <th style={{ padding: '0.75rem 0.5rem' }}>Normalized Merchant</th>
                      <th style={{ padding: '0.75rem 0.5rem' }}>Category</th>
                      <th style={{ padding: '0.75rem 0.5rem', textAlign: 'right' }}>Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    {txnData.transactions.map(t => (
                      <tr key={t.id} style={{ borderBottom: '1px solid var(--border-color)', transition: 'background 0.1s' }} className="table-row">
                        <td style={{ padding: '0.75rem 0.5rem', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>{t.date}</td>
                        <td style={{ padding: '0.75rem 0.5rem', maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: 'var(--text-muted)' }} title={t.description_raw}>
                          {t.description_raw}
                        </td>
                        <td style={{ padding: '0.75rem 0.5rem', fontWeight: 600 }}>{t.description_clean || 'Unrecognized'}</td>
                        <td style={{ padding: '0.75rem 0.5rem' }}>
                          <select
                            value={t.category}
                            onChange={(e) => handleCategoryChange(t.id, e.target.value)}
                            style={{ 
                              padding: '0.2rem 0.5rem', 
                              borderRadius: '12px', 
                              fontSize: '0.75rem', 
                              fontWeight: 600,
                              backgroundColor: t.category === 'Salary' ? 'var(--color-success-bg)' : 'var(--bg-surface)',
                              color: t.category === 'Salary' ? 'var(--color-success)' : 'var(--text-secondary)',
                              border: 'none',
                              outline: 'none',
                              cursor: 'pointer'
                            }}
                          >
                            <option value="Food">Food</option>
                            <option value="Travel">Travel</option>
                            <option value="Shopping">Shopping</option>
                            <option value="Bills">Bills</option>
                            <option value="EMI">EMI</option>
                            <option value="Subscriptions">Subscriptions</option>
                            <option value="Salary">Salary</option>
                            <option value="Rent">Rent</option>
                            <option value="Investments">Investments</option>
                            <option value="Other">Other</option>
                          </select>
                        </td>
                        <td style={{ 
                          padding: '0.75rem 0.5rem', 
                          textAlign: 'right', 
                          fontWeight: 700,
                          color: t.type === 'credit' ? 'var(--color-success)' : 'var(--text-primary)'
                        }}>
                          {t.type === 'credit' ? '+' : ''}₹{t.amount.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                {/* Pagination Controls */}
                {txnData.total_count > limit && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1.5rem', borderTop: '1px solid var(--border-color)', paddingTop: '1rem' }}>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                      Showing {((page - 1) * limit) + 1} - {Math.min(page * limit, txnData.total_count)} of {txnData.total_count} transactions
                    </span>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <button 
                        onClick={() => setPage(p => Math.max(p - 1, 1))} 
                        disabled={page === 1}
                        className="btn btn-secondary"
                        style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }}
                      >
                        Previous
                      </button>
                      <button 
                        onClick={() => setPage(p => Math.min(p + 1, Math.ceil(txnData.total_count / limit)))} 
                        disabled={page >= Math.ceil(txnData.total_count / limit)}
                        className="btn btn-secondary"
                        style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }}
                      >
                        Next
                      </button>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </ScrollAnimate>

        {/* Right Side: Insights & Recurring */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          
          {/* Insights Panel */}
          <ScrollAnimate animationClass="slide-in-right">
            <div className="card card-3d" style={{ display: 'flex', flexDirection: 'column', gap: '1rem', height: '100%' }}>
              <h4 style={{ fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <AlertCircle size={18} style={{ color: 'var(--color-warning)' }} /> Behavioral Insights
              </h4>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {(!insights || insights.length === 0) ? (
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', padding: '1rem 0' }}>
                    No insights generated yet.
                  </div>
                ) : (
                  insights.map((insight, idx) => {
                    // Determine colors by index/content for rich aesthetics
                    const borderColors = ['var(--color-warning)', 'var(--color-info)', 'var(--color-success)'];
                    const borderColor = borderColors[idx % borderColors.length];
                    
                    return (
                      <div 
                        key={idx} 
                        style={{ 
                          padding: '0.75rem', 
                          borderRadius: 'var(--radius-sm)', 
                          backgroundColor: 'var(--bg-surface)', 
                          borderLeft: `3px solid ${borderColor}`, 
                          fontSize: '0.85rem',
                          lineHeight: 1.4
                        }}
                      >
                        {insight}
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </ScrollAnimate>

          {/* Recurring Panel */}
          <ScrollAnimate animationClass="slide-in-right">
            <div className="card card-3d" style={{ display: 'flex', flexDirection: 'column', gap: '1rem', height: '100%' }}>
              <h4 style={{ fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Calendar size={18} style={{ color: 'var(--color-info)' }} /> Recurring Payments
              </h4>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {(!recurring || recurring.length === 0) ? (
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', padding: '1rem 0' }}>
                    No recurring payments detected.
                  </div>
                ) : (
                  recurring.map(g => (
                    <div 
                      key={g.id} 
                      style={{ 
                        display: 'flex', 
                        justifyContent: 'space-between', 
                        alignItems: 'center', 
                        padding: '0.5rem 0', 
                        borderBottom: '1px solid var(--border-color)' 
                      }}
                    >
                      <div>
                        <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>{g.label}</span>
                        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'capitalize' }}>
                          {g.frequency} • {g.category}
                        </p>
                      </div>
                      <span style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--color-danger)' }}>
                        ₹{g.typical_amount.toLocaleString('en-IN')}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>
          </ScrollAnimate>

        </div>

      </div>

    </div>
  );
}
