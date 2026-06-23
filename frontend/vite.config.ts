import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

// When running inside a GitHub Codespace, the frontend is accessed through
// a forwarded HTTPS URL (https://<name>-5173.app.github.dev) instead of
// localhost. That changes two things:
//   1. Vite 5.4+ blocks requests whose Host header is not in allowedHosts.
//   2. HMR's websocket needs to use wss on port 443 through the tunnel.
const inCodespace = Boolean(process.env.CODESPACES);

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { "@": path.resolve(__dirname, "./src") },
  },
  server: {
    port: 5173,
    host: true,
    // Allow the Codespace forwarded host; harmless in local Docker.
    allowedHosts: true,
    ...(inCodespace
      ? { hmr: { clientPort: 443, protocol: "wss" as const } }
      : {}),
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test-setup.ts"],
  },
});
