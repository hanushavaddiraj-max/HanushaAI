import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  base: "/",
  plugins: [react()],
  preview: {
    port: parseInt(process.env.PORT) || 8080, // Use PORT env variable or fallback to 8080
    strictPort: true,
  },
  server: {
    port: parseInt(process.env.PORT) || 8080, // Use PORT env variable or fallback to 8080
    strictPort: true,
    host: true,
  },
});
