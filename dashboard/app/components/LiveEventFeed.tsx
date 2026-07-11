'use client';

import { useEffect, useState } from 'react';

interface EventMetadata {
  box?: number[];
  zone?: string;
  track_id?: number | string;
  [key: string]: unknown;
}

interface EventData {
  id?: number;
  camera_id: string;
  agent: string;
  event_type: string;
  confidence: number;
  timestamp: string;
  metadata?: EventMetadata;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8333';

export default function LiveEventFeed() {
  const [events, setEvents] = useState<EventData[]>([]);
  const [status, setStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting');

  const getWsUrl = (httpUrl: string) => {
    const url = new URL(httpUrl);
    url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
    url.pathname = '/ws/live';
    return url.toString();
  };

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const response = await fetch(`${API_URL}/api/events?limit=50`);
        if (response.ok) {
          const data = await response.json();
          setEvents(data);
        }
      } catch (err) {
        console.error('Failed to fetch event history:', err);
      }
    };

    fetchHistory();

    let ws: WebSocket | null = null;
    let reconnectTimeout: NodeJS.Timeout;

    const connectWS = () => {
      setStatus('connecting');
      const wsUrl = getWsUrl(API_URL);
      console.log(`Connecting to Live WS: ${wsUrl}`);
      
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setStatus('connected');
        console.log('Live WS Connected');
      };

      ws.onmessage = (messageEvent) => {
        try {
          const newEvent: EventData = JSON.parse(messageEvent.data);
          setEvents((prev) => [newEvent, ...prev.slice(0, 99)]);
        } catch (err) {
          console.error('Failed to parse WS message:', err);
        }
      };

      ws.onclose = () => {
        setStatus('disconnected');
        console.log('Live WS Disconnected. Reconnecting in 3s...');
        reconnectTimeout = setTimeout(connectWS, 3000);
      };

      ws.onerror = (err) => {
        console.error('WS Error:', err);
        ws?.close();
      };
    };

    connectWS();

    return () => {
      if (ws) {
        ws.close();
      }
      clearTimeout(reconnectTimeout);
    };
  }, []);

  const getEventStyle = (eventType: string) => {
    switch (eventType) {
      case 'intrusion':
        return {
          cardBg: 'bg-[#fee2e2]/40 border-l-[#ef4444]',
          badgeBg: 'bg-[#fecaca] text-[#dc2626]',
          badgeText: 'INTRUSION'
        };
      case 'active':
        return {
          cardBg: 'bg-[#e0e7ff]/40 border-l-[#3b2fc9]',
          badgeBg: 'bg-[#e0e7ff] text-[#3b2fc9]',
          badgeText: 'ACTIVE'
        };
      case 'idle':
        return {
          cardBg: 'bg-[#f1f5f9] border-l-[#64748b]',
          badgeBg: 'bg-[#e2e8f0] text-[#475569]',
          badgeText: 'IDLE'
        };
      case 'away':
      default:
        return {
          cardBg: 'bg-[#f8f9fc] border-l-[#cbd5e1] opacity-75',
          badgeBg: 'bg-[#f1f5f9] text-[#64748b]',
          badgeText: 'AWAY'
        };
    }
  };

  return (
    <div className="bg-white rounded-3xl border border-[#e2e8f0] p-6 shadow-sm flex flex-col h-[520px]">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-[20px] font-bold text-[#0f172a] tracking-tight">
            Live Event Feed
          </h2>
        </div>
        <div className="flex items-center space-x-1.5">
          <span className={`h-2 w-2 rounded-full ${
            status === 'connected' ? 'bg-[#22c55e]' :
            status === 'connecting' ? 'bg-amber-400' : 'bg-rose-500'
          }`} />
          <span className="text-[11px] font-bold text-[#0f172a] uppercase tracking-wider">
            {status}
          </span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto pr-1 space-y-4 min-h-0">
        {events.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-8 bg-[#f8f9fc] rounded-2xl border border-[#e2e8f0]">
            <p className="text-[#64748b] text-[13px] font-medium">Listening for live events...</p>
          </div>
        ) : (
          events.map((event, idx) => {
            const styles = getEventStyle(event.event_type);
            const timeStr = new Date(event.timestamp).toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
              second: '2-digit',
              hour12: false
            });

            return (
              <div
                key={event.id || idx}
                className={`p-4 rounded-xl border-l-[3.5px] border border-y-[#e2e8f0] border-r-[#e2e8f0] ${styles.cardBg} transition-all duration-300`}
              >
                <div className="flex justify-between items-start mb-2.5">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${styles.badgeBg}`}>
                    {styles.badgeText}
                  </span>
                  <span className="text-[10px] font-bold text-[#64748b] font-mono">
                    {timeStr}
                  </span>
                </div>
                
                <div className="flex justify-between items-end">
                  <div className="space-y-0.5">
                    <div className="text-[13px] text-[#0f172a] font-medium">
                      Camera: <span className="font-bold">{event.camera_id}</span>
                    </div>
                    <div className="text-[12px] text-[#64748b] font-medium">
                      Agent: <span className="italic text-[#3b2fc9] font-mono">{event.agent}</span>
                    </div>
                  </div>
                  <div className="text-[11px] font-bold text-[#22c55e] font-sans">
                    {(event.confidence * 100).toFixed(0)}% Match
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      <div className="pt-4 border-t border-[#f1f5f9] text-center mt-3">
        <button className="text-[13px] font-bold text-[#3b2fc9] hover:underline">
          View All Alerts
        </button>
      </div>
    </div>
  );
}
