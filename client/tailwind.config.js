/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["'Manrope Variable'", "Manrope", "system-ui", "sans-serif"],
        display: ["'Fraunces Variable'", "Fraunces", "Georgia", "serif"],
      },
      colors: {
        // Холодна темна нейтральна шкала — фон і поверхні застосунку.
        ink: {
          50: "#f3f4f8",
          100: "#e4e6ef",
          200: "#c7cbdc",
          300: "#a6abc4",
          400: "#8489a8",
          500: "#6b7690",
          600: "#4f5670",
          700: "#383d56",
          800: "#23273d",
          850: "#1a1d30",
          900: "#171a2c",
          950: "#0d0f1a",
        },
        // Теплий золотий акцент — основна дія (кнопки, активний стан, непрочитане).
        signal: {
          300: "#e8c988",
          400: "#d9b158",
          500: "#c89b3c",
          600: "#a67f2e",
          700: "#82631f",
        },
        // Приглушений зелений — індикатор «в мережі».
        moss: {
          400: "#7fc9a0",
          500: "#4fae79",
          600: "#398f61",
        },
      },
      boxShadow: {
        panel: "0 4px 12px rgba(0, 0, 0, 0.24), 0 12px 32px -8px rgba(0, 0, 0, 0.32)",
      },
      keyframes: {
        "bubble-in": {
          "0%": { opacity: 0, transform: "translateY(4px) scale(0.98)" },
          "100%": { opacity: 1, transform: "translateY(0) scale(1)" },
        },
        "typing-dot": {
          "0%, 60%, 100%": { transform: "translateY(0)", opacity: 0.4 },
          "30%": { transform: "translateY(-3px)", opacity: 1 },
        },
      },
      animation: {
        "bubble-in": "bubble-in 0.15s ease-out",
        "typing-dot": "typing-dot 1.1s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
