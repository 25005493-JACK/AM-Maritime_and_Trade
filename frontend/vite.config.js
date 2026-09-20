import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [tailwindcss(), react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/shipments': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/submit': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/emails': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/attachments': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/sample_submission': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  }
})
