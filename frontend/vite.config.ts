import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/manuals': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/machines': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/query': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/translate': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/voice': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
