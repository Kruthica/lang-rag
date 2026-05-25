import { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { Send } from 'lucide-react';
import { useChat } from '../context/ChatContext';
import EmptyState from '../components/EmptyState';
import MessageBubble from '../components/MessageBubble';
import TypingLoader from '../components/TypingLoader';

export default function ChatPage() {
  const { messages, sendMessage, isLoading } = useChat();
  const [input, setInput] = useState('');
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const submit = (e) => {
    e.preventDefault();
    const q = input.trim();
    if (!q) return;
    setInput('');
    sendMessage(q);
  };

  const lastMessage = messages[messages.length - 1];

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <div className="flex-1 overflow-y-auto px-4 py-6">
        {messages.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="mx-auto max-w-3xl space-y-6">
            {messages.map((msg) => (
              <MessageBubble
                key={msg.id}
                message={msg}
                isStreaming={
                  isLoading && msg.id === lastMessage?.id && msg.role === 'assistant'
                }
              />
            ))}
            {isLoading && lastMessage?.role !== 'assistant' && <TypingLoader />}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      <form
        onSubmit={submit}
        className="border-t border-surface-border bg-surface-elevated/80 p-4 backdrop-blur-xl"
      >
        <div className="mx-auto flex max-w-3xl gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about your documents…"
            disabled={isLoading}
            className="flex-1 rounded-xl border border-surface-border bg-surface px-4 py-3 text-sm outline-none ring-accent/0 transition focus:border-accent/50 focus:ring-2 focus:ring-accent/30 disabled:opacity-50"
          />
          <motion.button
            type="submit"
            disabled={isLoading || !input.trim()}
            whileTap={{ scale: 0.95 }}
            className="flex items-center justify-center rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 px-4 py-3 text-white shadow-lg shadow-indigo-500/20 disabled:opacity-40"
          >
            <Send className="h-5 w-5" />
          </motion.button>
        </div>
      </form>
    </div>
  );
}
