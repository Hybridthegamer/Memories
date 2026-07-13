import type { FileItem } from "../types";

interface FileCardProps {
  file: FileItem;
  onDownload: () => void;
  onDelete: () => void;
  onPlay: () => void;
}

export function FileCard({ file, onDownload, onDelete, onPlay }: FileCardProps) {
  const isVideo = file.media_type === "video";
  const clickable = isVideo && file.status === "ready";

  return (
    <div className="relative group">
      {file.status === "ready" && file.thumbnail_url ? (
        <img
          src={file.thumbnail_url}
          alt={file.original_name}
          className={`w-full aspect-square object-cover rounded ${clickable ? "cursor-pointer" : ""}`}
          onClick={clickable ? onPlay : undefined}
          loading="lazy"
        />
      ) : file.status === "failed" ? (
        <div className="w-full aspect-square bg-red-50 rounded flex items-center justify-center text-xs text-red-400">
          Failed
        </div>
      ) : (
        <div className="w-full aspect-square bg-gray-100 rounded flex items-center justify-center text-xs text-gray-400">
          Processing…
        </div>
      )}
      {isVideo && file.status === "ready" && (
        <span className="absolute top-1 right-1 bg-black/60 text-white text-[10px] px-1 rounded">▶</span>
      )}
      <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 flex items-center justify-center gap-2 rounded transition-opacity">
        <button className="text-white text-xs underline" onClick={onDownload}>
          Download
        </button>
        <button className="text-white text-xs underline" onClick={onDelete}>
          Delete
        </button>
      </div>
    </div>
  );
}
