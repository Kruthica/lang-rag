import { useCallback, useState } from 'react';
import { motion } from 'framer-motion';
import { CloudUpload, File, Trash2 } from 'lucide-react';
import { useChat } from '../context/ChatContext';

const MAX_MB = 50;

export default function UploadPanel() {
  const { handleUpload, uploadProgress, documents, handleDeleteDocument } = useChat();
  const [dragOver, setDragOver] = useState(false);
  const [pending, setPending] = useState([]);

  const validate = (files) => {
    const valid = [];
    for (const f of files) {
      if (!f.name.toLowerCase().endsWith('.pdf')) continue;
      if (f.size > MAX_MB * 1024 * 1024) continue;
      valid.push(f);
    }
    return valid;
  };

  const onFiles = useCallback(
    async (fileList) => {
      const files = validate(Array.from(fileList));
      if (!files.length) return;
      setPending(files.map((f) => f.name));
      await handleUpload(files);
      setPending([]);
    },
    [handleUpload]
  );

  const onDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    onFiles(e.dataTransfer.files);
  };

  return (
    <div className="space-y-4 p-4">
      <motion.label
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        whileHover={{ scale: 1.01 }}
        className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-6 transition-colors ${
          dragOver ? 'border-accent bg-accent/10' : 'border-surface-border hover:border-accent/50'
        }`}
      >
        <input
          type="file"
          accept=".pdf,application/pdf"
          multiple
          className="hidden"
          onChange={(e) => onFiles(e.target.files)}
        />
        <CloudUpload className="mb-2 h-8 w-8 text-accent-glow" />
        <span className="text-sm font-medium">Drop PDFs or click to upload</span>
        <span className="mt-1 text-xs text-gray-500">PDF only · max {MAX_MB}MB</span>
      </motion.label>

      {uploadProgress > 0 && (
        <div className="h-1.5 overflow-hidden rounded-full bg-surface-border">
          <motion.div
            className="h-full bg-accent"
            initial={{ width: 0 }}
            animate={{ width: `${uploadProgress}%` }}
          />
        </div>
      )}

      {pending.length > 0 && (
        <p className="text-xs text-gray-400">Uploading: {pending.join(', ')}</p>
      )}

      <motion.div className="space-y-2">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500">
          Documents ({documents.length})
        </h3>
        {documents.length === 0 ? (
          <p className="text-xs text-gray-500">No documents yet</p>
        ) : (
          documents.map((doc) => (
            <motion.div
              key={doc.id}
              layout
              className="flex items-center gap-2 rounded-lg glass px-3 py-2 text-sm"
            >
              <File className="h-4 w-4 shrink-0 text-accent-glow" />
              <div className="min-w-0 flex-1">
                <p className="truncate font-medium">{doc.filename}</p>
                <p className="text-[10px] text-gray-500">{doc.chunk_count} chunks</p>
              </div>
              <button
                type="button"
                onClick={() => handleDeleteDocument(doc.id)}
                className="rounded p-1 text-gray-500 hover:bg-red-500/20 hover:text-red-400"
                aria-label="Delete"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </motion.div>
          ))
        )}
      </motion.div>
    </div>
  );
}
