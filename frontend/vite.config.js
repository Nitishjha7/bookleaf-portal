import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// During local dev we proxy /api to the FastAPI backend on :8099 so the
// frontend can call relative URLs and we avoid CORS entirely in dev.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:8099",
    },
  },
});
