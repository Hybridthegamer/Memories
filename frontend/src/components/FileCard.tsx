import { motion } from "framer-motion";
import { useMemo, useState } from "react";
import { isMine } from "../lib/ownership";
import { BorderBeam } from "./magic/BorderBeam";
import type { FileItem } from "../types";

interface FileCardProps {
  file: FileItem;
  onDownload: () => void;
  onDelete: () => void;
  onPlay: () => void;
}

function formatTimeLeft(deadline: string): string {
  const ms = new Date(deadline).getTime() - Date.now();
  if (ms <= 0) return "";
  const hours = Math.floor(ms / (1000 * 60 * 60));
  if (hours < 1) return "under 1h left to delete";
  if (hours < 24) return `${hours}h left to delete`;
  return `${Math.floor(hours / 24)}d left to delete`;
}

export function FileCard({ file, onDownload, onDelete, onPlay }: FileCardProps) {
  const [hovered, setHovered] = useState(false);
  const mine = useMemo(() => isMine(file.id), [file.id]);
  const withinWindow = useMemo(() => new Date(file.delete_deadline).getTime() > Date.now(), [file.delete_deadline]);
  const canDelete = mine && withinWindow;
  const isVideo = file.media_type === "video";
  const clickable = isVideo && file.status === "ready";

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.94 }}
      transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      className="group relative mb-4 break-inside-avoid overflow-hidden rounded-2xl border border-border bg-surface"
    >
      {hovered && <BorderBeam radius={16} />}

      {file.status === "ready" && file.thumbnail_url ? (
        <img
          src={file.thumbnail_url}
          alt={file.original_name}
          loading="lazy"
          onClick={clickable ? onPlay : undefined}
          className={`block w-full ${clickable ? "cursor-pointer" : ""}`}
        />
      ) : file.status === "failed" ? (
        <div className="flex aspect-[4/3] w-full items-center justify-center bg-surface2 text-sm text-muted">
          Processing failed
        </div>
      ) : (
        <div className="flex aspect-[4/3] w-full animate-pulse items-center justify-center bg-surface2 text-sm text-muted">
          Developing…
        </div>
      )}

      {isVideo && file.status === "ready" && (
        <span className="pointer-events-none absolute left-2 top-2 rounded-full bg-bg/70 px-2 py-0.5 text-xs text-ink backdrop-blur-sm">
          ▶ video
        </span>
      )}

      {file.folder && (
        <span className="pointer-events-none absolute right-2 top-2 max-w-[70%] truncate rounded-full bg-bg/70 px-2 py-0.5 text-xs text-muted backdrop-blur-sm">
          {file.folder}
        </span>
      )}

      <div className="pointer-events-none absolute inset-0 flex flex-col justify-end bg-gradient-to-t from-bg/90 via-bg/0 to-bg/0 opacity-0 transition-opacity duration-300 group-hover:opacity-100">
        <div className="pointer-events-auto flex items-center justify-between gap-2 p-3">
          <button
            onClick={onDownload}
            className="rounded-full bg-ink/10 px-3 py-1.5 text-xs font-medium text-ink backdrop-blur-sm transition-colors hover:bg-accent hover:text-accentInk"
          >
            Download
          </button>
          {canDelete ? (
            <button
              onClick={onDelete}
              className="rounded-full px-3 py-1.5 text-xs font-medium text-ink/80 transition-colors hover:bg-red-500/20 hover:text-red-300"
              title={formatTimeLeft(file.delete_deadline)}
            >
              Delete
            </button>
          ) : (
            <span className="text-xs text-ink/50">{mine ? "permanent now" : ""}</span>
          )}
        </div>
      </div>
    </motion.div>
  );
}
