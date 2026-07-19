import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useMemo, useState } from "react";
import { fetchDownloadUrl } from "../api/files";
import { triggerDownload } from "../lib/download";
import { formatTimeLeft, isWithinDeleteWindow } from "../lib/format";
import { isMine } from "../lib/ownership";
import { useDeleteFile } from "../hooks/useFiles";
import type { FileItem } from "../types";

interface MediaViewerProps {
  files: FileItem[];
  index: number;
  onClose: () => void;
  onIndexChange: (index: number) => void;
}

export function MediaViewer({ files, index, onClose, onIndexChange }: MediaViewerProps) {
  const file = files[index];
  const [url, setUrl] = useState<string | null>(null);
  const [error, setError] = useState(false);
  const deleteFile = useDeleteFile();

  const mine = useMemo(() => (file ? isMine(file.id) : false), [file]);
  const canDelete = useMemo(() => mine && !!file && isWithinDeleteWindow(file.delete_deadline), [mine, file]);

  useEffect(() => {
    if (!file) return;
    let cancelled = false;
    setUrl(null);
    setError(false);
    fetchDownloadUrl(file.id)
      .then((downloadUrl) => {
        if (!cancelled) setUrl(downloadUrl);
      })
      .catch(() => {
        if (!cancelled) setError(true);
      });
    return () => {
      cancelled = true;
    };
  }, [file]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
      if (e.key === "ArrowRight" && index < files.length - 1) onIndexChange(index + 1);
      if (e.key === "ArrowLeft" && index > 0) onIndexChange(index - 1);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose, onIndexChange, index, files.length]);

  if (!file) return null;

  const isVideo = file.media_type === "video";

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center bg-bg/90 p-4 backdrop-blur-sm"
        onClick={onClose}
      >
        {index > 0 && (
          <button
            aria-label="Previous"
            onClick={(e) => {
              e.stopPropagation();
              onIndexChange(index - 1);
            }}
            className="absolute left-2 top-1/2 z-10 -translate-y-1/2 rounded-full bg-bg/60 p-3 text-ink hover:bg-accent hover:text-accentInk sm:left-6"
          >
            ‹
          </button>
        )}
        {index < files.length - 1 && (
          <button
            aria-label="Next"
            onClick={(e) => {
              e.stopPropagation();
              onIndexChange(index + 1);
            }}
            className="absolute right-2 top-1/2 z-10 -translate-y-1/2 rounded-full bg-bg/60 p-3 text-ink hover:bg-accent hover:text-accentInk sm:right-6"
          >
            ›
          </button>
        )}

        <motion.div
          key={file.id}
          initial={{ opacity: 0, scale: 0.97 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.97 }}
          transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
          className="flex max-h-full w-full max-w-4xl flex-col items-center"
          onClick={(e) => e.stopPropagation()}
        >
          {error && <p className="text-center text-red-300">Couldn't load this file.</p>}

          {!error && isVideo && (
            <video
              controls
              autoPlay
              poster={file.thumbnail_url ?? undefined}
              className="max-h-[75vh] w-full rounded-2xl bg-surface"
              src={url ?? undefined}
            >
              Your browser does not support the video tag.
            </video>
          )}

          {!error && !isVideo && (
            <img
              src={url ?? file.thumbnail_url ?? undefined}
              alt={file.original_name}
              className="max-h-[75vh] w-full rounded-2xl bg-surface object-contain"
            />
          )}

          <div className="mt-4 flex w-full flex-wrap items-center justify-between gap-3 text-sm">
            <div className="min-w-0">
              <p className="truncate text-ink">{file.original_name}</p>
              {canDelete && <p className="text-xs text-muted">{formatTimeLeft(file.delete_deadline)}</p>}
            </div>
            <div className="flex shrink-0 items-center gap-2">
              <button
                onClick={() => url && triggerDownload(url)}
                disabled={!url}
                className="rounded-full bg-accent px-4 py-2 text-xs font-medium text-accentInk transition-transform hover:scale-105 disabled:opacity-50"
              >
                Download
              </button>
              {canDelete && (
                <button
                  onClick={() => {
                    if (confirm(`Delete "${file.original_name}"? This can't be undone.`)) {
                      deleteFile.mutate(file.id);
                      onClose();
                    }
                  }}
                  className="rounded-full border border-border px-4 py-2 text-xs font-medium text-ink/80 transition-colors hover:border-red-400 hover:text-red-300"
                >
                  Delete
                </button>
              )}
              <button onClick={onClose} className="rounded-full border border-border px-4 py-2 text-xs text-muted hover:text-ink">
                Close
              </button>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
