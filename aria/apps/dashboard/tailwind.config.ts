import type { Config } from "tailwindcss";

export default {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        base: "#f5f3ef",
        ink: "#1f1b16",
        accent: "#165d52",
        muted: "#7b756d"
      },
      fontFamily: {
        display: ["Georgia", "serif"],
        body: ["ui-sans-serif", "system-ui"]
      }
    }
  },
  plugins: []
} satisfies Config;
