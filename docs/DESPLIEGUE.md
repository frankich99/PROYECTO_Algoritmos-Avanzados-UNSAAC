# Despliegue de la aplicación web

La web oficial es React + TypeScript (`web/`) y la API es FastAPI
(`python/web_api.py`). En producción, FastAPI sirve la web compilada y la API
desde el mismo origen, de modo que no hace falta un proxy adicional.

> La API ejecuta algoritmos que consumen CPU y puede consultar proveedores
> externos. No la publique sin límites de tráfico y autenticación si estará
> abierta a Internet. El proyecto no incluye cuentas de usuario ni rate
> limiting.

## 1. Build y ejecución local de producción

Desde la raíz del repositorio:

```powershell
cd web
npm ci
npm run build
cd ..
.\.venv\Scripts\python.exe -m uvicorn web_api:app --app-dir python --host 127.0.0.1 --port 8000
```

Abrir <http://127.0.0.1:8000/>. La API queda en el mismo origen:

| Ruta | Contenido |
| :--- | :--- |
| `/` | Aplicación web compilada |
| `/docs` | Documentación interactiva de la API |
| `/openapi.json` | Contrato OpenAPI |
| `/api/v1/health` | Verificación de disponibilidad |
| `/api/v1/version` | Versión de la API y si el build web está presente |

Si `web/dist/` no existe, FastAPI funciona solo como API y no registra las
rutas de la interfaz.

## 2. Paquete publicable

El script `python/scripts/build_publicable.py` reúne el backend, los datos, el
build de la web, un `Dockerfile`, un `Procfile` y scripts de arranque:

```powershell
.\.venv\Scripts\python.exe -B python/scripts/build_publicable.py
```

Genera:

```text
dist_publicable/
├── rutas-cusco-v1.2.0/          # Carpeta lista para ejecutar o copiar
└── rutas-cusco-v1.2.0.zip       # Archivo para entregar o subir al servidor
```

Ejecución local del paquete:

```powershell
cd dist_publicable\rutas-cusco-v1.2.0
.\iniciar.ps1
```

En Linux/macOS:

```bash
cd dist_publicable/rutas-cusco-v1.2.0
chmod +x iniciar.sh
./iniciar.sh
```

El paquete escucha en `0.0.0.0:8000` por defecto y respeta la variable `PORT`.

## 3. Docker

Dentro del paquete publicable:

```bash
docker build -t rutas-cusco:1.2.0 .
docker run --rm -p 8000:8000 -e PORT=8000 rutas-cusco:1.2.0
```

Abrir <http://127.0.0.1:8000/>.

## 4. Render o Railway

1. Suba el contenido de `dist_publicable/rutas-cusco-v1.2.0/` a un repositorio
   (o conecte el repositorio del proyecto y use el `Dockerfile`).
2. Comando de arranque:
   `uvicorn web_api:app --app-dir python --host 0.0.0.0 --port $PORT`.
3. Variables de entorno:
   - `PORT`: la asigna el proveedor.
   - `RUTAS_CORS_ORIGINS`: solo si la web se sirve desde otro dominio.
   - `RUTAS_WEB_DIST`: solo si el build está en otra ruta.
4. Verifique `/api/v1/health` y `/api/v1/version` después del despliegue.

El `Procfile` incluido contiene el comando de arranque para proveedores que lo
reconocen. En Railway también puede configurarse manualmente.

## 5. Publicar la web y la API en orígenes distintos

Si la interfaz se aloja en un servicio estático (Netlify, Vercel, Cloudflare
Pages) y la API en otro dominio:

1. Compile con la URL del backend:

   ```powershell
   cd web
   $env:VITE_API_BASE_URL = "https://api.ejemplo.com"
   npm run build
   ```

2. En el backend, permita el origen de la web:

   ```powershell
   $env:RUTAS_CORS_ORIGINS = "https://web.ejemplo.com"
   .\.venv\Scripts\python.exe -m uvicorn web_api:app --app-dir python --host 0.0.0.0 --port 8000
   ```

No use `*` como origen si la API quedará abierta a Internet.

## 6. Variables de entorno

| Variable | Valor por defecto | Uso |
| :--- | :--- | :--- |
| `PORT` | `8000` | Puerto de escucha en el paquete publicable |
| `RUTAS_WEB_DIST` | `<raíz>/web/dist` | Ruta del build estático |
| `RUTAS_CORS_ORIGINS` | vacío | Orígenes permitidos, separados por coma |
| `VITE_API_BASE_URL` | vacío (mismo origen) | URL de la API al compilar la web |
| `OPENWEATHERMAP_API_KEY` | vacío | Solo CLI; la web pide la clave en el formulario |

Nunca guarde claves en Git. Las claves enviadas desde la web se usan para esa
consulta y no se escriben en los archivos del proyecto.

## 7. Comprobaciones antes de publicar

```powershell
.\.venv\Scripts\python.exe -B -m pytest python/tests -q -p no:cacheprovider
cd web
npm run build
npm audit
```

El resultado esperado es la suite completa en verde y un build sin errores de
TypeScript.
