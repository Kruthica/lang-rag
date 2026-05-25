import { motion } from 'framer-motion';
import { FileText } from 'lucide-react';

export default function SourceCard({ source, index, highlighted }) {
  const scorePercent = Math.round((source.score || 0) * 100);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className={`rounded-lg border p-3 text-xs transition-colors ${
        highlighted
          ? 'border-accent/60 bg-accent/10'
          : 'border-surface-border bg-surface/50'
      }`}
    >
      <motion.div className="mb-1 flex items-center justify-between gap-2">
        <span className="flex items-center gap-1.5 font-medium text-accent-glow">
          <FileText className="h-3.5 w-3.5" />
          {source.filename}
          {source.page != null && (
            <span className="text-gray-500">· p.{source.page}</span>
          )}
        </span>
        <span className="rounded-full bg-surface-elevated px-2 py-0.5 text-[10px] text-gray-400">
          {scorePercent}% match
        </span>
      </motion.div>
      <p className="line-clamp-3 text-gray-400">{source.content}</p>
    </motion.div>
  );
}
