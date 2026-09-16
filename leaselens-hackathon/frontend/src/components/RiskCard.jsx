/**
 * RiskCard — Expandable clause risk card with full a11y support.
 *
 * Accessibility features:
 * - role="article" for semantic landmark identification
 * - aria-label with risk level and category for screen readers
 * - aria-expanded/aria-controls on the toggle button
 * - Keyboard operability: Enter/Space to expand, focus-visible ring
 * - WCAG AA contrast-compliant text colors on dark backgrounds
 * - tabIndex={0} on the card for sequential keyboard navigation
 */
import React, { useState, useCallback } from 'react';

/* ── Risk-level visual style mappings ──────────────────────────── */
const RISK_STYLES = {
  low: {
    border: 'border-risk-low/20',
    glow: 'hover:shadow-risk-low/5',
    badge: 'risk-badge-low',
    indicator: 'bg-risk-low',
    label: 'Standard',
    srLabel: 'low risk',
  },
  moderate: {
    border: 'border-risk-moderate/20',
    glow: 'hover:shadow-risk-moderate/5',
    badge: 'risk-badge-moderate',
    indicator: 'bg-risk-moderate',
    label: 'Moderate Variance',
    srLabel: 'moderate risk',
  },
  high: {
    border: 'border-risk-high/20',
    glow: 'hover:shadow-risk-high/5',
    badge: 'risk-badge-high',
    indicator: 'bg-risk-high',
    label: 'High Variance',
    srLabel: 'high risk',
  },
};

/* ── Category icon lookup ──────────────────────────────────────── */
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

  /* Unique IDs for aria-controls linkage */
  const cardId = `risk-card-${index}`;
  const detailId = `risk-detail-${index}`;

  /* Keyboard handler: Enter/Space toggle expansion */
  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      setExpanded((prev) => !prev);
    }
  }, []);

  /* Toggle handler for the explicit button */
  const handleToggle = useCallback((e) => {
    e.stopPropagation();
    setExpanded((prev) => !prev);
  }, []);

  return (
    <article
      id={cardId}
      role="article"
      aria-label={`${risk.category} — ${style.srLabel}`}
      tabIndex={0}
      onKeyDown={handleKeyDown}
      onClick={() => setExpanded((prev) => !prev)}
      className={`glass-card border ${style.border} ${style.glow} p-5
                  transition-all duration-300 hover:shadow-xl animate-slide-up
                  cursor-pointer focus:outline-none focus-visible:ring-2
                  focus-visible:ring-accent-primary/60 focus-visible:ring-offset-2
                  focus-visible:ring-offset-surface`}
      style={{ animationDelay: `${0.05 * index}s` }}
    >
      {/* ── Card Header ──────────────────────────────────────── */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-3">
          <span className="text-2xl" role="img" aria-hidden="true">{icon}</span>
          <div>
            <h4 className="text-white font-semibold text-sm">{risk.category}</h4>
            <span className={style.badge} aria-label={`Risk level: ${style.label}`}>
              {style.label}
            </span>
          </div>
        </div>

        {risk.deviation_percentage != null && (
          <div className="text-right" aria-label={`Deviation: ${risk.deviation_percentage}%`}>
            <span
              className={`text-lg font-bold ${
                risk.risk_level === 'low' ? 'text-risk-low' :
                risk.risk_level === 'moderate' ? 'text-risk-moderate' : 'text-risk-high'
              }`}
            >
              {risk.deviation_percentage > 0 ? '+' : ''}{risk.deviation_percentage}%
            </span>
            <p className="text-[10px] text-gray-500 uppercase tracking-wider">deviation</p>
          </div>
        )}
      </div>

      {/* ── Market Standard Baseline ─────────────────────────── */}
      <div className="mb-3 p-3 rounded-lg bg-surface/60" role="note" aria-label="Market standard comparison">
        <p className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold mb-1">
          Market Standard
        </p>
        <p className="text-xs text-gray-300">{risk.market_standard}</p>
      </div>

      {/* ── Educational Note (never advisory) ────────────────── */}
      <p className="text-xs text-gray-400 leading-relaxed mb-2">
        {risk.educational_note}
      </p>

      {/* ── Expand/Collapse Toggle ───────────────────────────── */}
      <button
        type="button"
        aria-expanded={expanded}
        aria-controls={detailId}
        aria-label={expanded ? `Hide extracted text for ${risk.category}` : `Show extracted text for ${risk.category}`}
        className="text-[10px] text-accent-primary hover:text-accent-secondary
                   font-medium uppercase tracking-wider transition-colors
                   focus:outline-none focus-visible:underline"
        onClick={handleToggle}
      >
        {expanded ? '▾ Hide extracted text' : '▸ Show extracted text'}
      </button>

      {/* ── Verbatim Clause Extract (collapsed by default) ──── */}
      {expanded && (
        <div
          id={detailId}
          role="region"
          aria-label={`Verbatim clause text for ${risk.category}`}
          className="mt-3 p-3 rounded-lg bg-surface border border-white/5 animate-fade-in"
        >
          <p className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold mb-2">
            Verbatim Extracted Clause
          </p>
          <p className="text-xs text-gray-300 font-mono leading-relaxed whitespace-pre-wrap">
            {risk.extracted_text}
          </p>
        </div>
      )}
    </article>
  );
}
