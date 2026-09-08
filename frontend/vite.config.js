import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

function readPort(value, fallback) {
  const port = Number(value)
  return Number.isInteger(port) && port > 0 && port <= 65535 ? port : fallback
}

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '')
  const webPort = readPort(env.WHO_MESSED_UP_WEB_PORT, 5510)
  const apiPort = readPort(env.WHO_MESSED_UP_API_PORT, 5511)
  const apiOrigin =
    env.WHO_MESSED_UP_API_ORIGIN ||
    `http://localhost:${apiPort}`

  return {
    plugins: [react()],
    server: {
      port: webPort,
      strictPort: true,
      proxy: {
        "/api": {
          target: apiOrigin,
          changeOrigin: true,
        },
      },
    },
  }
})
