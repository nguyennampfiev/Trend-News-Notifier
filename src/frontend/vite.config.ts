import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 3000,  // Frontend runs on port 3000
    proxy: {
      '/api': {
        target: 'http://localhost:8002',  // Backend runs on port 8002
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
