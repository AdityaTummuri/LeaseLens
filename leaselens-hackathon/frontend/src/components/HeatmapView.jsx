import React from 'react';
import RiskCard from './RiskCard';

const RISK_COLORS = {
  low: { bg: 'bg-risk-low', text: 'text-risk-low', label: 'Standard' },
  moderate: { bg: 'bg-risk-moderate', text: 'text-risk-moderate', label: 'Moderate Variance' },
  high: { bg: 'bg-risk-high', text: 'text-risk-high', label: 'High Variance' },
};

function OverallRiskGauge({ score }) {
  const percentage = (score / 10) * 100;
  const color =
    score <= 3 ? 'from-risk-low to-emerald-400' :
    score <= 6 ? 'from-risk-moderate to-amber-400' :
                 'from-risk-high to-red-400';

  return (
    <div className="glass-card glow-border p-8 mb-8 animate-slide-up">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-bold text-white">Overall Risk Score</h3>
          <p className="text-sm text-gray-400 mt-1">
            Based on statistical deviation from market baselines
          </p>
        </div>
        <div className={`text-5xl font-extrabold bg-gradient-to-r ${color} bg-clip-text text-transparent`}>
          {score.toFixed(1)}
          <span className="text-lg text-gray-500 font-normal ml-1">/ 10</span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="h-3 bg-surface rounded-full overflow-hidden">
        <div
          className={`h-full bg-gradient-to-r ${color} rounded-full transition-all duration-1000 ease-out`}
          style={{ width: `${percentage}%` }}
        />
      </div>

      {/* Legend */}
      <div className="flex justify-between mt-4 text-xs text-gray-500">
        <span>0 — Fully Standard</span>
        <span>10 — Highly Onerous</span>
      </div>
    </div>
  );
}

function DocumentSummary({ summary, title, totalClauses }) {
  return (
    <div className="glass-card p-6 mb-8 animate-slide-up" style={{ animationDelay: '0.1s' }}>
      <div className="flex items-center gap-3 mb-4">
        <div className="w-8 h-8 rounded-lg bg-accent-primary/10 flex items-center justify-center">
          <span>📋</span>
        </div>
        <h3 className="text-lg font-bold text-white">{title || 'Document Summary'}</h3>
        <span className="ml-auto risk-badge bg-surface-elevated text-gray-400 border-white/5">
          {totalClauses} clauses analyzed
        </span>
      </div>
      <p className="text-gray-300 text-sm leading-relaxed">{summary}</p>
    </div>
  );
}

function RiskLegend() {
  return (
    <div className="flex flex-wrap gap-4 mb-6">
      {Object.entries(RISK_COLORS).map(([level, config]) => (
        <div key={level} className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${config.bg}`} />
          <span className="text-xs text-gray-400 font-medium">{config.label}</span>
        </div>
      ))}
    </div>
  );
}

export default function HeatmapView({ analysis }) {
  const riskCounts = {
    low: analysis.risks.filter((r) => r.risk_level === 'low').length,
    moderate: analysis.risks.filter((r) => r.risk_level === 'moderate').length,
    high: analysis.risks.filter((r) => r.risk_level === 'high').length,
  };

  // Sort: high risk first, then moderate, then low
  const sortedRisks = [...analysis.risks].sort((a, b) => {
    const order = { high: 0, moderate: 1, low: 2 };
    return order[a.risk_level] - order[b.risk_level];
  });

  return (
    <div className="animate-fade-in">
      <OverallRiskGauge score={analysis.overall_risk_score} />

      <DocumentSummary
        summary={analysis.document_summary}
        title={analysis.document_title}
        totalClauses={analysis.total_clauses_analyzed}
      />

      {/* Risk Distribution Chips */}
      <div className="flex flex-wrap gap-3 mb-6">
        {riskCounts.high > 0 && (
          <div className="risk-badge-high">
            {riskCounts.high} High Variance
          </div>
        )}
        {riskCounts.moderate > 0 && (
          <div className="risk-badge-moderate">
            {riskCounts.moderate} Moderate Variance
          </div>
        )}
        {riskCounts.low > 0 && (
          <div className="risk-badge-low">
            {riskCounts.low} Standard
          </div>
        )}
      </div>

      <RiskLegend />

      {/* Risk Cards Grid */}
      <div className="grid gap-4 md:grid-cols-2">
        {sortedRisks.map((risk, index) => (
          <RiskCard key={`${risk.category}-${index}`} risk={risk} index={index} />
        ))}
      </div>

      {/* Disclaimer Footer */}
      <div className="mt-8 p-5 rounded-xl bg-surface-card/50 border border-white/5">
        <p className="text-xs text-gray-500 leading-relaxed text-center">
          {analysis.disclaimer}
        </p>
      </div>
    </div>
  );
}
