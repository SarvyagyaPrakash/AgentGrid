'use client';

import { useState } from 'react';

export default function AskCamerasBox() {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{
    answer: string;
    matched_events: number;
    source?: string;
  } | null>(null);
  const [error, setError] = useState('');

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8333';

  const handleAsk = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await fetch(`${API_URL}/api/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      });

      const data = await response.json();

      if (response.ok) {
        setResult({
          answer: data.answer,
          matched_events: data.matched_events,
          source: data.source,
        });
      } else {
        setError(data.detail || 'Failed to query the reasoning layer.');
      }
    } catch (err) {
      console.error('Failed to ask cameras:', err);
      setError('Could not connect to reasoning layer.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white/5 backdrop-blur-lg rounded-3xl border border-white/10 p-6 md:p-8 shadow-2xl transition-all duration-300 hover:shadow-teal-500/5 hover:border-white/20">
      <div className="flex items-center space-x-3">
        <div className="p-2 bg-teal-500/10 text-teal-300 rounded-xl border border-teal-500/20">
          <svg className="w-6 h-6 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
        </div>
        <div>
          <h2 className="text-xl md:text-2xl font-bold bg-gradient-to-r from-teal-200 via-emerald-200 to-cyan-200 bg-clip-text text-transparent">
            Ask Your Cameras
          </h2>
          <p className="text-sm text-slate-400 mt-0.5">Semantic search and QA powered by local LLM</p>
        </div>
      </div>

      <form onSubmit={handleAsk} className="mt-6">
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="e.g. Were there any intrusion events last night?"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={loading}
            className="flex-1 bg-slate-900/50 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-slate-500 outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500 transition-all font-sans text-sm"
          />
          <button
            type="submit"
            disabled={loading || !question.trim()}
            className="bg-gradient-to-r from-teal-500 to-emerald-600 hover:from-teal-600 hover:to-emerald-700 text-white font-bold px-6 py-3 rounded-xl transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Thinking...' : 'Ask'}
          </button>
        </div>
      </form>

      {error && (
        <div className="mt-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs font-semibold">
          {error}
        </div>
      )}

      {result && (
        <div className="mt-6 p-5 rounded-2xl bg-teal-500/5 border border-teal-500/10 space-y-3 animate-fadeIn">
          <div className="flex items-center justify-between text-xs border-b border-teal-500/10 pb-2">
            <span className="text-slate-400 font-mono">
              Matched database events: <span className="text-teal-400 font-bold">{result.matched_events}</span>
            </span>
            {result.source && (
              <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono text-[10px]">
                source: {result.source}
              </span>
            )}
          </div>
          <p className="text-sm leading-relaxed text-slate-200 font-sans italic">
            &ldquo;{result.answer}&rdquo;
          </p>
        </div>
      )}
    </div>
  );
}
