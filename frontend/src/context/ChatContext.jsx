import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from 'react';

import toast from 'react-hot-toast';

import {
  askQuestion,
  askQuestionStream,
  deleteDocument,
  listDocuments,
  uploadFiles,
} from '../services/api';

const ChatContext = createContext(null);

export function ChatProvider({ children }) {
  const [messages, setMessages] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [useStreaming, setUseStreaming] = useState(true);

  const refreshDocuments = useCallback(async () => {
    try {
      const docs = await listDocuments();
      setDocuments(docs);
    } catch {
      toast.error('Could not load documents');
    }
  }, []);

  useEffect(() => {
    refreshDocuments();
  }, [refreshDocuments]);

  const handleUpload = async (files) => {
    if (!files?.length) return;

    setUploadProgress(0);

    try {
      const result = await uploadFiles(files, setUploadProgress);

      if (result.uploaded?.length) {
        toast.success(`Indexed ${result.uploaded.length} file(s)`);
      }

      if (result.skipped?.length) {
        result.skipped.forEach((s) => toast.error(s));
      }

      await refreshDocuments();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Upload failed');
    } finally {
      setUploadProgress(0);
    }
  };

  const handleDeleteDocument = async (id) => {
    try {
      await deleteDocument(id);
      toast.success('Document removed');
      await refreshDocuments();
    } catch {
      toast.error('Delete failed');
    }
  };

  const clearChat = () => setMessages([]);

  const sendMessage = async (question, { regenerate = false } = {}) => {
    if (!question.trim() || isLoading) return;

    const history = regenerate
      ? messages
          .slice(0, -1)
          .map((m) => ({ role: m.role, content: m.content }))
      : messages.map((m) => ({
          role: m.role,
          content: m.content,
        }));

    if (!regenerate) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'user',
          content: question,
          id: crypto.randomUUID(),
        },
      ]);
    }

    setIsLoading(true);

    const assistantId = crypto.randomUUID();

    const appendAssistant = (patch) => {
      setMessages((prev) => {
        const existing = prev.find((m) => m.id === assistantId);

        if (existing) {
          return prev.map((m) =>
            m.id === assistantId
              ? { ...m, ...patch }
              : m
          );
        }

        return [
          ...prev,
          {
            role: 'assistant',
            id: assistantId,
            content: '',
            ...patch,
          },
        ];
      });
    };

    try {
      if (useStreaming) {
        let content = '';

        askQuestionStream(question, history, {
          onSources: () => {
            // Ignore sources
          },

          onToken: (token) => {
            content += token;
            appendAssistant({ content });
          },

          onDone: () => {
            setIsLoading(false);
          },

          onError: () => {
            toast.error('Something went wrong');
            setIsLoading(false);
          },
        });

        return;
      }

      const response = await askQuestion(question, history);

      appendAssistant({
        content: response.answer,
      });
    } catch (err) {
      toast.error(
        err.response?.data?.detail || 'Request failed'
      );
    } finally {
      if (!useStreaming) {
        setIsLoading(false);
      }
    }
  };

  return (
    <ChatContext.Provider
      value={{
        messages,
        documents,
        isLoading,
        uploadProgress,
        sidebarOpen,
        settingsOpen,
        useStreaming,

        setSidebarOpen,
        setSettingsOpen,
        setUseStreaming,

        sendMessage,
        clearChat,
        handleUpload,
        handleDeleteDocument,
        refreshDocuments,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export const useChat = () => useContext(ChatContext);