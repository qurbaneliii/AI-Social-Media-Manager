import type { Config } from "tailwindcss";
import defaultTheme from "tailwindcss/defaultTheme";

const config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        aria: {
          bg: "#0A0B0E",
          surface: "#111318",
          border: "#1E2028",
          muted: "#2A2D38",
          accent: "#6C63FF",
          "accent-hover": "#7B73FF",
          success: "#22C55E",
          warning: "#F59E0B",
          danger: "#EF4444",
          text: "#F1F1F3",
          subtle: "#8A8FA8",
          dim: "#4A4F63"
        }
      },
      fontFamily: {
        sans: ["var(--font-inter)", ...defaultTheme.fontFamily.sans]
      }
    }
  }
} satisfies Config;

export default config;
