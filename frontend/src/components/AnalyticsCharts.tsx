import { useState, useEffect } from 'react';

interface CategoryData {
  category: string;
  amount: number;
}

interface AnalyticsChartsProps {
  topCategories: CategoryData[];
  totalSpend: number;
}

// Design-approved category color palette (Gradients & texts)
const CATEGORY_COLORS: Record<string, { start: string; end: string; text: string }> = {
  Food: { start: '#10b981', end: '#059669', text: '#10b981' },         // emerald
  Travel: { start: '#fbbf24', end: '#d97706', text: '#fbbf24' },       // amber/gold
  Shopping: { start: '#8b5cf6', end: '#6d28d9', text: '#a78bfa' },     // violet
  Bills: { start: '#f43f5e', end: '#e11d48', text: '#f43f5e' },       // rose/red
  EMI: { start: '#6366f1', end: '#4f46e5', text: '#818cf8' },         // indigo
  Subscriptions: { start: '#ec4899', end: '#db2777', text: '#f472b6' }, // pink
  Salary: { start: '#34d399', end: '#059669', text: '#34d399' },       // light emerald
  Rent: { start: '#f97316', end: '#ea580c', text: '#fb923c' },         // orange
  Investments: { start: '#06b6d4', end: '#0891b2', text: '#22d3ee' },   // cyan
  Other: { start: '#64748b', end: '#475569', text: '#94a3b8' },       // slate
};

const FALLBACK_PALETTE = [
  { start: '#38bdf8', end: '#0284c7', text: '#38bdf8' }, // sky
  { start: '#f472b6', end: '#be185d', text: '#f472b6' }, // pink
  { start: '#fb7185', end: '#e11d48', text: '#fb7185' }, // rose
  { start: '#fb923c', end: '#ea580c', text: '#fb923c' }, // orange
  { start: '#2dd4bf', end: '#0f766e', text: '#2dd4bf' }, // teal
  { start: '#a78bfa', end: '#6d28d9', text: '#a78bfa' }, // violet
];

const getCategoryColor = (category: string, index: number) => {
  return CATEGORY_COLORS[category] || FALLBACK_PALETTE[index % FALLBACK_PALETTE.length];
};

export function AnalyticsCharts({ topCategories, totalSpend }: AnalyticsChartsProps) {
  const [hoveredSlice, setHoveredSlice] = useState<number | null>(null);
  const [animateBars, setAnimateBars] = useState(false);

  // Group small categories under "Other" if they represent < 2% of total spends
  const processedCategories = (() => {
    if (!topCategories || topCategories.length === 0) return [];
    
    // Sort descending
    const sorted = [...topCategories].sort((a, b) => b.amount - a.amount);
    
    if (totalSpend === 0) return sorted;

    const threshold = totalSpend * 0.02; // 2% threshold
    const mainCategories: CategoryData[] = [];
    let otherSum = 0;

    sorted.forEach(cat => {
      if (cat.amount < threshold && cat.category !== 'Salary') {
        otherSum += cat.amount;
      } else {
        mainCategories.push(cat);
      }
    });

    if (otherSum > 0) {
      // Find if "Other" already exists
      const existingOtherIdx = mainCategories.findIndex(c => c.category === 'Other');
      if (existingOtherIdx !== -1) {
        mainCategories[existingOtherIdx].amount += otherSum;
      } else {
        mainCategories.push({ category: 'Other', amount: otherSum });
      }
    }

    // Re-sort in case "Other" accumulated sum exceeds main categories
    return mainCategories.sort((a, b) => b.amount - a.amount);
  })();

  // Filter out 'Salary' and credits from spending breakdowns if needed,
  // but let's assume we display all non-zero debit spends.
  const spendCategories = processedCategories.filter(c => c.amount > 0 && c.category !== 'Salary');
  const totalSpendAdjusted = spendCategories.reduce((sum, item) => sum + item.amount, 0);

  // Trigger bar and stroke drawing transition on mount
  useEffect(() => {
    const timer = setTimeout(() => setAnimateBars(true), 150);
    return () => clearTimeout(timer);
  }, []);

  // SVG Donut Calculations
  const radius = 70;
  const strokeWidthDefault = 16;
  const strokeWidthHovered = 22;
  const centerCoord = 100;
  const circumference = 2 * Math.PI * radius; // ~439.82

  let accumulatedOffset = 0;

  return (
    <div className="analytics-dashboard-grid">
      
      {/* 1. Donut Chart Card */}
      <div className="card card-3d" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', minHeight: '340px' }}>
        <h4 style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--text-primary)' }}>Spending Share</h4>
        
        {spendCategories.length === 0 ? (
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            No debit transactions available for visual analysis.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', flex: 1, justifyContent: 'center' }}>
            <div className="donut-svg-container">
              <svg width="200" height="200" viewBox="0 0 200 200" style={{ transform: 'rotate(-90deg)' }}>
                {/* SVG Definitions for Gradients */}
                <defs>
                  {spendCategories.map((cat, idx) => {
                    const colors = getCategoryColor(cat.category, idx);
                    return (
                      <linearGradient id={`grad-${idx}`} key={idx} x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stopColor={colors.start} />
                        <stop offset="100%" stopColor={colors.end} />
                      </linearGradient>
                    );
                  })}
                </defs>

                {spendCategories.map((cat, idx) => {
                  const percentage = totalSpendAdjusted > 0 ? cat.amount / totalSpendAdjusted : 0;
                  const strokeLength = percentage * circumference;
                  const dashOffset = accumulatedOffset;
                  accumulatedOffset -= strokeLength;

                  const isHovered = hoveredSlice === idx;

                  return (
                    <circle
                      key={idx}
                      className="donut-segment"
                      cx={centerCoord}
                      cy={centerCoord}
                      r={radius}
                      fill="transparent"
                      stroke={`url(#grad-${idx})`}
                      strokeWidth={isHovered ? strokeWidthHovered : strokeWidthDefault}
                      strokeDasharray={`${strokeLength} ${circumference}`}
                      strokeDashoffset={dashOffset}
                      onMouseEnter={() => setHoveredSlice(idx)}
                      onMouseLeave={() => setHoveredSlice(null)}
                      style={{
                        animation: 'drawCircle 1s cubic-bezier(0.25, 1, 0.5, 1) forwards',
                        transition: 'stroke-width 0.25s ease-out, filter 0.25s ease-out',
                      }}
                    />
                  );
                })}
              </svg>

              {/* Central text readouts */}
              <div className="donut-center-text">
                {hoveredSlice !== null ? (
                  <>
                    <span className="donut-center-title">{spendCategories[hoveredSlice].category}</span>
                    <span className="donut-center-value">
                      ₹{spendCategories[hoveredSlice].amount.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                    </span>
                    <span className="donut-center-percent" style={{ color: getCategoryColor(spendCategories[hoveredSlice].category, hoveredSlice).text }}>
                      {((spendCategories[hoveredSlice].amount / totalSpendAdjusted) * 100).toFixed(1)}%
                    </span>
                  </>
                ) : (
                  <>
                    <span className="donut-center-title">Total Spend</span>
                    <span className="donut-center-value">
                      ₹{totalSpendAdjusted.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                    </span>
                    <span className="donut-center-percent" style={{ color: 'var(--color-primary)' }}>
                      100%
                    </span>
                  </>
                )}
              </div>
            </div>

            {/* Custom Interactive Badges */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.6rem', justifyContent: 'center' }}>
              {spendCategories.map((cat, idx) => {
                const colors = getCategoryColor(cat.category, idx);
                const isHovered = hoveredSlice === idx;
                return (
                  <div
                    key={idx}
                    onMouseEnter={() => setHoveredSlice(idx)}
                    onMouseLeave={() => setHoveredSlice(null)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.4rem',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      padding: '0.3rem 0.6rem',
                      borderRadius: '12px',
                      border: `1px solid ${isHovered ? colors.text : 'var(--border-color)'}`,
                      backgroundColor: isHovered ? `${colors.start}15` : 'transparent',
                      color: isHovered ? colors.text : 'var(--text-secondary)',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                    }}
                  >
                    <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', background: `linear-gradient(135deg, ${colors.start}, ${colors.end})` }} />
                    <span>{cat.category}</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* 2. Bar Chart Card */}
      <div className="card card-3d" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', minHeight: '340px' }}>
        <h4 style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--text-primary)' }}>Category Breakdown</h4>
        
        {spendCategories.length === 0 ? (
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            No debit transactions available for visual analysis.
          </div>
        ) : (
          <div className="bar-chart-container" style={{ flex: 1, justifyContent: 'center' }}>
            {spendCategories.slice(0, 6).map((cat, idx) => {
              const percentage = totalSpendAdjusted > 0 ? (cat.amount / totalSpendAdjusted) * 100 : 0;
              const colors = getCategoryColor(cat.category, idx);
              const isHovered = hoveredSlice === idx;

              return (
                <div
                  key={idx}
                  className="bar-chart-row"
                  onMouseEnter={() => setHoveredSlice(idx)}
                  onMouseLeave={() => setHoveredSlice(null)}
                  style={{
                    opacity: isHovered || hoveredSlice === null ? 1 : 0.6,
                    transform: isHovered ? 'scale(1.01) translateX(4px)' : 'none',
                    transition: 'all 0.25s ease',
                  }}
                >
                  <span className="bar-chart-label" title={cat.category}>{cat.category}</span>
                  <div className="bar-chart-track">
                    <div
                      className="bar-chart-fill"
                      style={{
                        width: animateBars ? `${percentage}%` : '0%',
                        background: `linear-gradient(90deg, ${colors.start}, ${colors.end})`,
                        boxShadow: isHovered ? `0 0 10px ${colors.start}50` : 'none',
                      }}
                    />
                  </div>
                  <span className="bar-chart-value">
                    ₹{cat.amount.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>

    </div>
  );
}
