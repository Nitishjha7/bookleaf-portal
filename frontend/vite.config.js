import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// dev only: proxy /api to the backend
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:8099",
    },
  },
});
