import { AnimatePresence } from "framer-motion";
import { useState } from "react";
import { deleteFile as deleteFileRequest, fetchDownloadUrl } from "../api/files";
import { triggerDownload } from "../lib/download";
import { useFileWall } from "../hooks/useFiles";
import { useQueryClient } from "@tanstack/react-query";
import { FileCard } from "./FileCard";
import { MediaViewer } from "./MediaViewer";
import { SelectionToolbar } from "./SelectionToolbar";

interface GalleryGridProps {
  folder?: string | null;
}

export function GalleryGrid({ folder }: GalleryGridProps) {
  const { data, isLoading, isError, fetchNextPage, hasNextPage, isFetchingNextPage } = useFileWall(folder);
  const qc = useQueryClient();

  const [selectionMode, setSelectionMode] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [viewerIndex, setViewerIndex] = useState<number | null>(null);
  const [massActionBusy, setMassActionBusy] = useState(false);

  const items = data?.pages.flatMap((p) => p.items) ?? [];

  function enterSelectionWith(fileId: string) {
    setSelectionMode(true);
    setSelectedIds(new Set([fileId]));
  }

  function toggleSelect(fileId: string) {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(fileId)) next.delete(fileId);
      else next.add(fileId);
      return next;
    });
  }

  function exitSelection() {
    setSelectionMode(false);
    setSelectedIds(new Set());
  }

  async function handleMassDownload() {
    setMassActionBusy(true);
    try {
      for (const id of selectedIds) {
        try {
          const url = await fetchDownloadUrl(id);
          triggerDownload(url);
        } catch {
          // skip files that fail to yield a URL; continue with the rest
        }
        // Small stagger so the browser doesn't treat this as a burst of
        // popups and prompt to block multi-file downloads.
        await new Promise((resolve) => setTimeout(resolve, 200));
      }
    } finally {
      setMassActionBusy(false);
    }
  }

  async function handleMassDelete() {
    if (!confirm(`Delete ${selectedIds.size} file(s)? This can't be undone.`)) return;
    setMassActionBusy(true);
    let failed = 0;
    try {
      for (const id of selectedIds) {
        try {
          await deleteFileRequest(id);
        } catch {
          failed += 1;
        }
      }
    } finally {
      setMassActionBusy(false);
      qc.invalidateQueries({ queryKey: ["files"] });
      exitSelection();
      if (failed > 0) {
        alert(`${failed} file(s) couldn't be deleted — they may not be yours, or their 3-day window has passed.`);
      }
    }
  }

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
        {folder ? `Nothing in "${folder}" yet.` : "Nothing here yet — be the first to add a memory."}
      </p>
    );
  }

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <p className="text-xs text-muted">{selectionMode ? "Tap items to select" : "Hold an item to select multiple"}</p>
        <button
          onClick={() => (selectionMode ? exitSelection() : setSelectionMode(true))}
          className="rounded-full border border-border px-4 py-1.5 text-xs text-muted transition-colors hover:border-accent hover:text-accent"
        >
          {selectionMode ? "Cancel" : "Select"}
        </button>
      </div>

      <div className="columns-2 gap-4 sm:columns-3 md:columns-4 lg:columns-5">
        <AnimatePresence>
          {items.map((file, i) => (
            <FileCard
              key={file.id}
              file={file}
              selectionMode={selectionMode}
              selected={selectedIds.has(file.id)}
              onOpen={() => setViewerIndex(i)}
              onLongPress={enterSelectionWith}
              onToggleSelect={toggleSelect}
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

      {viewerIndex !== null && (
        <MediaViewer
          files={items}
          index={viewerIndex}
          onClose={() => setViewerIndex(null)}
          onIndexChange={setViewerIndex}
        />
      )}

      <SelectionToolbar
        count={selectedIds.size}
        busy={massActionBusy}
        onDownload={handleMassDownload}
        onDelete={handleMassDelete}
        onCancel={exitSelection}
      />
    </div>
  );
}
