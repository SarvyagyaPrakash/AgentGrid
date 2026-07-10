'use client';

import { useState } from 'react';
import AgentToggle from './components/AgentToggle';
import LiveEventFeed from './components/LiveEventFeed';
import AddCameraForm from './components/AddCameraForm';
import AskCamerasBox from './components/AskCamerasBox';

export default function Home() {
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const handleCameraAdded = () => {
    setRefreshTrigger((prev) => prev + 1);
  };

  return (
    <main className="min-h-screen bg-slate-950 text-white font-sans selection:bg-indigo-500/30 selection:text-indigo-200">
      {/* Background glow effects */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute top-1/3 right-1/4 w-[500px] h-[500px] bg-purple-500/5 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-10 left-10 w-80 h-80 bg-teal-500/5 rounded-full blur-3xl pointer-events-none" />

      <div className="max-w-7xl mx-auto px-4 py-8 md:py-12 relative z-10 space-y-8 md:space-y-12">
        
        {/* Header */}
        <header className="flex flex-col md:flex-row md:items-center md:justify-between border-b border-white/5 pb-8 gap-4">
          <div>
            <h1 className="text-3xl md:text-5xl font-extrabold tracking-tight bg-gradient-to-r from-white via-indigo-100 to-slate-400 bg-clip-text text-transparent">
              AgentGrid Dashboard
            </h1>
            <p className="text-slate-400 mt-2 text-base md:text-lg max-w-2xl">
              Multi-Agent Video Intelligence Control & Analytics Platform. Powered by edge processing, unified in the cloud.
            </p>
          </div>
          <div className="flex items-center space-x-3 bg-white/5 border border-white/10 px-4 py-2.5 rounded-2xl backdrop-blur-md">
            <div className="h-2 w-2 rounded-full bg-indigo-400 animate-pulse" />
            <span className="text-xs font-semibold text-slate-300 font-mono tracking-wider">CLOUD LAYER LIVE</span>
          </div>
        </header>

        {/* Dashboard Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 md:gap-8">
          
          {/* Left Column (Controllers & Forms) */}
          <div className="lg:col-span-7 space-y-6 md:space-y-8">
            <AgentToggle refreshTrigger={refreshTrigger} />
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <AddCameraForm onCameraAdded={handleCameraAdded} />
              <AskCamerasBox />
            </div>
          </div>

          {/* Right Column (Live Feed & Bandwidth) */}
          <div className="lg:col-span-5 space-y-6 md:space-y-8">
            <LiveEventFeed />
            
            {/* Bandwidth Comparison Panel */}
            <div className="bg-gradient-to-br from-white/5 to-transparent backdrop-blur-lg rounded-3xl border border-white/10 p-6 md:p-8 shadow-2xl relative overflow-hidden group hover:border-white/20 transition-all duration-300">
              <div className="absolute top-0 right-0 px-3 py-1 bg-indigo-500/10 text-indigo-300 border-l border-b border-indigo-500/20 rounded-bl-xl font-mono text-[9px] uppercase tracking-widest font-bold">
                Illustrative Spec Part 8
              </div>
              
              <h3 className="text-lg font-bold text-slate-200 flex items-center gap-2">
                <svg className="w-5 h-5 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Bandwidth & Compute Efficiency Split
              </h3>
              
              <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                AgentGrid runs heavy neural models (YOLOv8) at the edge, sending only lightweight JSON event metadata to the cloud. This avoids continuous 24/7 video streaming costs.
              </p>

              <div className="mt-6 space-y-4">
                <div>
                  <div className="flex justify-between text-xs font-semibold text-slate-300 mb-1">
                    <span>Traditional Cloud AI (Continuous Raw Streaming)</span>
                    <span className="font-mono text-rose-400">~2,000 Kbps</span>
                  </div>
                  <div className="w-full bg-slate-900 rounded-full h-2 border border-white/5">
                    <div className="bg-rose-500/60 h-2 rounded-full w-full" />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-xs font-semibold text-slate-300 mb-1">
                    <span>AgentGrid Split AI (Event Metadata Only)</span>
                    <span className="font-mono text-emerald-400">~0.4 Kbps (99.98% Saving)</span>
                  </div>
                  <div className="w-full bg-slate-900 rounded-full h-2 border border-white/5">
                    <div className="bg-gradient-to-r from-emerald-400 to-indigo-500 h-2 rounded-full w-[2%]" />
                  </div>
                </div>
              </div>

              <div className="mt-6 p-3 rounded-xl bg-indigo-500/5 border border-indigo-500/10 text-[11px] leading-relaxed text-indigo-200">
                <strong>Why no video here?</strong> Continuous live streaming to public servers requires expensive cloud infrastructure. Mirroring professional architectures (e.g. Dragonfruit), we keep raw video locally on-site and sync states & events to this dashboard.
              </div>
            </div>

          </div>

        </div>

        {/* Footer */}
        <footer className="text-center pt-8 border-t border-white/5 text-xs text-slate-500">
          AgentGrid Portfolio Project &bull; Day 6 Build completed successfully.
        </footer>
      </div>
    </main>
  );
}
