import React from 'react';

/**
 * Non-collapsible legal disclaimer banner.
 * Permanently visible at the top of the page to ensure UPL compliance.
 * Cannot be dismissed, hidden, or collapsed by the user.
 */
export default function LegalDisclaimer() {
  return (
    <div
      id="legal-disclaimer-banner"
      role="banner"
      aria-label="Legal Disclaimer"
      className="bg-amber-500/10 border-b border-amber-500/20 px-6 py-3"
    >
      <div className="max-w-7xl mx-auto flex items-start gap-3">
        <span className="text-amber-400 text-lg flex-shrink-0 mt-0.5">⚖️</span>
        <p className="text-xs text-amber-200/90 leading-relaxed">
          <span className="font-bold text-amber-300 uppercase tracking-wider">
            Important Disclaimer:
          </span>{' '}
          LeaseLens is an AI-powered informational and educational tool only. It does{' '}
          <span className="font-bold underline">not</span> constitute legal advice, does not create
          an attorney-client relationship, and should not be used as a substitute for professional
          legal counsel. All risk assessments are based on statistical comparisons against market
          baselines and may not reflect jurisdiction-specific regulations. Always consult a qualified
          legal professional before making any decisions regarding your lease agreement.
        </p>
      </div>
    </div>
  );
}
