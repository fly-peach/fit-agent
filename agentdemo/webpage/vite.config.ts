import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  define: {
    BASE_URL: JSON.stringify('/process'),
    TOKEN: JSON.stringify(process.env.TOKEN || ''),
    MOBILE: false,
  },
  plugins: [react()],
  server: {
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
