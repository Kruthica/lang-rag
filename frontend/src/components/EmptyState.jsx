import { motion } from 'framer-motion';
import { FileSearch, Sparkles } from 'lucide-react';

export default function EmptyState() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-1 flex-col items-center justify-center px-6 text-center"
    >
      <motion.div
        className="mb-6 rounded-2xl p-4 gradient-border"
        animate={{ scale: [1, 1.03, 1] }}
        transition={{ duration: 4, repeat: Infinity }}
      >
        <Sparkles className="h-12 w-12 text-accent-glow" />
      </motion.div>
      <h2 className="text-2xl font-semibold text-white">Ask your documents anything</h2>
      <p className="mt-2 max-w-md text-sm text-gray-400">
        Upload PDFs in the sidebar, then ask questions. Answers are grounded in your files with
        source citations.
      </p>
      <motion.div
        className="mt-8 flex items-center gap-2 rounded-xl glass px-4 py-3 text-sm text-gray-400"
        whileHover={{ scale: 1.02 }}
      >
        <FileSearch className="h-4 w-4 text-accent-glow" />
        <span>Try: &quot;Summarize the main points&quot;</span>
      </motion.div>
    </motion.div>
  );
}
