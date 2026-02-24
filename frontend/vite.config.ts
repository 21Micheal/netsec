import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import * as path from 'path'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    open: false,
    // --- Proxy Configuration Added Here ---
    proxy: {
      // Proxy for Socket.IO requests (needs WebSocket support: ws: true)
      '/socket.io': {
        target: 'http://localhost:5000',
        ws: true,
      },
      // Proxy for general API requests
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true, // Needed for virtual hosting
      }
    }
    // --------------------------------------
  },
  build: {
    outDir: 'dist',
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
})
