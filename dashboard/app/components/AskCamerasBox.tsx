'use client';

import { useState, useEffect, useRef } from 'react';

interface ChatMessage {
  type: 'user' | 'system' | 'bot';
  content: string;
  timestamp?: string;
  title?: string;
  matched_events?: number;
}

export default function AskCamerasBox() {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const chatEndRef = useRef<HTMLDivElement | null>(null);
  
  // Initialize with the exact conversation from the mock image
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([
    {
      type: 'user',
      content: 'Show me any movement detected at the Loading Dock B after 10 PM yesterday.',
    },
    {
      type: 'system',
      content: 'Searching historical logs for Loading Dock B. I found 1 event matching your criteria:',
    },
    {
      type: 'bot',
      title: 'Intrusion Detected',
      timestamp: '22:14:05 • 03/24/2024',
      content: 'Large object movement detected at perimeter fence near Loading Dock B. Motion classified as "Humanoid".',
    }
  ]);

  const isFirstRender = useRef(true);

  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8333';

  const handleAsk = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    const userQ = question.trim();
    setQuestion('');
    setLoading(true);
    setError('');

    // Append user question
    setChatHistory((prev) => [
      ...prev,
      { type: 'user', content: userQ }
    ]);

    try {
      const response = await fetch(`${API_URL}/api/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: userQ }),
      });

      const data = await response.json();

      if (response.ok) {
        setChatHistory((prev) => [
          ...prev,
          {
            type: 'system',
            content: `Searching historical logs. I found ${data.matched_events} event(s) matching your criteria:`,
          },
          {
            type: 'bot',
            title: data.matched_events > 0 ? 'Event Found' : 'No Events Found',
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }) + ' • ' + new Date().toLocaleDateString(),
            content: data.answer,
            matched_events: data.matched_events,
          }
        ]);
      } else {
        setError(data.detail || 'Failed to query the reasoning layer.');
      }
    } catch (err) {
      console.error('Failed to ask cameras:', err);
      setError('Could not connect to reasoning layer.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-3xl border border-[#e2e8f0] p-6 shadow-sm flex flex-col space-y-5">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-[#eef2ff] text-[#3b2fc9] rounded-2xl border border-[#e0e7ff]">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 21l-.813-5.096L3 15l5.096-.813L9 9l.813 5.187L15 15l-5.187.813zM18 10.5l-.5 3-.5-3-3-.5 3-.5.5-3 .5 3 3 .5-3 .5zM19.5 19.5l-.25 1.5-.25-1.5-1.5-.25 1.5-.25.25-1.5.25 1.5 1.5.25-1.5.25z" />
            </svg>
          </div>
          <div>
            <h2 className="text-[20px] font-bold text-[#0f172a] tracking-tight">
              Ask Your Cameras
            </h2>
            <p className="text-[13px] text-[#64748b] font-medium mt-0.5">Semantic query across your edge network</p>
          </div>
        </div>

        <button className="flex items-center space-x-1.5 text-[13px] font-bold text-[#64748b] hover:text-[#0f172a] transition-colors">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>History</span>
        </button>
      </div>

      {/* Chat History Area */}
      <div className="space-y-4 max-h-[350px] overflow-y-auto pr-1">
        {chatHistory.map((msg, idx) => {
          if (msg.type === 'user') {
            return (
              <div key={idx} className="flex justify-end">
                <div className="bg-[#eef2ff] text-[#1e1b4b] text-[13px] font-semibold px-5 py-3 rounded-2xl max-w-[85%] leading-relaxed border border-[#e0e7ff]">
                  {msg.content}
                </div>
              </div>
            );
          } else if (msg.type === 'system') {
            const hasTargetPhrase = msg.content.includes('Loading Dock B');
            return (
              <div key={idx} className="flex items-center space-x-2 text-[12px] font-bold text-[#64748b] px-1">
                <span className="p-1 bg-[#3b2fc9] text-white rounded-full flex items-center justify-center w-5 h-5">
                  <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
                  </svg>
                </span>
                <span>
                  {hasTargetPhrase ? (
                    <>
                      {msg.content.split('Loading Dock B')[0]}
                      <strong className="text-[#0f172a]">Loading Dock B</strong>
                      {msg.content.split('Loading Dock B')[1] || ''}
                    </>
                  ) : (
                    msg.content
                  )}
                </span>
              </div>
            );
          } else {
            return (
              <div key={idx} className="bg-[#f8f9fc] border border-[#e2e8f0] rounded-2xl p-4 space-y-3">
                <div className="flex justify-between items-center">
                  <div className="flex items-center space-x-2">
                    <span className="p-1 bg-[#eef2ff] text-[#3b2fc9] rounded border border-[#e0e7ff]">
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2.5">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                      </svg>
                    </span>
                    <span className="text-[13px] font-bold text-[#0f172a]">{msg.title}</span>
                  </div>
                  <span className="text-[10px] font-bold text-[#94a3b8] font-mono">{msg.timestamp}</span>
                </div>
                <p className="text-[12.5px] text-[#475569] leading-relaxed font-semibold">
                  {msg.content}
                </p>
                <div className="flex space-x-3 text-[11.5px] font-bold text-[#3b2fc9]">
                  <button className="hover:underline">Play Clip</button>
                  <button className="hover:underline">Export Log</button>
                </div>
              </div>
            );
          }
        })}
        <div ref={chatEndRef} />
      </div>

      {/* Input box */}
      <form onSubmit={handleAsk} className="relative border border-[#e2e8f0] rounded-2xl p-3 bg-[#f8f9fc]">
        <textarea
          rows={3}
          placeholder="Ask anything about your video feeds... (e.g., 'Were there any intruders detected near the parking lot between 2 AM and 4 AM?')"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          disabled={loading}
          className="w-full bg-transparent resize-none outline-none text-[13px] text-[#0f172a] placeholder-[#94a3b8] font-semibold leading-relaxed"
        />
        <div className="flex justify-end items-center pt-2">
          <button
            type="submit"
            disabled={loading || !question.trim()}
            className="bg-[#3b2fc9] hover:bg-[#2e24a8] text-white font-bold px-4 py-2 rounded-xl transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5 text-[13px]"
          >
            <span>{loading ? 'Thinking...' : 'Ask'}</span>
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="3">
              <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 10.5L12 3m0 0l7.5 7.5M12 3v18" />
            </svg>
          </button>
        </div>
      </form>

      {error && (
        <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-[12px] font-semibold">
          {error}
        </div>
      )}

      {/* Powered by footer text */}
      <div className="text-center text-[11px] text-[#94a3b8] font-bold italic pt-1">
        Powered by localized Multi-Modal LLM. Video data remains on-site.
      </div>
    </div>
  );
}
