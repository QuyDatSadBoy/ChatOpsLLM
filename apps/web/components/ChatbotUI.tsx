'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { ChatSocket } from '@/lib/socket';
import ChatInput from './ChatInput';
import MessageBubble from './MessageBubble';
import SettingsPanel from './SettingsPanel';

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  streaming?: boolean;
}

export default function ChatbotUI() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [model, setModel] = useState('gemini-flash');
  const [showSettings, setShowSettings] = useState(false);
  const socketRef = useRef<ChatSocket | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    socketRef.current = new ChatSocket({
      onToken: (token) => {
        setMessages((prev) => {
          const last = prev[prev.length - 1];
          if (last?.role === 'assistant' && last.streaming) {
            return [...prev.slice(0, -1), { ...last, content: last.content + token }];
          }
          return [...prev, { role: 'assistant', content: token, streaming: true }];
        });
      },
      onDone: () => {
        setIsStreaming(false);
        setMessages((prev) => {
          const last = prev[prev.length - 1];
          if (last?.streaming) {
            return [...prev.slice(0, -1), { ...last, streaming: false }];
          }
          return prev;
        });
      },
      onError: (err) => {
        setIsStreaming(false);
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: `⚠️ Error: ${err}` },
        ]);
      },
    });

    socketRef.current.connect().catch(() => {
      /* handled via onError */
    });

    return () => socketRef.current?.disconnect();
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = useCallback(
    (text: string) => {
      if (!text.trim() || isStreaming) return;

      const history: Array<[string, string]> = messages
        .filter((_, i, arr) => i % 2 === 0 && i + 1 < arr.length)
        .map((m, i) => [m.content, messages[i * 2 + 1]?.content ?? '']);

      setMessages((prev) => [...prev, { role: 'user', content: text }]);
      setIsStreaming(true);

      socketRef.current?.send({
        latest_prompt: text,
        message: "",
        history,
        model,
        prompt_type: 'enhance_prompt',
      });
    },
    [isStreaming, messages, model],
  );

  return (
    <div className="flex h-screen flex-col bg-slate-50">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-3 shadow-sm">
        <h1 className="text-lg font-semibold text-indigo-600">ChatOpsLLM</h1>
        <button
          onClick={() => setShowSettings((s) => !s)}
          className="rounded-lg px-3 py-1.5 text-sm text-slate-500 hover:bg-slate-100"
        >
          Settings
        </button>
      </header>

      {showSettings && (
        <SettingsPanel model={model} onModelChange={setModel} onClose={() => setShowSettings(false)} />
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
        {messages.length === 0 && (
          <p className="text-center text-slate-400 mt-20">Send a message to start chatting.</p>
        )}
        {messages.map((msg, i) => (
          <MessageBubble key={i} message={msg} />
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <ChatInput onSend={handleSend} disabled={isStreaming} />
    </div>
  );
}
