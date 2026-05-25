import { Settings, Trash2, RotateCcw } from 'lucide-react';
import { useChat } from '../context/ChatContext';

export default function Navbar() {
  const { clearChat, regenerateLast, setSettingsOpen, messages, isLoading } = useChat();
  const hasAssistant = messages.some((m) => m.role === 'assistant');

  return (
    <header className="flex items-center justify-between border-b border-surface-border px-4 py-3 glass">
      <h1 className="text-sm font-medium text-gray-300">Document Chat</h1>
      <div className="flex items-center gap-1">
        <button
          type="button"
          disabled={!hasAssistant || isLoading}
          onClick={regenerateLast}
          className="rounded-lg p-2 text-gray-400 hover:bg-surface-border hover:text-white disabled:opacity-40"
          title="Regenerate"
        >
          <RotateCcw className="h-4 w-4" />
        </button>
        <button
          type="button"
          onClick={clearChat}
          className="rounded-lg p-2 text-gray-400 hover:bg-surface-border hover:text-white"
          title="Clear chat"
        >
          <Trash2 className="h-4 w-4" />
        </button>
        <button
          type="button"
          onClick={() => setSettingsOpen(true)}
          className="rounded-lg p-2 text-gray-400 hover:bg-surface-border hover:text-white"
          title="Settings"
        >
          <Settings className="h-4 w-4" />
        </button>
      </div>
    </header>
  );
}
