import React, { useState, useEffect } from 'react';

const STEPS = [
  { label: 'Extracting document text...', icon: '📄', duration: 8000 },
  { label: 'Classifying lease clauses...', icon: '🔍', duration: 12000 },
  { label: 'Applying UPL guardrails...', icon: '🛡️', duration: 5000 },
  { label: 'Generating risk heatmap...', icon: '🎨', duration: 3000 },
];

export default function LoadingSpinner() {
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
    <div className="max-w-md mx-auto py-20 text-center animate-fade-in">
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
      <p className="text-gray-400 text-sm mb-8">
        {STEPS[currentStep].label}
      </p>

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
