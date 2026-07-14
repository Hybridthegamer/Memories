import { useCallback, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { uploadFile } from "../lib/uploader";

export interface UploadItem {
  name: string;
  progress: number;
  error?: string;
}

export function useUploader() {
  const [items, setItems] = useState<Record<string, UploadItem>>({});
  const qc = useQueryClient();

  const handleFiles = useCallback(
    async (files: FileList) => {
      for (const file of Array.from(files)) {
        const key = `${file.name}-${file.size}-${Date.now()}`;
        setItems((prev) => ({ ...prev, [key]: { name: file.name, progress: 0 } }));
        try {
          await uploadFile(file, (percent) => {
            setItems((prev) => ({ ...prev, [key]: { ...prev[key], progress: percent } }));
          });
          qc.invalidateQueries({ queryKey: ["files"] });
        } catch {
          setItems((prev) => ({ ...prev, [key]: { ...prev[key], error: "Upload failed" } }));
        }
      }
    },
    [qc]
  );

  return { items, handleFiles };
}
