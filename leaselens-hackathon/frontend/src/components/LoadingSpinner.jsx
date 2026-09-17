import React, { useState, useEffect } from 'react';

const STEPS = [
  { label: 'Extracting document text...', icon: '📄', duration: 8000 },
  { label: 'Classifying lease clauses...', icon: '🔍', duration: 12000 },
  { label: 'Applying UPL guardrails...', icon: '🛡️', duration: 5000 },
  { label: 'Generating risk heatmap...', icon: '🎨', duration: 3000 },
];

export default function LoadingSpinner({ isColdStarting = false }) {
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    if (currentStep >= STEPS.length - 1) return;
    const timer = setTimeout(
      () => setCurrentStep((s) => Math.min(s + 1, STEPS.length - 1)),
      STEPS[currentStep].duration
    );
    return () => clearTimeout(timer);
  }, [currentStep]);

  return (
    <div
      role="region"
      aria-label="Analysis in Progress"
      className="max-w-md mx-auto py-16 text-center animate-fade-in"
    >
      {/* Spinning Lens */}
      <div className="relative w-24 h-24 mx-auto mb-8">
        <div className="absolute inset-0 rounded-full border-4 border-surface-elevated" />
        <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-accent-primary animate-spin" />
        <div className="absolute inset-3 rounded-full bg-surface-card flex items-center justify-center">
          <span className="text-3xl animate-pulse-slow">
            {STEPS[currentStep].icon}
          </span>
        </div>
      </div>

      {/* Step Label */}
      <h3 className="text-white font-semibold text-lg mb-2">
        Analyzing Your Lease
      </h3>
      <p className="text-gray-400 text-sm mb-6">
        {STEPS[currentStep].label}
      </p>

      {/* Render Free-Tier Cold Start Notice */}
      {isColdStarting && (
        <div
          role="status"
          aria-live="polite"
          className="mb-8 p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/20 
                     text-amber-300 text-xs leading-relaxed max-w-sm mx-auto animate-fade-in text-left"
        >
          <div className="flex items-center gap-2 font-semibold mb-1 text-amber-200">
            <span>⚡</span>
            <span>Render Free-Tier Server Spinning Up</span>
          </div>
          <p className="text-[11px] text-amber-300/90">
            The backend is spinning up from its idle state. This initial cold-start takes
            ~30–50 seconds, after which subsequent requests are instantaneous.
          </p>
        </div>
      )}

      {/* Progress Steps */}
      <div className="flex flex-col gap-3 text-left max-w-xs mx-auto">
        {STEPS.map((step, i) => (
          <div
            key={i}
            className={`flex items-center gap-3 text-sm transition-all duration-500 ${
              i < currentStep
                ? 'text-risk-low'
                : i === currentStep
                ? 'text-white'
                : 'text-gray-600'
            }`}
          >
            <span className="w-5 text-center">
              {i < currentStep ? '✓' : i === currentStep ? '◉' : '○'}
            </span>
            <span className={i === currentStep ? 'font-medium' : ''}>
              {step.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
