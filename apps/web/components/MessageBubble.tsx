'use client';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Message } from './ChatbotUI';
import { clsx } from 'clsx';

interface Props {
  message: Message;
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === 'user';

  return (
    <div className={clsx('flex', isUser ? 'justify-end' : 'justify-start')}>
      <div
        className={clsx(
          'max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-sm',
          isUser
            ? 'bg-indigo-600 text-white rounded-br-sm'
            : 'bg-white text-slate-800 border border-slate-200 rounded-bl-sm',
          message.streaming && 'animate-pulse',
        )}
      >
        {isUser ? (
          <span>{message.content}</span>
        ) : (
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
        )}
      </div>
    </div>
  );
}
