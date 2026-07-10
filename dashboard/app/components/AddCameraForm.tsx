'use client';

import { useState } from 'react';

export default function AddCameraForm({ onCameraAdded }: { onCameraAdded: () => void }) {
  const [name, setName] = useState('');
  const [rtspUrl, setRtspUrl] = useState('');
  const [status, setStatus] = useState<{ type: 'success' | 'error' | null; message: string }>({
    type: null,
    message: '',
  });
  const [submitting, setSubmitting] = useState(false);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8333';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !rtspUrl.trim()) {
      setStatus({ type: 'error', message: 'All fields are required.' });
      return;
    }

    setSubmitting(true);
    setStatus({ type: null, message: '' });

    try {
      const response = await fetch(`${API_URL}/api/cameras`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, rtsp_url: rtspUrl }),
      });

      const data = await response.json();

      if (response.ok) {
        setStatus({
          type: 'success',
          message: `Camera added successfully with ID: ${data.camera_id}`,
        });
        setName('');
        setRtspUrl('');
        onCameraAdded(); // Trigger refresh on parent
      } else {
        setStatus({
          type: 'error',
          message: data.detail || 'Failed to add camera.',
        });
      }
    } catch (err) {
      console.error('Failed to add camera:', err);
      setStatus({
        type: 'error',
        message: 'Could not connect to API server.',
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="bg-white/5 backdrop-blur-lg rounded-3xl border border-white/10 p-6 md:p-8 shadow-2xl transition-all duration-300 hover:shadow-purple-500/5 hover:border-white/20">
      <div>
        <h2 className="text-xl md:text-2xl font-bold bg-gradient-to-r from-purple-200 via-pink-200 to-rose-200 bg-clip-text text-transparent">
          Onboard Edge Stream
        </h2>
        <p className="text-sm text-slate-400 mt-1">Register a local RTSP feed or simulated loop</p>
      </div>

      <form onSubmit={handleSubmit} className="mt-6 space-y-4">
        <div>
          <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
            Camera Display Name
          </label>
          <input
            type="text"
            placeholder="e.g. Back Warehouse Entrance"
            value={name}
            onChange={(e) => setName(e.target.value)}
            disabled={submitting}
            className="w-full bg-slate-900/50 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-slate-500 outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all font-sans"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
            RTSP Stream URL
          </label>
          <input
            type="text"
            placeholder="rtsp://localhost:8554/cam1"
            value={rtspUrl}
            onChange={(e) => setRtspUrl(e.target.value)}
            disabled={submitting}
            className="w-full bg-slate-900/50 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-slate-500 outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all font-mono text-sm"
          />
        </div>

        {status.type && (
          <div
            className={`p-3 rounded-xl text-xs font-semibold border ${
              status.type === 'success'
                ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-300'
                : 'bg-rose-500/10 border-rose-500/20 text-rose-300'
            }`}
          >
            {status.message}
          </div>
        )}

        <button
          type="submit"
          disabled={submitting}
          className="w-full bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 hover:from-indigo-600 hover:via-purple-600 hover:to-pink-600 text-white font-bold py-3 px-4 rounded-xl shadow-lg shadow-purple-500/25 transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {submitting ? 'Registering Stream...' : 'Register Camera Feed'}
        </button>
      </form>
    </div>
  );
}
