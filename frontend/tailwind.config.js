function withOpacity(variableName) {
  return ({ opacityValue }) => {
    if (opacityValue === undefined) {
      return `oklch(var(${variableName}))`;
    }
    return `oklch(var(${variableName}) / ${opacityValue})`;
  };
}

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: withOpacity("--color-bg"),
        surface: withOpacity("--color-surface"),
        surface2: withOpacity("--color-surface2"),
        ink: withOpacity("--color-ink"),
        muted: withOpacity("--color-muted"),
        border: withOpacity("--color-border"),
        accent: withOpacity("--color-accent"),
        accentDim: withOpacity("--color-accentDim"),
        accentInk: withOpacity("--color-accentInk"),
      },
      fontFamily: {
        display: ["Fraunces", "ui-serif", "Georgia", "serif"],
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      keyframes: {
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        marquee: {
          "0%": { transform: "translateX(0%)" },
          "100%": { transform: "translateX(-50%)" },
        },
        "border-beam": {
          "100%": { offsetDistance: "100%" },
        },
        drift: {
          "0%, 100%": { transform: "translate3d(0,0,0)" },
          "50%": { transform: "translate3d(2%, -3%, 0)" },
        },
      },
      animation: {
        shimmer: "shimmer 2.5s linear infinite",
        marquee: "marquee 28s linear infinite",
        "border-beam": "border-beam 6s linear infinite",
        drift: "drift 14s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
