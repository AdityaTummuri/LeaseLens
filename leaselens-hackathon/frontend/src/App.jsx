import React, { useState, useCallback, useRef, useEffect } from 'react';
import LegalDisclaimer from './components/LegalDisclaimer';
import FileUpload from './components/FileUpload';
import HeatmapView from './components/HeatmapView';
import LoadingSpinner from './components/LoadingSpinner';

const API_BASE_URL =
  import.meta.env.VITE_API_URL || 'https://leaselens-backend.onrender.com';
const API_URL = `${API_BASE_URL}/api/analyze-lease`;

export default function App() {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isColdStarting, setIsColdStarting] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('upload'); // 'upload' | 'results'

  const coldStartTimerRef = useRef(null);
  const abortControllerRef = useRef(null);

  const handleAnalyze = useCallback(async ({ file, rawText }) => {
    // Abort any prior in-flight request to save network bandwidth and avoid race conditions
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;

    // Timeout signal after 120 seconds to prevent hanging requests
    const timeoutId = setTimeout(() => {
      controller.abort();
    }, 120000);

    setLoading(true);
    setIsColdStarting(false);
    setError(null);
    setAnalysis(null);

    // Render free-tier cold-start detector (> 3 seconds)
    coldStartTimerRef.current = setTimeout(() => {
      setIsColdStarting(true);
    }, 3000);

    try {
      const formData = new FormData();
      if (file) {
        formData.append('file', file);
      } else if (rawText) {
        formData.append('raw_text', rawText);
      }

      const response = await fetch(API_URL, {
        method: 'POST',
        body: formData,
        signal: controller.signal,
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(
          errData.detail || `Server returned error status: ${response.status}`
        );
      }

      const data = await response.json();
      setAnalysis(data);
      setActiveTab('results');
    } catch (err) {
      if (err.name === 'AbortError') {
        setError('Analysis request was cancelled or timed out. Please try again.');
      } else {
        setError(
          err.message ||
            'Failed to connect to LeaseLens backend. If using Render free-tier, the server may take ~50s to wake up from idle.'
        );
      }
    } finally {
      clearTimeout(timeoutId);
      if (coldStartTimerRef.current) {
        clearTimeout(coldStartTimerRef.current);
      }
      setLoading(false);
      setIsColdStarting(false);
    }
  }, []);

  const handleReset = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setAnalysis(null);
    setError(null);
    setIsColdStarting(false);
    setActiveTab('upload');
  }, []);

  // Cleanup in-flight requests and timers on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      if (coldStartTimerRef.current) {
        clearTimeout(coldStartTimerRef.current);
      }
    };
  }, []);

  return (
    <div className="min-h-screen bg-surface">
      {/* Non-collapsible Legal Disclaimer Banner */}
      <LegalDisclaimer />

      {/* Header */}
      <header className="border-b border-white/5 bg-surface/80 backdrop-blur-lg sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-accent-primary to-accent-secondary flex items-center justify-center">
              <span className="text-xl" role="img" aria-label="lens">🔍</span>
            </div>
            <div>
              <h1 className="text-xl font-bold gradient-text">LeaseLens</h1>
              <p className="text-xs text-gray-500 font-medium tracking-wide uppercase">
                Lease Risk Highlighter
              </p>
            </div>
          </div>

          {analysis && (
            <button
              id="btn-new-analysis"
              onClick={handleReset}
              className="px-4 py-2 rounded-lg bg-surface-elevated text-gray-300 
                         hover:bg-surface-card hover:text-white text-sm font-medium 
                         transition-all duration-200 border border-white/5"
            >
              ← New Analysis
            </button>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {loading ? (
          <LoadingSpinner isColdStarting={isColdStarting} />
        ) : analysis ? (
          <HeatmapView analysis={analysis} />
        ) : (
          <div className="animate-fade-in">
            <div className="text-center mb-10">
              <h2 className="text-3xl font-bold text-white mb-3">
                Understand Your Lease Agreement
              </h2>
              <p className="text-gray-400 max-w-2xl mx-auto text-lg">
                Upload your residential lease and get an instant statistical risk heatmap.
                See how each clause compares against regional market standards.
              </p>
            </div>

            <FileUpload onAnalyze={handleAnalyze} />

            {error && (
              <div
                id="error-banner"
                className="mt-6 max-w-2xl mx-auto p-4 rounded-xl bg-risk-high/10 
                           border border-risk-high/20 text-risk-high text-sm"
                role="alert"
              >
                <span className="font-semibold">Error: </span>
                {error}
              </div>
            )}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-white/5 mt-auto">
        <div className="max-w-7xl mx-auto px-6 py-6 text-center">
          <p className="text-xs text-gray-600">
            LeaseLens is an informational tool powered by AI. It does not provide legal advice.
            Always consult a qualified legal professional for guidance on lease agreements.
          </p>
        </div>
      </footer>
    </div>
  );
}
