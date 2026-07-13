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

  return (
    <div
      className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div className="max-w-3xl w-full" onClick={(e) => e.stopPropagation()}>
        {error && <p className="text-white text-center">Failed to load video.</p>}
        {!error && !url && <p className="text-white text-center">Loading video…</p>}
        {url && (
          <video controls autoPlay className="w-full max-h-[80vh] rounded" src={url}>
            Your browser does not support the video tag.
          </video>
        )}
        <button className="mt-4 text-white text-sm underline block mx-auto" onClick={onClose}>
          Close
        </button>
      </div>
    </div>
  );
}
