import type { Config } from "tailwindcss";

// Coral Stay design system (DESIGN.md)
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: { DEFAULT: "#FF5A5F", hover: "#E04E52" }, // Rausch Coral
        secondary: "#00A699", // Kazan Teal
        neutral: "#767676", // Foggy Gray
        surface: "#F7F7F7",
        border: "#DDDDDD", // Babu Light Gray
        text: { primary: "#222222", secondary: "#717171" }, // Hof Dark
        success: "#008A05",
        warning: "#E07912",
        error: "#C13515",
      },
      fontFamily: {
        display: ['"Nunito Sans"', "system-ui", "sans-serif"],
        body: ['"DM Sans"', "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', "ui-monospace", "monospace"],
      },
      borderRadius: {
        sm: "4px",
        DEFAULT: "8px",
        lg: "12px",
        xl: "16px",
        full: "9999px",
      },
      boxShadow: {
        lvl1: "0 1px 2px rgba(0,0,0,0.08), 0 4px 12px rgba(0,0,0,0.05)",
        lvl2: "0 2px 4px rgba(0,0,0,0.08), 0 8px 24px rgba(0,0,0,0.12)",
        lvl3: "0 6px 20px rgba(0,0,0,0.12), 0 16px 40px rgba(0,0,0,0.16)",
      },
      maxWidth: { container: "1280px" },
    },
  },
  plugins: [],
} satisfies Config;
