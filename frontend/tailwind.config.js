/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "oklch(0.16 0.012 70)",
        surface: "oklch(0.21 0.014 70)",
        surface2: "oklch(0.27 0.017 70)",
        ink: "oklch(0.96 0.01 80)",
        muted: "oklch(0.74 0.02 75)",
        border: "oklch(0.33 0.015 70)",
        accent: "oklch(0.75 0.16 75)",
        accentDim: "oklch(0.6 0.13 75)",
        accentInk: "oklch(0.18 0.02 75)",
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
