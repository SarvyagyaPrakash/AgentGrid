'use client';

import { useState, useEffect } from 'react';
import AgentToggle from './components/AgentToggle';
import LiveEventFeed from './components/LiveEventFeed';
import AddCameraForm from './components/AddCameraForm';
import AskCamerasBox from './components/AskCamerasBox';
import DemoClips from './components/DemoClips';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8333';

interface BenchmarkMetric {
  avg_inference_ms: number;
  avg_fps: number;
  model_file_size_mb: number;
}

interface BenchmarkResults {
  test_date: string;
  test_duration_seconds: number;
  hardware: string;
  raw_video: {
    total_bytes: number;
    avg_kbps: number;
    peak_kbps: number;
  };
  event_only: {
    total_events: number;
    total_bytes: number;
    avg_kbps: number;
  };
  extrapolated: {
    events_per_hour: number;
    estimated_daily_event_kb: number;
  };
  savings_percent: number;
  model_speed: {
    test_frame_count: number;
    pytorch: BenchmarkMetric;
    onnx: BenchmarkMetric;
    coreml: BenchmarkMetric;
    fastest_method: string;
    note: string;
  };
}

export default function Home() {
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [benchmarks, setBenchmarks] = useState<BenchmarkResults | null>(null);

  const handleCameraAdded = () => {
    setRefreshTrigger((prev) => prev + 1);
  };

  useEffect(() => {
    const fetchBenchmarks = () => {
      fetch(`${API_URL}/api/benchmarks`)
        .then((res) => res.json())
        .then((data) => {
          if (data && data.raw_video) {
            setBenchmarks(data);
          }
        })
        .catch((err) => console.error('Error fetching benchmarks:', err));
    };
    fetchBenchmarks();
    const interval = setInterval(fetchBenchmarks, 10000);
    return () => clearInterval(interval);
  }, []);

  // Format date helper
  const formatDate = (isoString: string) => {
    try {
      const d = new Date(isoString);
      return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
    } catch {
      return 'Recent';
    }
  };

  return (
    <main className="min-h-screen bg-[#f8f9fc] text-[#1e293b] font-sans relative pb-16">
      <div className="max-w-7xl mx-auto px-6 py-10 space-y-8">
        
        {/* Brand Header Bar */}
        <header className="bg-[#02091c] rounded-3xl border border-[#111827]/10 p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 shadow-sm">
          <div className="flex items-center">
            <img 
              src="/logo.png" 
              alt="AgentGrid Logo" 
              className="h-16 md:h-20 w-auto object-contain rounded-lg" 
            />
          </div>
          <div className="flex items-center space-x-2 bg-emerald-500/10 border border-emerald-500/20 px-4 py-2 rounded-full self-start sm:self-center mr-2">
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-[11px] font-bold text-emerald-400 tracking-wider uppercase font-sans">
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
                {benchmarks ? `MEASURED — ${formatDate(benchmarks.test_date)} — ${benchmarks.hardware || 'CPU'}` : 'LOADING MEASUREMENTS...'}
              </div>
              
              <h3 className="text-xl font-bold text-[#0f172a] flex items-center gap-2">
                <svg className="w-5 h-5 text-[#4f46e5]" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2.5">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
                </svg>
                Efficiency Split & Speed Benchmarks
              </h3>
              
              <p className="text-[13px] text-[#64748b] mt-3 leading-relaxed font-medium">
                AgentGrid runs heavy neural models (YOLOv8) at the edge, sending only lightweight JSON event metadata to the cloud. This avoids continuous 24/7 video streaming costs.
              </p>

              {/* Bandwidth Telemetry */}
              <div className="mt-8 flex flex-col md:flex-row gap-6 justify-between items-start">
                <div className="flex-1 w-full space-y-5">
                  <div>
                    <div className="flex justify-between text-[11px] font-bold tracking-wide uppercase mb-1.5">
                      <span className="text-[#0f172a]">TRADITIONAL CLOUD AI (RAW RTSP STREAM)</span>
                      <span className="text-[#ef4444] font-mono">
                        {benchmarks ? `~${Math.round(benchmarks.raw_video.avg_kbps).toLocaleString()} Kbps` : '~2,000 Kbps'}
                      </span>
                    </div>
                    <div className="w-full bg-[#f1f5f9] rounded-full h-3">
                      <div className="bg-[#ef4444] h-3 rounded-full w-full" />
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-[11px] font-bold tracking-wide uppercase mb-1.5">
                      <span className="text-[#0f172a]">AGENTGRID SPLIT AI (JSON EVENTS ONLY)</span>
                      <span className="text-[#22c55e] font-mono">
                        {benchmarks 
                          ? `~${benchmarks.event_only.avg_kbps.toFixed(4)} Kbps (${benchmarks.savings_percent.toFixed(4)}% Saving)` 
                          : '~0.4 Kbps (99.98% Saving)'}
                      </span>
                    </div>
                    <div className="w-full bg-[#f1f5f9] rounded-full h-3 relative">
                      <div className="bg-[#22c55e] h-3 w-3 rounded-full absolute left-0" style={{ width: benchmarks ? `${(benchmarks.event_only.avg_kbps / benchmarks.raw_video.avg_kbps) * 100}%` : '0.1%' }} />
                    </div>
                  </div>
                </div>

                <div className="w-full md:w-[260px] p-4 rounded-2xl bg-[#eef2ff] border border-[#e0e7ff] text-[11.5px] leading-relaxed text-[#3730a3] relative font-medium">
                  <strong>Measured bandwidth:</strong> <i>Continuous live streaming to public servers requires expensive cloud infrastructure. Mirroring professional architectures, we keep raw video locally on-site and sync states & events to this dashboard.</i>
                </div>
              </div>

              {/* Model Speed Telemetry */}
              {benchmarks && benchmarks.model_speed && (
                <div className="mt-8 pt-6 border-t border-[#f1f5f9]">
                  <h4 className="text-[12px] font-bold text-[#0f172a] uppercase tracking-wider mb-4 flex items-center gap-1.5">
                    <svg className="w-4.5 h-4.5 text-[#4f46e5]" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2.5">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 6a7.5 7.5 0 107.5 7.5h-7.5V6z" />
                      <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 10.5H21A7.5 7.5 0 0013.5 3v7.5z" />
                    </svg>
                    Edge Model Speed Comparison (YOLOv8s-Pose)
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-[12px]">
                    <div className={`p-4 rounded-2xl border ${benchmarks.model_speed.fastest_method === 'pytorch' ? 'bg-emerald-50 border-emerald-200' : 'bg-slate-50 border-slate-100'}`}>
                      <div className="flex justify-between items-center">
                        <span className="font-bold text-slate-500 uppercase text-[10px]">PyTorch CPU Baseline</span>
                        {benchmarks.model_speed.fastest_method === 'pytorch' && (
                          <span className="bg-emerald-500 text-white text-[8px] font-bold px-1.5 py-0.5 rounded">FASTEST</span>
                        )}
                      </div>
                      <div className="text-lg font-extrabold text-slate-800 mt-1 font-mono">
                        {benchmarks.model_speed.pytorch.avg_fps} FPS
                      </div>
                      <div className="text-slate-500 text-[11px] mt-0.5">
                        {benchmarks.model_speed.pytorch.avg_inference_ms} ms • {benchmarks.model_speed.pytorch.model_file_size_mb} MB
                      </div>
                    </div>

                    <div className={`p-4 rounded-2xl border ${benchmarks.model_speed.fastest_method === 'onnx' ? 'bg-emerald-50 border-emerald-200' : 'bg-indigo-50/50 border-indigo-100'}`}>
                      <div className="flex justify-between items-center">
                        <span className="font-bold text-indigo-600 uppercase text-[10px]">Optimized ONNX CPU</span>
                        {benchmarks.model_speed.fastest_method === 'onnx' && (
                          <span className="bg-emerald-500 text-white text-[8px] font-bold px-1.5 py-0.5 rounded">FASTEST</span>
                        )}
                      </div>
                      <div className="text-lg font-extrabold text-indigo-900 mt-1 font-mono">
                        {benchmarks.model_speed.onnx.avg_fps} FPS
                      </div>
                      <div className="text-indigo-600 text-[11px] mt-0.5">
                        {benchmarks.model_speed.onnx.avg_inference_ms} ms • {benchmarks.model_speed.onnx.model_file_size_mb} MB
                      </div>
                    </div>

                    <div className={`p-4 rounded-2xl border ${benchmarks.model_speed.fastest_method === 'coreml' ? 'bg-emerald-50/50 border-emerald-200' : 'bg-purple-50/50 border-purple-100'}`}>
                      <div className="flex justify-between items-center">
                        <span className="font-bold text-purple-700 uppercase text-[10px]">CoreML Neural Engine</span>
                        {benchmarks.model_speed.fastest_method === 'coreml' && (
                          <span className="bg-emerald-500 text-white text-[8px] font-bold px-1.5 py-0.5 rounded">FASTEST</span>
                        )}
                      </div>
                      <div className="text-lg font-extrabold text-purple-900 mt-1 font-mono">
                        {benchmarks.model_speed.coreml.avg_fps} FPS
                      </div>
                      <div className="text-purple-600 text-[11px] mt-0.5">
                        {benchmarks.model_speed.coreml.avg_inference_ms} ms • {benchmarks.model_speed.coreml.model_file_size_mb} MB
                      </div>
                    </div>
                  </div>
                  
                  {benchmarks.model_speed.note && (
                    <div className="mt-4 p-3 rounded-xl bg-slate-50 border border-slate-100 text-[11px] text-[#64748b] leading-relaxed">
                      <strong>Note:</strong> {benchmarks.model_speed.note}
                    </div>
                  )}
                </div>
              )}
            </div>
            <DemoClips />
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
