import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#071018",
        panel: "#0d1b24",
        line: "#22313d",
        mint: "#2dd4bf",
        skyglass: "#7dd3fc",
        ember: "#f59e0b",
        signal: "#fb7185",
      },
      boxShadow: {
        panel: "0 20px 50px rgba(3, 10, 18, 0.32)",
      },
    },
  },
  plugins: [],
} satisfies Config;

