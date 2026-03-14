import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  base: process.env.VITE_BASE_PATH ?? "/",
  server: {
    watch: {
      // Use polling to avoid ENOSPC (inotify limit) on WSL/Linux with many watchers
      usePolling: true,
      ignored: ["**/public/docs/**"],
    },
  },
});
