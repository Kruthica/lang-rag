import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';
import { useChat } from '../context/ChatContext';

export default function SettingsModal() {
  const { settingsOpen, setSettingsOpen, useStreaming, setUseStreaming } = useChat();

  return (
    <AnimatePresence>
      {settingsOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
          onClick={() => setSettingsOpen(false)}
        >
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.95, opacity: 0 }}
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-md rounded-2xl glass p-6 shadow-2xl"
          >
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold">Settings</h2>
              <button
                type="button"
                onClick={() => setSettingsOpen(false)}
                className="rounded-lg p-1 hover:bg-surface-border"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <label className="flex cursor-pointer items-center justify-between gap-4 rounded-lg border border-surface-border p-4">
              <div>
                <p className="font-medium">Streaming responses</p>
                <p className="text-xs text-gray-500">Show tokens as they arrive (SSE)</p>
              </div>
              <input
                type="checkbox"
                checked={useStreaming}
                onChange={(e) => setUseStreaming(e.target.checked)}
                className="h-5 w-5 accent-indigo-500"
              />
            </label>
            <p className="mt-4 text-xs text-gray-500">
              API: {import.meta.env.VITE_API_URL || '/api (proxied to :8000)'}
            </p>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
