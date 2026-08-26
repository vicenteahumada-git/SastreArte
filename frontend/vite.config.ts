import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// El backend se expone a través del propio servidor de Vite bajo /api.
// Así el navegador siempre pide al mismo origen desde el que cargó la página:
// funciona igual en localhost que detrás de un túnel, sin CORS y sin mezclar
// HTTPS con HTTP.
const destinoApi = process.env.VITE_API_PROXY ?? 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // expone el puerto fuera del contenedor
    allowedHosts: [
      'viewer-sniff-eclair.ngrok-free.dev', // Permite esta URL específica
      '.ngrok-free.app', // Opcional: Permite cualquier ngrok
      '.ngrok-free.dev', // Opcional: Permite cualquier ngrok
    ],
    proxy: {
      '/api': {
        target: destinoApi,
        changeOrigin: true,
      },
    },
  },
})
