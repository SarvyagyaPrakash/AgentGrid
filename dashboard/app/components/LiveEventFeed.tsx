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

  // Helper to convert HTTP to WS protocol
  const getWsUrl = (httpUrl: string) => {
    const url = new URL(httpUrl);
    url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
    url.pathname = '/ws/live';
    return url.toString();
  };

  useEffect(() => {
    // 1. Fetch initial historical events
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

    // 2. Connect to WebSocket
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
          // Prepend new event
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

  // Style logic based on event type
  const getEventStyle = (eventType: string) => {
    switch (eventType) {
      case 'intrusion':
        return {
          cardBg: 'bg-red-500/10 border-red-500/20 hover:border-red-500/30',
          badgeBg: 'bg-red-500/20 text-red-300 border-red-500/30',
          text: 'text-red-200'
        };
      case 'active':
        return {
          cardBg: 'bg-blue-500/10 border-blue-500/20 hover:border-blue-500/30',
          badgeBg: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
          text: 'text-blue-200'
        };
      case 'idle':
        return {
          cardBg: 'bg-slate-500/10 border-slate-500/20 hover:border-slate-500/30',
          badgeBg: 'bg-slate-500/20 text-slate-300 border-slate-500/30',
          text: 'text-slate-200'
        };
      case 'away':
      default:
        return {
          cardBg: 'bg-slate-900/30 border-slate-800 hover:border-slate-700 opacity-60',
          badgeBg: 'bg-slate-800 text-slate-400 border-slate-700',
          text: 'text-slate-400'
        };
    }
  };

  return (
    <div className="bg-white/5 backdrop-blur-lg rounded-3xl border border-white/10 p-6 md:p-8 shadow-2xl transition-all duration-300 flex flex-col h-[520px]">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h2 className="text-xl md:text-2xl font-bold bg-gradient-to-r from-teal-200 via-emerald-200 to-indigo-200 bg-clip-text text-transparent">
            Live Event Feed
          </h2>
          <p className="text-sm text-slate-400 mt-1">Real-time alerts processed at edge</p>
        </div>
        <div className="flex items-center space-x-2">
          <span className={`h-2.5 w-2.5 rounded-full ${
            status === 'connected' ? 'bg-emerald-400 animate-pulse' :
            status === 'connecting' ? 'bg-amber-400 animate-pulse' : 'bg-rose-500'
          }`} />
          <span className="text-xs font-mono text-slate-400 uppercase tracking-wider">
            {status}
          </span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto pr-2 space-y-3 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
        {events.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-8 bg-slate-900/20 rounded-2xl border border-white/5">
            <svg className="w-8 h-8 text-slate-600 animate-pulse mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
            <p className="text-slate-500 text-sm">Listening for live events...</p>
          </div>
        ) : (
          events.map((event, idx) => {
            const styles = getEventStyle(event.event_type);
            const hasTrackId = event.metadata?.track_id !== undefined && event.metadata?.track_id !== null;
            const trackId = event.metadata?.track_id;

            return (
              <div
                key={event.id || idx}
                className={`p-4 rounded-2xl border transition-all duration-300 ${styles.cardBg} flex flex-col sm:flex-row sm:items-center justify-between gap-3`}
              >
                <div className="flex flex-col gap-1.5">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${styles.badgeBg}`}>
                      {event.event_type.toUpperCase()}
                    </span>
                    {hasTrackId && (
                      <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-violet-500/20 text-violet-300 border border-violet-500/30">
                        Person #{trackId}
                      </span>
                    )}
                    <span className="text-xs text-slate-400 font-medium">
                      Camera: <span className="text-slate-200 font-semibold">{event.camera_id}</span>
                    </span>
                  </div>
                  <div className="text-sm font-medium text-slate-300">
                    Agent: <span className="font-mono text-indigo-300 text-xs">{event.agent}</span>
                    {event.metadata?.zone && (
                      <span className="text-xs text-slate-400">
                        {' '}in <span className="text-slate-200 font-semibold">{event.metadata.zone}</span>
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex flex-row sm:flex-col items-center sm:items-end justify-between sm:justify-center text-xs text-slate-400 font-mono gap-1">
                  <span className="text-indigo-400 font-semibold">
                    {(event.confidence * 100).toFixed(0)}% Match
                  </span>
                  <span>
                    {new Date(event.timestamp).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                      second: '2-digit',
                    })}
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
