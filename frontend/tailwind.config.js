import forms from "@tailwindcss/forms";
import typography from "@tailwindcss/typography";
import tailwindcssAnimate from "tailwindcss-animate";

/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class", '[data-theme="dark"]'],
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "hsl(var(--bg))",
        surface: "hsl(var(--surface))",
        content: "hsl(var(--content))",
        muted: "hsl(var(--muted))",
        border: "hsl(var(--border))",
        ring: "hsl(var(--ring))",
        primary: { DEFAULT: "hsl(var(--primary))", 2: "hsl(var(--primary-2))" },
        glow: "hsl(var(--glow))",
      },
      boxShadow: {
        glass:
          "0 1px 0 hsl(var(--content)/0.06) inset, 0 0 0 1px hsl(var(--border)/0.6) inset, 0 10px 30px -10px hsl(var(--primary)/0.25)",
      },
      backdropBlur: { xs: "2px" },
      borderRadius: { xl2: "1.25rem" },
      backgroundImage: {
        "radial-pool":
          "radial-gradient(60% 60% at 70% 20%, hsl(var(--primary)/0.20) 0%, transparent 60%), radial-gradient(40% 40% at 20% 80%, hsl(var(--glow)/0.12) 0%, transparent 60%), radial-gradient(30% 30% at 80% 80%, hsl(var(--primary-2)/0.16) 0%, transparent 65%)",
        "glass-gradient": "linear-gradient(180deg, hsl(var(--surface)/0.75), hsl(var(--surface)/0.55))",
      },
      ringColor: { DEFAULT: "hsl(var(--ring))" },
      typography: { invert: { css: { "--tw-prose-links": "hsl(var(--primary))" } } },
    },
  },
  plugins: [forms, typography, tailwindcssAnimate],
};
