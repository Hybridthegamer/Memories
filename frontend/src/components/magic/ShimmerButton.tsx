import { ButtonHTMLAttributes, ReactNode } from "react";

interface ShimmerButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
}

export function ShimmerButton({ children, className = "", ...props }: ShimmerButtonProps) {
  return (
    <button
      {...props}
      className={`group relative isolate overflow-hidden rounded-full bg-accent px-7 py-3
        font-medium text-accentInk transition-transform duration-300 ease-out
        hover:scale-[1.03] active:scale-[0.98] disabled:opacity-50 disabled:hover:scale-100
        ${className}`}
    >
      <span className="relative z-10">{children}</span>
      <span
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 z-0 animate-shimmer opacity-60
          [background-size:200%_100%]
          [background-image:linear-gradient(110deg,transparent_35%,rgba(255,255,255,0.55)_50%,transparent_65%)]"
      />
    </button>
  );
}
