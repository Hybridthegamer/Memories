import { useCallback, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { uploadFile } from "../lib/uploader";

export interface UploadItem {
  name: string;
  progress: number;
  error?: string;
  done?: boolean;
}

const DISMISS_DELAY_MS = 2500;

export function useUploader() {
  const [items, setItems] = useState<Record<string, UploadItem>>({});
  const qc = useQueryClient();
  const dismissTimers = useRef<Record<string, ReturnType<typeof setTimeout>>>({});

  const handleFiles = useCallback(
    async (files: FileList, folder?: string) => {
      for (const file of Array.from(files)) {
        const key = `${file.name}-${file.size}-${Date.now()}`;
        setItems((prev) => ({ ...prev, [key]: { name: file.name, progress: 0 } }));
        try {
          await uploadFile(
            file,
            (percent) => {
              setItems((prev) => (prev[key] ? { ...prev, [key]: { ...prev[key], progress: percent } } : prev));
            },
            folder
          );
          setItems((prev) => (prev[key] ? { ...prev, [key]: { ...prev[key], progress: 100, done: true } } : prev));
          qc.invalidateQueries({ queryKey: ["files"] });

          dismissTimers.current[key] = setTimeout(() => {
            setItems((prev) => {
              const next = { ...prev };
              delete next[key];
              return next;
            });
            delete dismissTimers.current[key];
          }, DISMISS_DELAY_MS);
        } catch {
          setItems((prev) => (prev[key] ? { ...prev, [key]: { ...prev[key], error: "Upload failed" } } : prev));
        }
      }
    },
    [qc]
  );

  return { items, handleFiles };
}
