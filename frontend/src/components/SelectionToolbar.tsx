import { AnimatePresence, motion } from "framer-motion";

interface SelectionToolbarProps {
  count: number;
  busy: boolean;
  onDownload: () => void;
  onDelete: () => void;
  onCancel: () => void;
}

export function SelectionToolbar({ count, busy, onDownload, onDelete, onCancel }: SelectionToolbarProps) {
  return (
    <AnimatePresence>
      {count > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 40 }}
          transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
          className="fixed inset-x-0 bottom-4 z-40 flex justify-center px-4"
        >
          <div className="flex items-center gap-3 rounded-full border border-border bg-surface/95 px-4 py-2.5 shadow-lg backdrop-blur-sm">
            <span className="text-sm text-ink">{count} selected</span>
            <button
              onClick={onDownload}
              disabled={busy}
              className="rounded-full bg-accent px-4 py-1.5 text-xs font-medium text-accentInk transition-transform hover:scale-105 disabled:opacity-50"
            >
              Download
            </button>
            <button
              onClick={onDelete}
              disabled={busy}
              className="rounded-full border border-border px-4 py-1.5 text-xs font-medium text-ink/80 transition-colors hover:border-red-400 hover:text-red-300 disabled:opacity-50"
            >
              Delete
            </button>
            <button onClick={onCancel} className="rounded-full px-3 py-1.5 text-xs text-muted hover:text-ink">
              Cancel
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
