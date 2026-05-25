import { motion, AnimatePresence } from 'framer-motion';
import { PanelLeftClose, PanelLeft } from 'lucide-react';
import { useChat } from '../context/ChatContext';
import UploadPanel from './UploadPanel';

export default function Sidebar() {
  const { sidebarOpen, setSidebarOpen } = useChat();

  return (
    <>
      <AnimatePresence mode="wait">
        {sidebarOpen && (
          <motion.aside
            initial={{ x: -280, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: -280, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
            className="fixed inset-y-0 left-0 z-30 flex w-72 flex-col border-r border-surface-border bg-surface-elevated/95 backdrop-blur-xl md:relative md:z-0"
          >
            <div className="flex items-center justify-between border-b border-surface-border p-4">
              <span className="bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-lg font-bold text-transparent">
                RAG Studio
              </span>
              <button
                type="button"
                className="rounded-lg p-2 text-gray-400 hover:bg-surface-border md:hidden"
                onClick={() => setSidebarOpen(false)}
              >
                <PanelLeftClose className="h-5 w-5" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto">
              <UploadPanel />
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      {!sidebarOpen && (
        <button
          type="button"
          className="fixed left-4 top-4 z-20 rounded-lg glass p-2 md:absolute"
          onClick={() => setSidebarOpen(true)}
        >
          <PanelLeft className="h-5 w-5" />
        </button>
      )}
    </>
  );
}
