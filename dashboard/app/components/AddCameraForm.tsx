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
    <div className="bg-white rounded-3xl border border-[#e2e8f0] p-6 shadow-sm">
      <div>
        <h2 className="text-[20px] font-bold text-[#0f172a] tracking-tight">
          Onboard Edge Stream
        </h2>
        <p className="text-[13px] text-[#64748b] font-medium mt-0.5">Register a local RTSP feed</p>
      </div>

      <form onSubmit={handleSubmit} className="mt-5 space-y-4">
        <div>
          <label className="block text-[11px] font-bold text-[#475569] uppercase tracking-wider mb-1.5">
            CAMERA NAME
          </label>
          <input
            type="text"
            placeholder="e.g. Back Warehouse Entrance"
            value={name}
            onChange={(e) => setName(e.target.value)}
            disabled={submitting}
            className="w-full bg-[#f1f5f9] border border-[#e2e8f0] rounded-xl px-4 py-3 text-[#0f172a] placeholder-[#94a3b8] outline-none focus:border-[#4f46e5] focus:ring-1 focus:ring-[#4f46e5] transition-all font-sans text-[14px]"
          />
        </div>

        <div>
          <label className="block text-[11px] font-bold text-[#475569] uppercase tracking-wider mb-1.5">
            RTSP URL
          </label>
          <input
            type="text"
            placeholder="rtsp://localhost:8554/cam1"
            value={rtspUrl}
            onChange={(e) => setRtspUrl(e.target.value)}
            disabled={submitting}
            className="w-full bg-[#f1f5f9] border border-[#e2e8f0] rounded-xl px-4 py-3 text-[#0f172a] placeholder-[#94a3b8] outline-none focus:border-[#4f46e5] focus:ring-1 focus:ring-[#4f46e5] transition-all font-mono text-[13px]"
          />
        </div>

        {status.type && (
          <div
            className={`p-3 rounded-xl text-xs font-semibold border ${
              status.type === 'success'
                ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                : 'bg-rose-50 border-rose-200 text-rose-800'
            }`}
          >
            {status.message}
          </div>
        )}

        <button
          type="submit"
          disabled={submitting}
          className="w-full bg-[#3b2fc9] hover:bg-[#2e24a8] text-white font-bold py-3 px-4 rounded-xl transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 text-[14px]"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M13.19 8.688a4.5 4.5 0 011.242 7.244l-4.5 4.5a4.5 4.5 0 01-6.364-6.364l1.757-1.757m13.35-.622l1.757-1.757a4.5 4.5 0 00-6.364-6.364l-4.5 4.5a4.5 4.5 0 001.242 7.244" />
          </svg>
          {submitting ? 'Registering...' : 'Register Feed'}
        </button>
      </form>
    </div>
  );
}
