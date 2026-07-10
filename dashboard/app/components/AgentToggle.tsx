'use client';

import { useEffect, useState, useCallback } from 'react';

interface Camera {
  camera_id: string;
  name: string;
  rtsp_url: string;
}

interface AgentConfig {
  camera_id: string;
  agent_name: string;
  enabled: boolean;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8333';

export default function AgentToggle({ refreshTrigger }: { refreshTrigger: number }) {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [configs, setConfigs] = useState<AgentConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [toggling, setToggling] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const [cRes, aRes] = await Promise.all([
        fetch(`${API_URL}/api/cameras`),
        fetch(`${API_URL}/api/agents`)
      ]);
      if (cRes.ok && aRes.ok) {
        const cData = await cRes.json();
        const aData = await aRes.json();
        setCameras(cData);
        setConfigs(aData);
      }
    } catch (err) {
      console.error('Failed to fetch data for AgentToggle:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [refreshTrigger, fetchData]);


  const handleToggle = async (cameraId: string, agentName: string, currentVal: boolean) => {
    const toggleKey = `${cameraId}-${agentName}`;
    setToggling(toggleKey);
    try {
      const response = await fetch(`${API_URL}/api/agents/${cameraId}/${agentName}/toggle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: !currentVal }),
      });
      if (response.ok) {
        setConfigs((prev) => {
          const index = prev.findIndex(
            (c) => c.camera_id === cameraId && c.agent_name === agentName
          );
          if (index > -1) {
            const updated = [...prev];
            updated[index] = { ...updated[index], enabled: !currentVal };
            return updated;
          } else {
            return [...prev, { camera_id: cameraId, agent_name: agentName, enabled: !currentVal }];
          }
        });
      }
    } catch (err) {
      console.error('Failed to toggle agent:', err);
    } finally {
      setToggling(null);
    }
  };

  const isEnabled = (cameraId: string, agentName: string) => {
    const conf = configs.find((c) => c.camera_id === cameraId && c.agent_name === agentName);
    return conf ? conf.enabled : false; // default to false
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8 bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 shadow-xl min-h-[250px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-400"></div>
      </div>
    );
  }

  const agentsList = ['intrusion_detection', 'productivity_tracker'];

  return (
    <div className="bg-white/5 backdrop-blur-lg rounded-3xl border border-white/10 p-6 md:p-8 shadow-2xl transition-all duration-300 hover:shadow-indigo-500/5 hover:border-white/20">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-xl md:text-2xl font-bold bg-gradient-to-r from-indigo-200 via-purple-200 to-pink-200 bg-clip-text text-transparent">
            AI Agent Controller
          </h2>
          <p className="text-sm text-slate-400 mt-1">Activate or deactivate models per camera stream</p>
        </div>
        <button
          onClick={fetchData}
          className="p-2 bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-300 rounded-lg border border-indigo-500/20 transition-all active:scale-95"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.253 8H18" />
          </svg>
        </button>
      </div>

      {cameras.length === 0 ? (
        <div className="text-center py-12 bg-slate-900/40 rounded-2xl border border-white/5">
          <p className="text-slate-400">No cameras registered yet.</p>
          <p className="text-xs text-slate-500 mt-2">Use the &quot;Add Camera&quot; form to onboard your first stream.</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse font-sans">
            <thead>
              <tr className="border-b border-white/10 text-slate-300">
                <th className="pb-4 font-semibold">Camera</th>
                <th className="pb-4 font-semibold text-center">Intrusion Detection</th>
                <th className="pb-4 font-semibold text-center">Productivity Tracker</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {cameras.map((camera) => (
                <tr key={camera.camera_id} className="group hover:bg-white/5 transition-colors">
                  <td className="py-4 pr-4">
                    <div className="font-semibold text-white group-hover:text-indigo-300 transition-colors">
                      {camera.name}
                    </div>
                    <div className="text-xs text-slate-400 font-mono truncate max-w-[200px]" title={camera.rtsp_url}>
                      {camera.rtsp_url}
                    </div>
                  </td>
                  {agentsList.map((agent) => {
                    const active = isEnabled(camera.camera_id, agent);
                    const key = `${camera.camera_id}-${agent}`;
                    const isToggling = toggling === key;
                    return (
                      <td key={agent} className="py-4 text-center">
                        <div className="flex items-center justify-center">
                          <button
                            disabled={isToggling}
                            onClick={() => handleToggle(camera.camera_id, agent, active)}
                            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-all duration-300 outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-slate-900 ${
                              active
                                ? 'bg-gradient-to-r from-indigo-500 to-purple-600 shadow-lg shadow-indigo-500/20'
                                : 'bg-slate-700'
                            } ${isToggling ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                          >
                            <span
                              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform duration-300 ${
                                active ? 'translate-x-6' : 'translate-x-1'
                              }`}
                            />
                          </button>
                        </div>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
