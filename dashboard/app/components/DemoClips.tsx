'use client';

import { useState, useEffect } from 'react';

interface Clip {
  id: string;
  title: string;
  description: string;
  url: string;
}

export default function DemoClips() {
  const clips: Clip[] = [
    {
      id: 'intrusion',
      title: 'Intrusion Detection Alert',
      description: 'Triggered when a person enters a restricted polygon zone during off-hours, playing the local siren and sending a metadata alert.',
      url: '/demo_intrusion.mp4',
    },
    {
      id: 'productivity',
      title: 'Productivity State Tracker',
      description: 'Calculates active vs. idle states based on skeleton skeletal keypoint displacement within a workstation zone.',
      url: '/demo_productivity.mp4',
    },
    {
      id: 'reasoning',
      title: 'Ask Your Cameras',
      description: 'Natural language reasoning query fetching database event history and summarizing it using a local deepseek-r1 model.',
      url: '/demo_ask.mp4',
    },
  ];

  const [activeTab, setActiveTab] = useState(clips[0].id);
  const [videoError, setVideoError] = useState(false);
  const activeClip = clips.find((c) => c.id === activeTab) || clips[0];

  // Reset video error when tab changes
  useEffect(() => {
    setVideoError(false);
  }, [activeTab]);

  return (
    <div className="bg-white rounded-3xl border border-[#e2e8f0] p-6 shadow-sm">
      <div className="mb-5">
        <h2 className="text-[20px] font-bold text-[#0f172a] tracking-tight">
          Edge Demo Recordings
        </h2>
        <p className="text-[13px] text-[#64748b] font-medium mt-0.5">
          Examples captured during local testing (Verifying Part 8 Local vs. Cloud Split)
        </p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-[#f1f5f9] mb-5 gap-2 overflow-x-auto">
        {clips.map((clip) => (
          <button
            key={clip.id}
            onClick={() => setActiveTab(clip.id)}
            className={`pb-3 px-3 text-[13px] font-bold transition-all border-b-2 whitespace-nowrap outline-none ${
              activeTab === clip.id
                ? 'border-[#3b2fc9] text-[#3b2fc9]'
                : 'border-transparent text-[#64748b] hover:text-[#0f172a]'
            }`}
          >
            {clip.title}
          </button>
        ))}
      </div>

      {/* Active Clip Display */}
      <div className="space-y-4">
        <div className="aspect-video bg-[#0f172a] rounded-2xl overflow-hidden flex items-center justify-center relative border border-[#e2e8f0]">
          {!videoError ? (
            <video
              src={activeClip.url}
              controls
              onError={() => setVideoError(true)}
              className="w-full h-full object-contain"
              poster={`/posters/${activeClip.id}.jpg`}
            >
              Your browser does not support the video tag.
            </video>
          ) : (
            <div className="flex flex-col items-center justify-center text-center p-8 space-y-4 w-full h-full bg-[#0a0f1d] text-slate-300">
              <div className="p-4 bg-indigo-500/10 border border-indigo-500/20 rounded-full">
                <svg className="w-10 h-10 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 002.25-2.25v-9a2.25 2.25 0 00-2.25-2.25h-9A2.25 2.25 0 002.25 7.5v9a2.25 2.25 0 002.25 2.25z" />
                </svg>
              </div>
              <div className="space-y-1.5 max-w-sm">
                <p className="text-[14px] font-bold text-white tracking-wide uppercase">Demo Clip Coming Soon</p>
                <p className="text-[12px] text-slate-400 leading-relaxed">
                  This pre-recorded demonstration is pending upload. Run your local edge ingestion pipeline in Terminal 4 to see real-time events on the dashboard!
                </p>
              </div>
            </div>
          )}
          <div className="absolute top-3 left-3 bg-[#02091c]/80 backdrop-blur-md px-3 py-1 rounded-full text-[10px] font-bold text-indigo-300 uppercase tracking-wider border border-indigo-500/20">
            Local Test Capture
          </div>
        </div>

        <div className="p-4 bg-[#f8f9fc] rounded-2xl border border-[#e2e8f0]">
          <p className="text-[13px] text-[#374151] font-semibold leading-relaxed">
            {activeClip.description}
          </p>
        </div>
      </div>
    </div>
  );
}

