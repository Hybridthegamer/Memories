import { useEffect, useRef } from "react";
import { animate, useInView, useMotionValue, useReducedMotion } from "framer-motion";

interface NumberTickerProps {
  value: number;
  className?: string;
  formatter?: (n: number) => string;
}

const defaultFormatter = (n: number) => Math.round(n).toLocaleString();

export function NumberTicker({ value, className = "", formatter = defaultFormatter }: NumberTickerProps) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, margin: "-10% 0px" });
  const motionValue = useMotionValue(0);
  const prefersReducedMotion = useReducedMotion();

  useEffect(() => {
    if (!ref.current) return;
    if (!inView) return;

    if (prefersReducedMotion) {
      if (ref.current) ref.current.textContent = formatter(value);
      return;
    }

    const controls = animate(motionValue, value, {
      duration: 1.4,
      ease: [0.16, 1, 0.3, 1],
      onUpdate: (latest) => {
        if (ref.current) ref.current.textContent = formatter(latest);
      },
    });
    return () => controls.stop();
  }, [inView, value, motionValue, formatter, prefersReducedMotion]);

  return (
    <span ref={ref} className={className}>
      0
    </span>
  );
}
