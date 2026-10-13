import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

const frontendDir = path.resolve(__dirname, "../../frontend");

export default defineConfig({
  root: path.resolve(__dirname),
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    port: 5189,
    strictPort: true,
    hmr: false,
    cors: false,
    fs: {
      allow: [path.resolve(__dirname, "../..")],
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(frontendDir, "src"),
      "react": path.resolve(frontendDir, "node_modules/react"),
      "react-dom": path.resolve(frontendDir, "node_modules/react-dom"),
    },
  },
});
