import { useState } from "react";
import { useDeleteFile, useDownloadUrl, useFileList } from "../hooks/useFiles";
import { FileCard } from "./FileCard";
import { VideoPlayerModal } from "./VideoPlayerModal";

export function GalleryGrid() {
  const [page, setPage] = useState(1);
  const { data, isLoading, isError } = useFileList(page);
  const downloadUrl = useDownloadUrl();
  const deleteFile = useDeleteFile();
  const [playingFileId, setPlayingFileId] = useState<string | null>(null);

  if (isLoading) return <p className="text-center text-gray-500 mt-8">Loading…</p>;
  if (isError || !data) return <p className="text-center text-red-500 mt-8">Failed to load your files.</p>;

  return (
    <div>
      {data.items.length === 0 ? (
        <p className="text-center text-gray-400 mt-8">No files yet — upload something above.</p>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-3">
          {data.items.map((file) => (
            <FileCard
              key={file.id}
              file={file}
              onDownload={async () => {
                const url = await downloadUrl.mutateAsync(file.id);
                window.open(url, "_blank");
              }}
              onDelete={() => {
                if (confirm(`Delete "${file.original_name}"? This cannot be undone.`)) {
                  deleteFile.mutate(file.id);
                }
              }}
              onPlay={() => setPlayingFileId(file.id)}
            />
          ))}
        </div>
      )}

      <div className="flex justify-center items-center gap-4 mt-6">
        <button
          className="text-sm disabled:opacity-40"
          disabled={page === 1}
          onClick={() => setPage((p) => p - 1)}
        >
          Prev
        </button>
        <span className="text-sm text-gray-500">Page {page}</span>
        <button
          className="text-sm disabled:opacity-40"
          disabled={page * data.page_size >= data.total}
          onClick={() => setPage((p) => p + 1)}
        >
          Next
        </button>
      </div>

      {playingFileId && (
        <VideoPlayerModal fileId={playingFileId} onClose={() => setPlayingFileId(null)} />
      )}
    </div>
  );
}
