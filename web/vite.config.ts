import { defineConfig, loadEnv } from 'vite'

export default defineConfig(({ mode }) => {
  const target = loadEnv(mode, process.cwd(), 'ROUTES_').ROUTES_API_URL || 'http://127.0.0.1:8000'
  return { server: { proxy: { '/api': target, '/docs': target, '/openapi.json': target } } }
})
