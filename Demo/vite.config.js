import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  base: "/IoT-APARS/", // Ensure this matches your GitHub repo name exactly
  publicDir: "public", // Ensure Vite finds static files
  build: {
    outDir: "docs", // GitHub Pages requires build files in docs/
    emptyOutDir: true, // Clears old files before rebuilding
    rollupOptions: {
      input: "public/index.html", // Explicitly tell Vite where to find index.html
    },
  },
});
