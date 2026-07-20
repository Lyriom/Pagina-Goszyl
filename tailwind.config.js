/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/templates/**/*.html",
    "./app/**/*.py"
  ],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        display: ["Space Grotesk", "Inter", "system-ui", "sans-serif"]
      },
      colors: {
        brand: {
          50: "#f0efff",
          100: "#e4e1ff",
          200: "#cbc6ff",
          300: "#aaa1ff",
          400: "#8578ff",
          500: "#6558f5",
          600: "#5748db",
          700: "#493bb6",
          800: "#3d3294",
          900: "#342d78"
        },
        signal: "#baf56a",
        ink: {
          900: "#05070b",
          850: "#080b12",
          800: "#0d111b",
          700: "#121827",
          600: "#1a2233",
          500: "#263146"
        }
      },
      boxShadow: {
        glow: "0 24px 80px -32px rgba(101, 88, 245, 0.55)",
        soft: "0 24px 60px -36px rgba(2, 6, 23, 0.35)",
        project: "0 40px 90px -35px rgba(0, 0, 0, 0.8)"
      },
      backgroundImage: {
        "grid-dark": "linear-gradient(rgba(255,255,255,0.045) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.045) 1px, transparent 1px)",
        "grid-light": "linear-gradient(rgba(15,23,42,0.055) 1px, transparent 1px), linear-gradient(90deg, rgba(15,23,42,0.055) 1px, transparent 1px)"
      }
    }
  },
  plugins: []
};
