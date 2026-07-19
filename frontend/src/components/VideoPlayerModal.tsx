import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useState } from "react";
import { fetchDownloadUrl } from "../api/files";

interface VideoPlayerModalProps {
  fileId: string;
  onClose: () => void;
}

export function VideoPlayerModal({ fileId, onClose }: VideoPlayerModalProps) {
  const [url, setUrl] = useState<string | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetchDownloadUrl(fileId)
      .then((videoUrl) => {
        if (!cancelled) setUrl(videoUrl);
      })
      .catch(() => {
        if (!cancelled) setError(true);
      });
    return () => {
      cancelled = true;
    };
  }, [fileId]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center bg-bg/90 p-4 backdrop-blur-sm"
        onClick={onClose}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.96, y: 12 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.96 }}
          transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
          className="w-full max-w-3xl"
          onClick={(e) => e.stopPropagation()}
        >
          {error && <p className="text-center text-red-300">Couldn't load this video.</p>}
          {!error && !url && <p className="text-center text-muted">Loading…</p>}
          {url && (
            <video controls autoPlay className="max-h-[80vh] w-full rounded-2xl" src={url}>
              Your browser does not support the video tag.
            </video>
          )}
          <button className="mx-auto mt-4 block text-sm text-muted hover:text-ink" onClick={onClose}>
            Close (Esc)
          </button>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
