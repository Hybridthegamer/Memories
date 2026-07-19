interface BorderBeamProps {
  size?: number;
  radius?: number;
  duration?: number;
  className?: string;
}

// A glowing "comet" that travels around the parent's border using the CSS
// motion-path spec. The parent needs `relative` for this to sit correctly;
// pass `radius` matching the parent's own rounded-corner value in pixels.
export function BorderBeam({ size = 60, radius = 24, duration = 6, className = "" }: BorderBeamProps) {
  return (
    <div aria-hidden="true" className={`pointer-events-none absolute inset-0 overflow-hidden rounded-[inherit] ${className}`}>
      <div
        className="absolute animate-border-beam"
        style={{
          offsetPath: `inset(0 round ${radius}px)`,
          animationDuration: `${duration}s`,
          width: size,
          height: size,
          marginLeft: -size / 2,
          marginTop: -size / 2,
          background:
            "radial-gradient(circle, oklch(0.75 0.16 75 / 0.9) 0%, oklch(0.75 0.16 75 / 0) 70%)",
        }}
      />
    </div>
  );
}
