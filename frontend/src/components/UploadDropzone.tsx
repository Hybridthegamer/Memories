import { AnimatePresence, motion } from "framer-motion";
import { useCallback, useRef, useState } from "react";
import { useUploader } from "../hooks/useUploader";
import { ShimmerButton } from "./magic/ShimmerButton";

export function UploadDropzone() {
  const { items, handleFiles } = useUploader();
  const [isDragging, setIsDragging] = useState(false);
  const [folder, setFolder] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      if (e.dataTransfer.files.length) handleFiles(e.dataTransfer.files, folder);
    },
    [handleFiles, folder]
  );

  return (
    <div>
      <div
        className={`relative rounded-3xl border-2 border-dashed p-10 text-center transition-colors duration-300 ${
          isDragging ? "border-accent bg-accent/5" : "border-border bg-surface/50"
        }`}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={onDrop}
      >
        <input
          ref={inputRef}
          type="file"
          multiple
          accept="image/*,video/*"
          onChange={(e) => e.target.files && handleFiles(e.target.files, folder)}
          className="absolute inset-0 h-full w-full cursor-pointer opacity-0"
          aria-label="Choose photos or videos to upload"
        />
        <p className="font-display text-2xl text-ink">Drop it on the wall</p>
        <p className="mt-2 text-sm text-muted">Photos and videos, no account needed. Everyone can see it.</p>

        <div className="relative z-10 mx-auto mt-5 max-w-xs">
          <input
            type="text"
            value={folder}
            onChange={(e) => setFolder(e.target.value)}
            onClick={(e) => e.stopPropagation()}
            placeholder="Folder name (optional)"
            maxLength={60}
            className="w-full rounded-full border border-border bg-bg/60 px-4 py-2 text-center text-sm text-ink placeholder:text-muted focus:border-accent focus:outline-none"
          />
        </div>

        <div className="relative z-10 mt-4">
          <ShimmerButton onClick={() => inputRef.current?.click()}>Choose files</ShimmerButton>
        </div>
      </div>

      <AnimatePresence>
        {Object.entries(items).length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-4 space-y-2 overflow-hidden"
          >
            <AnimatePresence initial={false}>
              {Object.entries(items).map(([key, item]) => (
                <motion.div
                  key={key}
                  layout
                  initial={{ opacity: 0, y: -8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.96 }}
                  transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
                  className={`rounded-xl border px-4 py-3 text-sm transition-colors ${
                    item.done ? "border-accent/40 bg-accent/5" : "border-border bg-surface"
                  }`}
                >
                  <div className="flex justify-between">
                    <span className="max-w-[70%] truncate text-ink">{item.name}</span>
                    <span className={item.error ? "text-red-400" : item.done ? "text-accent" : "text-muted"}>
                      {item.error ?? (item.done ? "Uploaded ✓" : `${item.progress}%`)}
                    </span>
                  </div>
                  <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-surface2">
                    <motion.div
                      className={`h-full rounded-full ${
                        item.error ? "bg-red-500" : item.done ? "bg-accent" : "bg-accent/70"
                      }`}
                      animate={{ width: `${item.error ? 100 : item.progress}%` }}
                      transition={{ ease: "easeOut", duration: 0.3 }}
                    />
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
