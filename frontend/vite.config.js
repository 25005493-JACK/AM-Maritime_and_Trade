import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [tailwindcss(), react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/shipments': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/submit': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/emails': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/attachments': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/sample_submission': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
