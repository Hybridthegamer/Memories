import { useCallback, useRef, useState } from "react";
import { useUploader } from "../hooks/useUploader";

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
    <div
      className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
        isDragging ? "border-blue-500 bg-blue-50" : "border-gray-300"
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
        className="mb-4"
      />
      <p className="text-sm text-gray-500">Drag and drop photos/videos here, or click to select</p>

      <div className="mt-4 space-y-2 text-left">
        {Object.entries(items).map(([key, item]) => (
          <div key={key} className="text-sm">
            <div className="flex justify-between">
              <span className="truncate max-w-[70%]">{item.name}</span>
              <span className={item.error ? "text-red-500" : "text-gray-600"}>
                {item.error ?? `${item.progress}%`}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded h-2">
              <div
                className={`h-2 rounded ${item.error ? "bg-red-500" : "bg-blue-500"}`}
                style={{ width: `${item.error ? 100 : item.progress}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
