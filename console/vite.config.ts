import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  define: {
    BASE_URL: JSON.stringify('/process'),
  },
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/process': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    }
  }
})
