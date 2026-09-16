import React, { useState } from 'react';

const RISK_STYLES = {
  low: {
    border: 'border-risk-low/20',
    glow: 'hover:shadow-risk-low/5',
    badge: 'risk-badge-low',
    indicator: 'bg-risk-low',
    label: 'Standard',
  },
  moderate: {
    border: 'border-risk-moderate/20',
    glow: 'hover:shadow-risk-moderate/5',
    badge: 'risk-badge-moderate',
    indicator: 'bg-risk-moderate',
    label: 'Moderate Variance',
  },
  high: {
    border: 'border-risk-high/20',
    glow: 'hover:shadow-risk-high/5',
    badge: 'risk-badge-high',
    indicator: 'bg-risk-high',
    label: 'High Variance',
  },
};

const CATEGORY_ICONS = {
  'Security Deposit': '🏦',
  'Lock-in Period': '🔒',
  'Notice Period': '📢',
  'Maintenance Liability': '🔧',
  'Rent Escalation': '📈',
  'Subletting': '🏠',
  'Termination': '🚪',
  'Painting & Restoration Charges': '🎨',
  'Utilities & Common Area': '💡',
  'Other': '📌',
};

export default function RiskCard({ risk, index }) {
  const [expanded, setExpanded] = useState(false);
  const style = RISK_STYLES[risk.risk_level] || RISK_STYLES.low;
  const icon = CATEGORY_ICONS[risk.category] || '📌';

  return (
    <div
      id={`risk-card-${index}`}
      className={`glass-card border ${style.border} ${style.glow} p-5 
                  transition-all duration-300 hover:shadow-xl animate-slide-up
                  cursor-pointer`}
      style={{ animationDelay: `${0.05 * index}s` }}
      onClick={() => setExpanded(!expanded)}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-3">
          <span className="text-2xl">{icon}</span>
          <div>
            <h4 className="text-white font-semibold text-sm">{risk.category}</h4>
            <div className={style.badge}>{style.label}</div>
          </div>
        </div>

        {risk.deviation_percentage != null && (
          <div className="text-right">
            <span className={`text-lg font-bold ${
              risk.risk_level === 'low' ? 'text-risk-low' :
              risk.risk_level === 'moderate' ? 'text-risk-moderate' : 'text-risk-high'
            }`}>
              {risk.deviation_percentage > 0 ? '+' : ''}{risk.deviation_percentage}%
            </span>
            <p className="text-[10px] text-gray-600 uppercase tracking-wider">deviation</p>
          </div>
        )}
      </div>

      {/* Market Standard */}
      <div className="mb-3 p-3 rounded-lg bg-surface/60">
        <p className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold mb-1">
          Market Standard
        </p>
        <p className="text-xs text-gray-300">{risk.market_standard}</p>
      </div>

      {/* Educational Note */}
      <p className="text-xs text-gray-400 leading-relaxed mb-2">
        {risk.educational_note}
      </p>

      {/* Expandable Extracted Text */}
      <button
        className="text-[10px] text-accent-primary hover:text-accent-secondary 
                   font-medium uppercase tracking-wider transition-colors"
        onClick={(e) => {
          e.stopPropagation();
          setExpanded(!expanded);
        }}
      >
        {expanded ? '▾ Hide extracted text' : '▸ Show extracted text'}
      </button>

      {expanded && (
        <div className="mt-3 p-3 rounded-lg bg-surface border border-white/5 animate-fade-in">
          <p className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold mb-2">
            Verbatim Extracted Clause
          </p>
          <p className="text-xs text-gray-300 font-mono leading-relaxed whitespace-pre-wrap">
            {risk.extracted_text}
          </p>
        </div>
      )}
    </div>
  );
}
