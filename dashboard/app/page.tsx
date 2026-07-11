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
    <main className="min-h-screen bg-[#f8f9fc] text-[#1e293b] font-sans relative pb-16">
      <div className="max-w-7xl mx-auto px-6 py-10 space-y-8">
        
        {/* Header */}
        <header className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-4 gap-4">
          <div>
            <h1 className="text-[34px] font-extrabold tracking-tight text-[#0f172a] leading-tight">
              AgentGrid Dashboard
            </h1>
            <p className="text-[#64748b] mt-1.5 text-[15px] font-medium max-w-3xl">
              Multi-Agent Video Intelligence Control & Analytics Platform. Powered by edge processing, unified in the cloud.
            </p>
          </div>
          <div className="flex items-center space-x-2 bg-[#eef2ff] border border-[#e0e7ff] px-4 py-2 rounded-full self-start sm:self-center">
            <span className="h-2 w-2 rounded-full bg-[#4f46e5] animate-pulse" />
            <span className="text-[11px] font-bold text-[#4f46e5] tracking-wider uppercase font-sans">
              CLOUD LAYER LIVE
            </span>
          </div>
        </header>

        {/* Dashboard Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          
          {/* Left Column (Ask Your Cameras & Efficiency Split) */}
          <div className="lg:col-span-7 space-y-8">
            <AskCamerasBox />
            
            {/* Efficiency Split Panel */}
            <div className="bg-white rounded-3xl border border-[#e2e8f0] p-8 shadow-sm relative overflow-hidden">
              <div className="absolute top-0 right-0 px-3 py-1 bg-[#1e293b] text-white text-[9px] uppercase tracking-widest font-bold">
                ILLUSTRATIVE SPEC PART 8
              </div>
              
              <h3 className="text-xl font-bold text-[#0f172a] flex items-center gap-2">
                <svg className="w-5 h-5 text-[#4f46e5]" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2.5">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
                </svg>
                Efficiency Split
              </h3>
              
              <p className="text-[13px] text-[#64748b] mt-3 leading-relaxed font-medium">
                AgentGrid runs heavy neural models (YOLOv8) at the edge, sending only lightweight JSON event metadata to the cloud. This avoids continuous 24/7 video streaming costs.
              </p>

              <div className="mt-8 flex flex-col md:flex-row gap-6 justify-between items-start">
                <div className="flex-1 w-full space-y-5">
                  <div>
                    <div className="flex justify-between text-[11px] font-bold tracking-wide uppercase mb-1.5">
                      <span className="text-[#0f172a]">TRADITIONAL CLOUD AI</span>
                      <span className="text-[#ef4444] font-mono">~2,000 Kbps</span>
                    </div>
                    <div className="w-full bg-[#f1f5f9] rounded-full h-3">
                      <div className="bg-[#ef4444] h-3 rounded-full w-full" />
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-[11px] font-bold tracking-wide uppercase mb-1.5">
                      <span className="text-[#0f172a]">AGENTGRID SPLIT AI</span>
                      <span className="text-[#22c55e] font-mono">~0.4 Kbps (99.98% Saving)</span>
                    </div>
                    <div className="w-full bg-[#f1f5f9] rounded-full h-3 relative">
                      <div className="bg-[#4f46e5] h-3 w-3 rounded-full absolute left-0" />
                    </div>
                  </div>
                </div>

                <div className="w-full md:w-[260px] p-4 rounded-2xl bg-[#eef2ff] border border-[#e0e7ff] text-[11.5px] leading-relaxed text-[#3730a3] relative font-medium">
                  <strong>Why no video here?</strong> <i>Continuous live streaming to public servers requires expensive cloud infrastructure. Mirroring professional architectures, we keep raw video locally on-site and sync states & events to this dashboard.</i>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column (AI Agent Controller, Live Event Feed, Onboard Edge Stream) */}
          <div className="lg:col-span-5 space-y-8">
            <AgentToggle refreshTrigger={refreshTrigger} />
            <LiveEventFeed />
            <AddCameraForm onCameraAdded={handleCameraAdded} />
          </div>

        </div>

        {/* Footer */}
        <footer className="pt-8 border-t border-[#e2e8f0] flex justify-between items-center text-[13px] font-bold text-[#64748b]">
          <div>AgentGrid</div>
        </footer>
      </div>
    </main>
  );
}
