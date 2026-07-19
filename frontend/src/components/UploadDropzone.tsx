import { AnimatePresence, motion } from "framer-motion";
import { useCallback, useRef, useState } from "react";
import { useUploader } from "../hooks/useUploader";
import { ShimmerButton } from "./magic/ShimmerButton";

export function UploadDropzone() {
  const { items, handleFiles } = useUploader();
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      if (e.dataTransfer.files.length) handleFiles(e.dataTransfer.files);
    },
    [handleFiles]
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
          onChange={(e) => e.target.files && handleFiles(e.target.files)}
          className="absolute inset-0 h-full w-full cursor-pointer opacity-0"
          aria-label="Choose photos or videos to upload"
        />
        <p className="font-display text-2xl text-ink">Drop it on the wall</p>
        <p className="mt-2 text-sm text-muted">Photos and videos, no account needed. Everyone can see it.</p>
        <div className="mt-5">
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
            {Object.entries(items).map(([key, item]) => (
              <div key={key} className="rounded-xl border border-border bg-surface px-4 py-3 text-sm">
                <div className="flex justify-between">
                  <span className="max-w-[70%] truncate text-ink">{item.name}</span>
                  <span className={item.error ? "text-red-400" : "text-muted"}>
                    {item.error ?? `${item.progress}%`}
                  </span>
                </div>
                <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-surface2">
                  <motion.div
                    className={`h-full rounded-full ${item.error ? "bg-red-500" : "bg-accent"}`}
                    animate={{ width: `${item.error ? 100 : item.progress}%` }}
                    transition={{ ease: "easeOut", duration: 0.3 }}
                  />
                </div>
              </div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
