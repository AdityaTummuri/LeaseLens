import React, { useState, useRef, useCallback } from 'react';

export default function FileUpload({ onAnalyze }) {
  const [dragOver, setDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [rawText, setRawText] = useState('');
  const [mode, setMode] = useState('file'); // 'file' | 'text'
  const fileInputRef = useRef(null);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file && (file.type === 'application/pdf' || file.type.startsWith('image/'))) {
      setSelectedFile(file);
    }
  }, []);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback(() => setDragOver(false), []);

  const handleFileSelect = useCallback((e) => {
    const file = e.target.files[0];
    if (file) setSelectedFile(file);
  }, []);

  const handleSubmit = useCallback(() => {
    if (mode === 'file' && selectedFile) {
      onAnalyze({ file: selectedFile });
    } else if (mode === 'text' && rawText.trim()) {
      onAnalyze({ rawText: rawText.trim() });
    }
  }, [mode, selectedFile, rawText, onAnalyze]);

  const canSubmit =
    (mode === 'file' && selectedFile) || (mode === 'text' && rawText.trim().length > 50);

  return (
    <div className="max-w-2xl mx-auto">
      {/* Mode Toggle */}
      <div className="flex gap-2 mb-6 p-1 bg-surface-card rounded-xl w-fit mx-auto">
        <button
          id="tab-file-upload"
          onClick={() => setMode('file')}
          className={`px-5 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
            mode === 'file'
              ? 'bg-accent-primary text-white shadow-lg shadow-accent-primary/25'
              : 'text-gray-400 hover:text-gray-200'
          }`}
        >
          📄 Upload PDF
        </button>
        <button
          id="tab-paste-text"
          onClick={() => setMode('text')}
          className={`px-5 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
            mode === 'text'
              ? 'bg-accent-primary text-white shadow-lg shadow-accent-primary/25'
              : 'text-gray-400 hover:text-gray-200'
          }`}
        >
          ✏️ Paste Text
        </button>
      </div>

      {mode === 'file' ? (
        /* Drag-and-Drop Zone */
        <div
          id="dropzone"
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => fileInputRef.current?.click()}
          className={`glass-card p-12 text-center cursor-pointer transition-all duration-300 ${
            dragOver
              ? 'border-accent-primary/50 bg-accent-primary/5 scale-[1.02]'
              : selectedFile
              ? 'border-risk-low/30 bg-risk-low/5'
              : 'hover:border-white/10 hover:bg-surface-card'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,image/*"
            onChange={handleFileSelect}
            className="hidden"
            id="file-input"
          />

          {selectedFile ? (
            <div className="animate-fade-in">
              <div className="w-16 h-16 rounded-2xl bg-risk-low/10 flex items-center justify-center mx-auto mb-4">
                <span className="text-3xl">✅</span>
              </div>
              <p className="text-white font-semibold text-lg">{selectedFile.name}</p>
              <p className="text-gray-500 text-sm mt-1">
                {(selectedFile.size / 1024).toFixed(1)} KB · Click to change
              </p>
            </div>
          ) : (
            <>
              <div className="w-16 h-16 rounded-2xl bg-accent-primary/10 flex items-center justify-center mx-auto mb-4">
                <span className="text-3xl">{dragOver ? '📥' : '📄'}</span>
              </div>
              <p className="text-white font-semibold text-lg mb-2">
                Drop your lease agreement here
              </p>
              <p className="text-gray-500 text-sm">
                or click to browse · PDF and image files supported
              </p>
            </>
          )}
        </div>
      ) : (
        /* Text Input */
        <div className="glass-card p-6">
          <textarea
            id="text-input"
            value={rawText}
            onChange={(e) => setRawText(e.target.value)}
            placeholder="Paste the full text of your lease agreement here..."
            rows={12}
            className="w-full bg-surface rounded-xl p-4 text-gray-200 text-sm font-mono 
                       border border-white/5 focus:border-accent-primary/30 focus:ring-1 
                       focus:ring-accent-primary/20 outline-none resize-y transition-all 
                       placeholder:text-gray-600"
          />
          <p className="text-right text-xs text-gray-600 mt-2">
            {rawText.length} characters
            {rawText.length > 0 && rawText.length < 50 && (
              <span className="text-amber-400 ml-2">· Minimum 50 characters required</span>
            )}
          </p>
        </div>
      )}

      {/* Submit Button */}
      <button
        id="btn-analyze"
        onClick={handleSubmit}
        disabled={!canSubmit}
        className={`mt-6 w-full py-4 rounded-xl text-base font-semibold transition-all duration-300 ${
          canSubmit
            ? 'bg-gradient-to-r from-accent-primary to-accent-secondary text-white ' +
              'hover:shadow-lg hover:shadow-accent-primary/25 hover:scale-[1.01] active:scale-[0.99]'
            : 'bg-surface-elevated text-gray-600 cursor-not-allowed'
        }`}
      >
        {canSubmit ? '🔍 Analyze Lease Agreement' : 'Upload or paste your lease to begin'}
      </button>
    </div>
  );
}
