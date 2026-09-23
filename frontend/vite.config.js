import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // 5000 ya lo usa el dashboard web de P8 en esta máquina; el backend
      // local de este proyecto corre en 5001 (ver backend/.env).
      "/api": "http://localhost:5001",
    },
  },
});
