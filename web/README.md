# Aplicación web de rutas

Interfaz React/TypeScript (`web/`) conectada a FastAPI (`python/web_api.py`).
La API usa `python/src/` para validar instancias y ejecutar Dijkstra con las
tres colas, además de A*. No modifica los resultados canónicos. Esta es la
única interfaz web del proyecto; la antigua aplicación Streamlit se retiró.

## Ejecutar en Windows

Desde la raíz del repositorio, instalar dependencias una vez:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r python/requirements.txt
cd web
npm ci
```

En **dos terminales**, desde la raíz y desde `web/` respectivamente:

```powershell
.\.venv\Scripts\python.exe -m uvicorn web_api:app --app-dir python --host 127.0.0.1 --port 8000
```

```powershell
cd web
npm run dev
```

Abrir <http://127.0.0.1:5173/>. Vite reenvía `/api`, `/docs` y
`/openapi.json` al backend local.

## Producción en un solo servicio

FastAPI sirve la web compilada y la API desde el mismo origen:

```powershell
cd web
npm run build
cd ..
.\.venv\Scripts\python.exe -m uvicorn web_api:app --app-dir python --host 0.0.0.0 --port 8000
```

Abrir <http://127.0.0.1:8000/>. `GET /api/v1/version` confirma la versión y si
el build web fue detectado. El paquete publicable se genera con
`python/scripts/build_publicable.py`; instrucciones completas en
[`docs/DESPLIEGUE.md`](../docs/DESPLIEGUE.md).

Si la web y la API se publican en orígenes distintos, compile con
`VITE_API_BASE_URL=https://api.ejemplo.com` y autorice el origen de la web en
la API con `RUTAS_CORS_ORIGINS`. `npm run preview` por sí solo no sirve la API.
No publicar el backend sin límites de tráfico y autenticación: acepta
experimentos de CPU y consultas a proveedores externos.

## Qué se puede hacer

- Consultar rutas en el centro OSM guardado (891 nodos y 2139 aristas, radio
  aproximado 1,5 km) o en el centro ampliado (1938 nodos y 4753 aristas,
  consulta radial de 3 km recortada por distancia de red), con nodo de origen
  y destino por ID o coordenadas.
- Crear un grafo dirigido desde una tabla, importar JSON o lista de aristas
  TXT/CSV (cabecera `origen,destino,peso` opcional), o generar uno con semilla. Para pesos genéricos la unidad es
  «peso», no metros ni segundos. Las coordenadas de grafos propios son
  esquemáticas; el ajuste por latitud/longitud es solo para snapshots OSM.
- Leer costo, recorrido, distancia y tiempo **cuando existen atributos
  viales**, ver aristas y comparar las tres colas con A* por separado. Los
  tiempos de una única ejecución no establecen una ventaja estadística.
- Ver benchmark histórico sin modificarlo, y ejecutar experimentos pequeños
  etiquetados como resultados nuevos de sesión.
- Consultar el modelo Open-Meteo sin clave, o OpenWeatherMap/TomTom con una
  clave suministrada para esa consulta. TomTom cubre un punto, no toda la red.
  Las claves no se escriben en los archivos del proyecto. Usar HTTPS si se
  despliega fuera de `127.0.0.1`.

La base cartográfica **plana** no requiere Internet; la opción «Calles OSM»
solicita teselas externas y su disponibilidad depende del proveedor. Solo una
parte de las aristas del snapshot contiene geometría vial curva; la API dibuja
la polilínea completa cuando todos los tramos de la ruta la tienen y, si falta
algún tramo, usa segmentos entre nodos y lo advierte. El modelo de clima y
horario aplica un multiplicador uniforme hipotético, no tráfico medido por
arista; cambia el costo pero no la ruta. Las observaciones históricas, el
snapshot posterior y las consultas actuales se etiquetan por separado. Más
procedencia: [`docs/DATOS_Y_MODELO.md`](../docs/DATOS_Y_MODELO.md).

## Coberturas ampliadas

Hay dos snapshots locales:

| Cobertura | Alcance | Nodos | Aristas | Estado |
| :--- | :--- | ---: | ---: | :--- |
| Centro | Radio de 1,5 km, descarga del 28/10/2026 | 891 | 2139 | Activa |
| Centro ampliado | Consulta radial de 3 km recortada por distancia de red; base OSM del 10/08/2026 | 1938 | 4753 | Activa y revisada |

El centro ampliado **no es todo Cusco** ni una cobertura administrativa
completa. Se generó desde un XML de Overpass con
`python/scripts/build_urban_snapshot.py`, que primero escribe un
`*.pending.json`, comprueba límites, distancia al centro, conectividad y rutas
de muestra, y solo publica con una segunda revisión:

```powershell
.\.venv\Scripts\python.exe -B python/scripts/build_urban_snapshot.py --xml cusco_3000_drive.osm
.\.venv\Scripts\python.exe -B python/scripts/build_urban_snapshot.py --publish --reviewed
```

El campo `coverage_reviewed: true` se escribe únicamente en el segundo paso.
La API exige ese campo, carga y valida el archivo, y mantiene la opción
desactivada si falta, no pasa los límites (5000 nodos y 30000 aristas) o es
inválido. Una cobertura mayor requiere una estrategia de extracción y límites
de servicio nueva; no debe forzarse la marca.

## API y pruebas

Contrato interactivo: <http://127.0.0.1:8000/docs>.
`POST /api/v1/instances/validate` devuelve IDs, coordenadas y recuentos;
`POST /api/v1/routes/solve` devuelve camino, costo, tramos y comparaciones;
`GET /api/v1/benchmarks/{sparse|dense}` sirve datos históricos;
`POST /api/v1/experiments` mide redes sintéticas nuevas;
`POST /api/v1/conditions` consulta el proveedor seleccionado. Validaciones
fallidas devuelven HTTP 422; ausencia de ruta devuelve `cost: null`.

```powershell
.\.venv\Scripts\python.exe -B -m pytest python/tests -q -p no:cacheprovider
cd web
npm run build
npm audit
```
