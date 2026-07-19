import { motion } from "framer-motion";
import { useRef, useState } from "react";
import { BorderBeam } from "./magic/BorderBeam";
import type { FileItem } from "../types";

const LONG_PRESS_MS = 450;
const MOVE_CANCEL_PX = 10;

interface FileCardProps {
  file: FileItem;
  selectionMode: boolean;
  selected: boolean;
  onOpen: (fileId: string) => void;
  onLongPress: (fileId: string) => void;
  onToggleSelect: (fileId: string) => void;
}

export function FileCard({ file, selectionMode, selected, onOpen, onLongPress, onToggleSelect }: FileCardProps) {
  const [hovered, setHovered] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const startPos = useRef<{ x: number; y: number } | null>(null);
  const firedLongPress = useRef(false);
  const isVideo = file.media_type === "video";
  const canOpen = file.status === "ready";

  function clearTimer() {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  }

  function onPointerDown(e: React.PointerEvent) {
    if (e.button !== undefined && e.button !== 0) return; // left click / touch only
    startPos.current = { x: e.clientX, y: e.clientY };
    firedLongPress.current = false;
    clearTimer();
    timerRef.current = setTimeout(() => {
      firedLongPress.current = true;
      onLongPress(file.id);
    }, LONG_PRESS_MS);
  }

  function onPointerMove(e: React.PointerEvent) {
    if (!startPos.current) return;
    const dx = e.clientX - startPos.current.x;
    const dy = e.clientY - startPos.current.y;
    if (Math.hypot(dx, dy) > MOVE_CANCEL_PX) clearTimer();
  }

  function onPointerUp() {
    clearTimer();
  }

  function onClick() {
    if (firedLongPress.current) {
      // The long-press already handled this interaction; the click that
      // follows pointerup shouldn't also toggle/open.
      firedLongPress.current = false;
      return;
    }
    if (selectionMode) {
      onToggleSelect(file.id);
    } else if (canOpen) {
      onOpen(file.id);
    }
  }

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.94 }}
      transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={onPointerUp}
      onPointerCancel={clearTimer}
      onContextMenu={(e) => e.preventDefault()}
      onClick={onClick}
      className={`group relative mb-4 select-none break-inside-avoid overflow-hidden rounded-2xl border bg-surface transition-colors ${
        selected ? "border-accent" : "border-border"
      } ${selectionMode || canOpen ? "cursor-pointer" : ""}`}
    >
      {hovered && !selectionMode && <BorderBeam radius={16} />}

      {file.status === "ready" && file.thumbnail_url ? (
        <img src={file.thumbnail_url} alt={file.original_name} loading="lazy" className="block w-full" draggable={false} />
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

      {selectionMode && (
        <div
          className={`pointer-events-none absolute inset-0 flex items-start justify-end p-2 transition-colors ${
            selected ? "bg-accent/20" : "bg-bg/10"
          }`}
        >
          <span
            className={`flex h-6 w-6 items-center justify-center rounded-full border-2 text-xs font-bold backdrop-blur-sm ${
              selected ? "border-accent bg-accent text-accentInk" : "border-ink/60 bg-bg/50 text-transparent"
            }`}
          >
            ✓
          </span>
        </div>
      )}
    </motion.div>
  );
}
