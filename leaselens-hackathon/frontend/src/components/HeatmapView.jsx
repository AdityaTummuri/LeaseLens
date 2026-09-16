/**
 * HeatmapView — Interactive risk heatmap and clause breakdown with full a11y support.
 *
 * Accessibility features:
 * - role="region" with descriptive aria-label on major layout sections
 * - role="meter" on the OverallRiskGauge with aria-valuenow, valuemin, valuemax, valuetext
 * - Semantic section landmarks and heading hierarchy (h2, h3, h4)
 * - Screen-reader announcements for risk distributions and count metrics
 * - High-contrast WCAG AA compliant text colors across all visual states
 * - High-contrast indicators and labels for colorblind accessibility
 */
import React from 'react';
import RiskCard from './RiskCard';

/* ── Visual and accessible color configurations ─────────────────── */
const RISK_COLORS = {
  low: {
    bg: 'bg-risk-low',
    text: 'text-risk-low',
    label: 'Standard',
    srLabel: 'Standard clauses with low variance from market baseline',
  },
  moderate: {
    bg: 'bg-risk-moderate',
    text: 'text-risk-moderate',
    label: 'Moderate Variance',
    srLabel: 'Clauses with moderate variance requiring attention',
  },
  high: {
    bg: 'bg-risk-high',
    text: 'text-risk-high',
    label: 'High Variance',
    srLabel: 'Clauses with significant variance from market baseline',
  },
};

/**
 * OverallRiskGauge — Visual and assistive meter representing aggregate lease risk.
 */
function OverallRiskGauge({ score }) {
  const percentage = Math.min(100, Math.max(0, (score / 10) * 100));
  const color =
    score <= 3
      ? 'from-risk-low to-emerald-400'
      : score <= 6
      ? 'from-risk-moderate to-amber-400'
      : 'from-risk-high to-red-400';

  const riskDescriptor =
    score <= 3 ? 'Low risk (aligned with market norms)' :
    score <= 6 ? 'Moderate risk (some clauses deviate from norms)' :
                 'Elevated risk (multiple heavy deviations from market baseline)';

  return (
    <section
      role="region"
      aria-label="Overall Risk Gauge"
      className="glass-card glow-border p-8 mb-8 animate-slide-up"
    >
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-bold text-white">Overall Risk Score</h3>
          <p className="text-sm text-gray-400 mt-1">
            Calculated via statistical variance from regional market baselines
          </p>
        </div>
        <div
          className={`text-5xl font-extrabold bg-gradient-to-r ${color} bg-clip-text text-transparent`}
          aria-hidden="true"
        >
          {score.toFixed(1)}
          <span className="text-lg text-gray-500 font-normal ml-1">/ 10</span>
        </div>
      </div>

      {/* Accessible progress meter */}
      <div
        role="meter"
        aria-label="Lease Risk Meter"
        aria-valuenow={score}
        aria-valuemin={0}
        aria-valuemax={10}
        aria-valuetext={`${score.toFixed(1)} out of 10: ${riskDescriptor}`}
        className="h-3 bg-surface rounded-full overflow-hidden"
      >
        <div
          className={`h-full bg-gradient-to-r ${color} rounded-full transition-all duration-1000 ease-out`}
          style={{ width: `${percentage}%` }}
        />
      </div>

      {/* Legend & screen reader description */}
      <div className="flex justify-between mt-4 text-xs text-gray-400 font-medium">
        <span>0 — Fully Standard</span>
        <span className="text-gray-300 font-semibold">{riskDescriptor}</span>
        <span>10 — Highly Onerous</span>
      </div>
    </section>
  );
}

/**
 * DocumentSummary — Executive summary of analyzed lease clauses.
 */
function DocumentSummary({ summary, title, totalClauses }) {
  return (
    <section
      role="region"
      aria-label="Document Summary"
      className="glass-card p-6 mb-8 animate-slide-up"
      style={{ animationDelay: '0.1s' }}
    >
      <div className="flex items-center gap-3 mb-4">
        <div className="w-8 h-8 rounded-lg bg-accent-primary/10 flex items-center justify-center">
          <span role="img" aria-hidden="true">📋</span>
        </div>
        <h3 className="text-lg font-bold text-white">{title || 'Document Analysis Summary'}</h3>
        <span
          className="ml-auto risk-badge bg-surface-elevated text-gray-300 border-white/5"
          aria-label={`Analyzed ${totalClauses} distinct lease clauses`}
        >
          {totalClauses} clauses analyzed
        </span>
      </div>
      <p className="text-gray-200 text-sm leading-relaxed">{summary}</p>
    </section>
  );
}

/**
 * RiskLegend — Color-coded key with dual visual + textual indicators for accessibility.
 */
function RiskLegend() {
  return (
    <div
      role="region"
      aria-label="Risk Severity Legend"
      className="flex flex-wrap items-center gap-4 mb-6 p-3 rounded-lg bg-surface/40 border border-white/5"
    >
      <span className="text-xs uppercase tracking-wider text-gray-400 font-semibold mr-1">
        Legend:
      </span>
      {Object.entries(RISK_COLORS).map(([level, config]) => (
        <div
          key={level}
          className="flex items-center gap-2"
          aria-label={config.srLabel}
        >
          <div className={`w-3 h-3 rounded-full ${config.bg}`} aria-hidden="true" />
          <span className="text-xs text-gray-300 font-medium">{config.label}</span>
        </div>
      ))}
    </div>
  );
}

/**
 * HeatmapView — Primary results dashboard orchestrating risk overview and clause cards.
 */
export default function HeatmapView({ analysis }) {
  const riskCounts = {
    low: analysis.risks.filter((r) => r.risk_level === 'low').length,
    moderate: analysis.risks.filter((r) => r.risk_level === 'moderate').length,
    high: analysis.risks.filter((r) => r.risk_level === 'high').length,
  };

  // Order clauses by severity: High variance first, then Moderate, then Standard
  const sortedRisks = [...analysis.risks].sort((a, b) => {
    const order = { high: 0, moderate: 1, low: 2 };
    return order[a.risk_level] - order[b.risk_level];
  });

  return (
    <main
      role="region"
      aria-label="LeaseLens Analysis Heatmap Dashboard"
      className="animate-fade-in"
    >
      <OverallRiskGauge score={analysis.overall_risk_score} />

      <DocumentSummary
        summary={analysis.document_summary}
        title={analysis.document_title}
        totalClauses={analysis.total_clauses_analyzed}
      />

      {/* ── Risk Distribution Metrics ─────────────────────────── */}
      <section
        role="region"
        aria-label="Risk Distribution Counts"
        className="flex flex-wrap gap-3 mb-6"
      >
        {riskCounts.high > 0 && (
          <div
            className="risk-badge-high"
            role="status"
            aria-label={`${riskCounts.high} High Variance clauses found`}
          >
            <span aria-hidden="true">⚠️ </span>
            {riskCounts.high} High Variance
          </div>
        )}
        {riskCounts.moderate > 0 && (
          <div
            className="risk-badge-moderate"
            role="status"
            aria-label={`${riskCounts.moderate} Moderate Variance clauses found`}
          >
            <span aria-hidden="true">⚡ </span>
            {riskCounts.moderate} Moderate Variance
          </div>
        )}
        {riskCounts.low > 0 && (
          <div
            className="risk-badge-low"
            role="status"
            aria-label={`${riskCounts.low} Standard baseline clauses found`}
          >
            <span aria-hidden="true">✓ </span>
            {riskCounts.low} Standard
          </div>
        )}
      </section>

      <RiskLegend />

      {/* ── Clause Breakdown Grid ─────────────────────────────── */}
      <section
        role="region"
        aria-label="Detailed Clause Variance Cards"
        className="grid gap-4 md:grid-cols-2"
      >
        {sortedRisks.map((risk, index) => (
          <RiskCard key={`${risk.category}-${index}`} risk={risk} index={index} />
        ))}
      </section>

      {/* ── Statutory Disclaimer Footer Landmark ─────────────── */}
      <footer
        role="contentinfo"
        aria-label="Statutory UPL Guardrail Disclaimer"
        className="mt-8 p-5 rounded-xl bg-surface-card/50 border border-white/5"
      >
        <p className="text-xs text-gray-400 leading-relaxed text-center">
          {analysis.disclaimer}
        </p>
      </footer>
    </main>
  );
}
