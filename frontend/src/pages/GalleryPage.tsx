import { useState } from "react";
import { GalleryGrid } from "../components/GalleryGrid";
import { UploadDropzone } from "../components/UploadDropzone";
import { Marquee } from "../components/magic/Marquee";
import { NumberTicker } from "../components/magic/NumberTicker";
import { Particles } from "../components/magic/Particles";
import { useFolders, useWallStats } from "../hooks/useFiles";

const TICKER_ITEMS = [
  "no accounts, ever",
  "anyone can add to the wall",
  "your upload is yours to delete for 3 days",
  "after that, it belongs to everyone, forever",
  "nothing here is private",
];

export function GalleryPage() {
  const { data: total } = useWallStats();
  const { data: folders } = useFolders();
  const [selectedFolder, setSelectedFolder] = useState<string | null>(null);

  return (
    <div className="min-h-screen bg-bg">
      <header className="relative overflow-hidden border-b border-border">
        <Particles className="absolute inset-0 h-full w-full animate-drift" count={70} />
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-transparent via-bg/40 to-bg" />

        <div className="relative mx-auto max-w-4xl px-6 pb-14 pt-16 text-center sm:pt-24">
          <p className="font-display text-lg text-accent">Memories</p>
          <h1 className="mt-4 text-balance font-display text-4xl leading-[1.05] tracking-[-0.02em] text-ink sm:text-6xl">
            A wall nobody owns, kept by everyone who adds to it.
          </h1>
          <p className="mx-auto mt-5 max-w-xl text-pretty text-base text-muted sm:text-lg">
            Drop a photo or video and it joins the wall for anyone to see and download. No sign-up. You can take
            your own upload back within 3 days — after that, it's permanent, for good.
          </p>

          {typeof total === "number" && (
            <p className="mt-6 font-display text-2xl text-ink">
              <NumberTicker value={total} /> <span className="text-muted">memories kept so far</span>
            </p>
          )}

          <div className="mx-auto mt-10 max-w-xl text-left">
            <UploadDropzone />
          </div>
        </div>

        <div className="relative border-t border-border bg-surface/60 py-3">
          <Marquee>
            {TICKER_ITEMS.map((item) => (
              <span key={item} className="text-sm text-muted">
                {item} <span className="mx-4 text-border">·</span>
              </span>
            ))}
          </Marquee>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-12">
        {!!folders?.length && (
          <div className="mb-8 flex flex-wrap items-center justify-center gap-2">
            <button
              onClick={() => setSelectedFolder(null)}
              className={`rounded-full border px-4 py-1.5 text-sm transition-colors ${
                selectedFolder === null
                  ? "border-accent bg-accent text-accentInk"
                  : "border-border text-muted hover:border-accent hover:text-accent"
              }`}
            >
              All
            </button>
            {folders.map((f) => (
              <button
                key={f.name}
                onClick={() => setSelectedFolder(f.name)}
                className={`rounded-full border px-4 py-1.5 text-sm transition-colors ${
                  selectedFolder === f.name
                    ? "border-accent bg-accent text-accentInk"
                    : "border-border text-muted hover:border-accent hover:text-accent"
                }`}
              >
                {f.name} <span className="opacity-60">({f.file_count})</span>
              </button>
            ))}
          </div>
        )}

        <GalleryGrid folder={selectedFolder} />
      </main>

      <footer className="border-t border-border px-6 py-8 text-center text-xs text-muted">
        Nothing here is private. Uploads are public the moment they land, and permanent after 3 days.
      </footer>
    </div>
  );
}
