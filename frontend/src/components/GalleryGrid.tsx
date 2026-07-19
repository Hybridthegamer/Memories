import { AnimatePresence } from "framer-motion";
import { useState } from "react";
import { useDeleteFile, useDownloadUrl, useFileWall } from "../hooks/useFiles";
import { FileCard } from "./FileCard";
import { VideoPlayerModal } from "./VideoPlayerModal";

export function GalleryGrid() {
  const { data, isLoading, isError, fetchNextPage, hasNextPage, isFetchingNextPage } = useFileWall();
  const downloadUrl = useDownloadUrl();
  const deleteFile = useDeleteFile();
  const [playingFileId, setPlayingFileId] = useState<string | null>(null);

  const items = data?.pages.flatMap((p) => p.items) ?? [];

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="aspect-[4/3] animate-pulse rounded-2xl bg-surface" />
        ))}
      </div>
    );
  }

  if (isError) {
    return <p className="text-center text-red-400">Couldn't load the wall. Try refreshing.</p>;
  }

  if (items.length === 0) {
    return (
      <p className="py-16 text-center font-display text-xl text-muted">
        Nothing here yet — be the first to add a memory.
      </p>
    );
  }

  return (
    <div>
      <div className="columns-2 gap-4 sm:columns-3 md:columns-4 lg:columns-5">
        <AnimatePresence>
          {items.map((file) => (
            <FileCard
              key={file.id}
              file={file}
              onDownload={async () => {
                const url = await downloadUrl.mutateAsync(file.id);
                window.open(url, "_blank");
              }}
              onDelete={() => {
                if (confirm(`Delete "${file.original_name}"? This can't be undone.`)) {
                  deleteFile.mutate(file.id);
                }
              }}
              onPlay={() => setPlayingFileId(file.id)}
            />
          ))}
        </AnimatePresence>
      </div>

      {hasNextPage && (
        <div className="mt-6 flex justify-center">
          <button
            onClick={() => fetchNextPage()}
            disabled={isFetchingNextPage}
            className="rounded-full border border-border px-6 py-2.5 text-sm text-ink transition-colors hover:border-accent hover:text-accent disabled:opacity-50"
          >
            {isFetchingNextPage ? "Loading…" : "Load more"}
          </button>
        </div>
      )}

      {playingFileId && <VideoPlayerModal fileId={playingFileId} onClose={() => setPlayingFileId(null)} />}
    </div>
  );
}
