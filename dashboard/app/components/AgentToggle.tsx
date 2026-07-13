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
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setError(null);
      const [cRes, aRes] = await Promise.all([
        fetch(`${API_URL}/api/cameras`),
        fetch(`${API_URL}/api/agents`)
      ]);
      if (cRes.ok && aRes.ok) {
        const cData = await cRes.json();
        const aData = await aRes.json();
        setCameras(cData);
        setConfigs(aData);
      } else {
        setError('Failed to fetch camera configurations from server.');
      }
    } catch (err) {
      console.error('Failed to fetch data for AgentToggle:', err);
      setError('Could not connect to API server.');
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
    setError(null);
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
      } else {
        const errData = await response.json().catch(() => ({}));
        setError(errData.detail || 'Failed to update agent toggle state.');
      }
    } catch (err) {
      console.error('Failed to toggle agent:', err);
      setError('Connection error: Failed to toggle agent.');
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
      <div className="flex flex-col items-center justify-center p-8 bg-white rounded-3xl border border-[#e2e8f0] shadow-sm min-h-[200px] gap-3">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#4f46e5]"></div>
        <p className="text-[12px] text-[#64748b] font-medium text-center">
          Loading camera configuration...<br/>
          <span className="text-[10px] opacity-75">(Render free instances may take 30-60s to wake up)</span>
        </p>
      </div>
    );
  }

  const agentsList = ['intrusion_detection', 'productivity_tracker'];

  return (
    <div className="bg-white rounded-3xl border border-[#e2e8f0] p-6 shadow-sm">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-[20px] font-bold text-[#0f172a] tracking-tight">
            AI Agent Controller
          </h2>
          <p className="text-[13px] text-[#64748b] font-medium mt-0.5">Activate or deactivate models per camera stream</p>
        </div>
        <button
          onClick={fetchData}
          className="p-2.5 bg-[#f1f5f9] hover:bg-[#e2e8f0] text-[#0f172a] rounded-xl transition-all active:scale-95"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
          </svg>
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-[12.5px] font-semibold">
          {error}
        </div>
      )}

      {cameras.length === 0 ? (
        <div className="text-center py-10 bg-[#f8f9fc] rounded-2xl border border-[#e2e8f0]">
          <p className="text-[#64748b] text-[13px] font-medium">No cameras registered yet.</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse font-sans">
            <thead>
              <tr className="border-b border-[#e2e8f0] text-[#475569] text-[13px] font-bold">
                <th className="pb-3 pr-4 font-bold">Camera</th>
                <th className="pb-3 text-center font-bold">Intrusion</th>
                <th className="pb-3 text-center font-bold">Productivity</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#f1f5f9]">
              {cameras.map((camera) => (
                <tr key={camera.camera_id} className="group transition-colors">
                  <td className="py-4 pr-4">
                    <div className="font-bold text-[#0f172a] text-[14px]">
                      {camera.name}
                    </div>
                    <div className="text-[12px] text-[#94a3b8] font-mono mt-0.5 truncate max-w-[200px]" title={camera.rtsp_url}>
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
                            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-all duration-300 outline-none ${
                              active
                                ? 'bg-[#3b2fc9]'
                                : 'bg-[#e2e8f0]'
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
