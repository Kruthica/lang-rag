import { useState } from 'react';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Bot, Copy, Check, User } from 'lucide-react';
import toast from 'react-hot-toast';

export default function MessageBubble({ message, isStreaming }) {
  const isUser = message.role === 'user';
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    await navigator.clipboard.writeText(message.content || '');
    setCopied(true);
    toast.success('Copied');
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}
    >
      <div
        className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${
          isUser ? 'bg-indigo-600/30' : 'bg-gradient-to-br from-indigo-500/30 to-purple-500/20'
        }`}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4 text-accent-glow" />}
      </div>

      <motion.div
        className={`max-w-[85%] rounded-2xl px-4 py-3 md:max-w-[75%] ${
          isUser
            ? 'bg-indigo-600/20 border border-indigo-500/30'
            : 'glass shadow-lg shadow-black/20'
        }`}
      >
        {isUser ? (
          <p className="text-sm leading-relaxed text-gray-100">{message.content}</p>
        ) : (
          <>
            <div className="prose prose-invert prose-sm max-w-none">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  code({ inline, className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || '');

                    if (!inline && match) {
                      return (
                        <SyntaxHighlighter
                          style={oneDark}
                          language={match[1]}
                          PreTag="div"
                          className="rounded-lg !text-xs"
                          {...props}
                        >
                          {String(children).replace(/\n$/, '')}
                        </SyntaxHighlighter>
                      );
                    }

                    return (
                      <code
                        className="rounded bg-surface px-1 py-0.5 text-accent-glow"
                        {...props}
                      >
                        {children}
                      </code>
                    );
                  },
                }}
              >
                {message.content || (isStreaming ? '…' : '')}
              </ReactMarkdown>
            </div>

            {!isUser && message.content && (
              <button
                type="button"
                onClick={copy}
                className="mt-2 flex items-center gap-1 text-xs text-gray-500 hover:text-gray-300"
              >
                {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                Copy
              </button>
            )}
          </>
        )}
      </motion.div>
    </motion.div>
  );
}