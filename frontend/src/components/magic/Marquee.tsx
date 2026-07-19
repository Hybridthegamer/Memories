import { ReactNode } from "react";

interface MarqueeProps {
  children: ReactNode;
  className?: string;
}

// Renders the content twice back-to-back inside one strip, then scrolls the
// whole strip by exactly -50% — since the two halves are identical, the loop
// point is invisible.
export function Marquee({ children, className = "" }: MarqueeProps) {
  return (
    <div className={`group flex w-full overflow-hidden ${className}`}>
      <div className="flex w-max shrink-0 animate-marquee items-center gap-8 group-hover:[animation-play-state:paused] motion-reduce:animate-none">
        <div className="flex shrink-0 items-center gap-8">{children}</div>
        <div className="flex shrink-0 items-center gap-8" aria-hidden="true">
          {children}
        </div>
      </div>
    </div>
  );
}
