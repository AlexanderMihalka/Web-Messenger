import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Проксі на бекенд у dev-режимі — фронтенд звертається до відносних /api та /ws,
// а Vite сам перенаправляє на FastAPI, тож CORS у розробці не заважає.
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      "/api": {
        target: process.env.VITE_PROXY_TARGET ?? "http://localhost:8000",
        changeOrigin: true,
      },
      "/uploads": {
        target: process.env.VITE_PROXY_TARGET ?? "http://localhost:8000",
        changeOrigin: true,
      },
      "/ws": {
        target: process.env.VITE_PROXY_TARGET ?? "http://localhost:8000",
        ws: true,
        changeOrigin: true,
      },
    },
  },
});
