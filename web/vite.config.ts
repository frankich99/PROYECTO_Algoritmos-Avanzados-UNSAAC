import { defineConfig, loadEnv } from 'vite'

export default defineConfig(({ mode }) => {
  const target = loadEnv(mode, process.cwd(), 'ROUTES_').ROUTES_API_URL || 'http://127.0.0.1:8000'
  return {
    base: './',
    server: {
      proxy: {
        '/api': {
          target,
          configure: (proxy) => {
            proxy.on('error', (_err, _req, res) => {
              if (res && 'writeHead' in res && !res.headersSent) {
                res.writeHead(503, { 'Content-Type': 'application/json' })
                res.end(
                  JSON.stringify({
                    detail:
                      'No se pudo conectar con el backend en http://127.0.0.1:8000. Asegúrate de haber iniciado el servidor con: .\\.venv\\Scripts\\python.exe -m uvicorn web_api:app --app-dir python --host 127.0.0.1 --port 8000'
                  })
                )
              }
            })
          }
        },
        '/docs': target,
        '/openapi.json': target
      }
    }
  }
})
