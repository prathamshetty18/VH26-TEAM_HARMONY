import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
<<<<<<< HEAD
      '/static': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/diagrams': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/query': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/chat': {
=======
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/manuals': {
>>>>>>> fe36efd08fbd519ff99cd722f33a11287c9daa47
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/machines': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
<<<<<<< HEAD
      '/api': {
=======
      '/query': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/health': {
>>>>>>> fe36efd08fbd519ff99cd722f33a11287c9daa47
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/translate': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
<<<<<<< HEAD
=======
      '/voice': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
>>>>>>> fe36efd08fbd519ff99cd722f33a11287c9daa47
    },
  },
})
