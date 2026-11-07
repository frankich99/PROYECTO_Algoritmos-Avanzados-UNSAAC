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

Después de modificar la API Python hay que reiniciar uvicorn si se inició
sin `--reload`. Para probar otro servidor local sin detener el puerto 8000,
definir `ROUTES_API_URL=http://127.0.0.1:8001` antes de iniciar Vite en otro
puerto. No guardar claves de proveedores en esa variable.

### Claves de los proveedores

La API toma `OPENWEATHERMAP_API_KEY` y `TOMTOM_API_KEY` de las variables de
entorno o, si faltan, del archivo `.env` en la raíz del repositorio. Copiar
`.env.example` a `.env` y escribir allí las claves **solo en tu máquina**;
`.env` está excluido de Git y del paquete publicable. Las variables de
entorno prevalecen. Reinicia la API al editar la configuración para que las
consultas nuevas y la web tengan el mismo estado.

La web solo recibe `true/false` para saber qué proveedores están configurados;
**nunca recibe ni muestra las claves del servidor**. Al elegir OpenWeatherMap
o activar TomTom no hace falta volver a escribirlas. Los campos opcionales
«Usar otra clave» sustituyen la clave del servidor solo para esa consulta;
«Quitar clave del navegador» vuelve a usar la del servidor. «Olvidar claves
del navegador» borra solo las alternativas locales. Por defecto las
alternativas no se guardan; «Recordar» las guarda en `localStorage`, que no es
una bóveda segura. Usa HTTPS y controles de acceso si publicas la API.

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

### GitHub Pages (sitio público)

GitHub Pages **no ejecuta Python**. Sin una API pública, la web muestra únicamente
los dos snapshots OSM reales y el benchmark/piloto histórico; calcular rutas,
generar instancias, medir experimentos y consultar proveedores muestran un error
explícito. No se sustituyen por rutas ni tiempos de cola inventados.

Para ofrecer la misma funcionalidad que en local, despliegue FastAPI en un
servicio HTTPS con límites de tráfico y autenticación apropiados y configure:

1. En la API, `RUTAS_CORS_ORIGINS=https://frankich99.github.io` (sin barra final).
2. En las variables del repositorio GitHub Actions, `RUTAS_API_BASE_URL` con el
   origen público de la API, por ejemplo `https://api.ejemplo.com` (sin claves).
3. Reinicie el despliegue de Pages: el workflow verifica `/api/v1/health` y que
   `/api/v1/version` coincide con la versión web **antes** de compilar. Vite
   incorpora la URL al bundle; cambiar la variable exige recompilar.

No configure el backend con `localhost`, ni suba `.env` al repositorio. En local,
si el servidor se inició sin `--reload`, reinícielo al modificar Python. Para
probar la modalidad de solo archivos en Vite, use `VITE_STATIC_DEMO=true` en
desarrollo, sin `VITE_API_BASE_URL`.

## Qué se puede hacer

- Consultar rutas en el centro OSM guardado (891 nodos y 2139 aristas, radio
  aproximado 1,5 km) o en el centro ampliado (1938 nodos y 4753 aristas,
  consulta radial de 3 km recortada por distancia de red), con nodo de origen
  y destino mediante selectores de nodos o coordenadas.
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
  clave configurada en el servidor o alternativa opcional en «Cobertura Cusco». TomTom cubre un
  segmento cercano a un punto, no toda la red.
  Las claves del servidor no se escriben en archivos versionados. Las alternativas por defecto viven
  solo en la memoria del navegador; «Recordar claves» las guarda en
  `localStorage` únicamente con consentimiento, y «Olvidar claves» borra las
  guardadas y las de la sesión, no las del servidor. El almacenamiento del navegador no protege
  frente a scripts ejecutados en el mismo origen. Usar HTTPS si se despliega
  fuera de `127.0.0.1`.

### Visor y condiciones

- El mapa se abre por defecto para redes geográficas. Las casillas «Nodos» y
  «Aristas» y el cambio de base no reinician el encuadre; los botones «Ver toda
  la red» y «Centrar ruta» sí lo ajustan expresamente. «Grafo» funciona sin
  WebGL. La vista previa grande limita las aristas visibles a 3000, sin
  recortar el grafo que utilizan los algoritmos.
- La casilla «Aplicar datos meteorológicos» consulta las condiciones para el
  origen seleccionado y la ruta utiliza **esa misma observación**. La
  actualización manual y la opcional cada 10 minutos requieren conexión;
  una lectura actual de más de 30 minutos se debe actualizar. La lectura se
  puede guardar y eliminar localmente en el navegador para repetir el
  escenario aun sin Internet; al recuperarla no se presenta como actual.
- El factor hipotético usa lluvia, visibilidad, ráfagas y humedad; la
  temperatura se muestra, **pero no está en la fórmula**. Es uniforme: cambia
  el tiempo estimado, no la ruta ni las operaciones de las colas. Los
  resultados JSON contienen fuente, fecha, valores y aportes, no claves.
- En «Rutas» se puede elegir una **hora simulada (HH:MM)** o la **hora actual de
  Cusco** que toma el servidor al calcular. En modo actual, el GPS es opcional:
  solo se solicita al pulsar «Usar mi ubicación» y únicamente coloca el origen;
  debe estar dentro del snapshot, cerca de un nodo vial y tener precisión
  suficiente. Si se deniega, se puede elegir un nodo. Sin TomTom se utiliza el
  supuesto horario del proyecto; con clave y activación explícita, la relación
  de velocidades de **un segmento** se usa como factor uniforme exploratorio.
  Si TomTom no responde o informa un cierre, la ruta no aplica el factor
  automáticamente. Ni el GPS ni TomTom miden congestión en toda la ruta.

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
`/catalog` devuelve solo la disponibilidad de cada clave del servidor (booleanos).
`/conditions` devuelve el factor y sus aportes; `/routes/solve` acepta una
observación aportada por la sesión y comprueba que coincida con el origen.
La respuesta indica que una observación reenviada por el navegador no fue
verificada por el servidor. La web no reescribe el benchmark canónico.

```powershell
.\.venv\Scripts\python.exe -B -m pytest python/tests -q -p no:cacheprovider
cd web
npm run build
npm audit
```
## Segunda entrega: verificación y bitácora

La sección **Evidencias** presenta la matriz de productos, resultados de pruebas,
protocolo/piloto y aportes de GitHub. Los conteos se leen de un JSON fechado, no de
texto fijo. Ver `../docs/SEGUNDA_ENTREGA.md` para reproducirlos.

```powershell
npm run test:report
```

Las pruebas de componentes usan Vitest, Testing Library y jsdom; no prueban el
renderizado WebGL. La suite Python y el piloto se ejecutan desde la raíz, según la
guía. Aprobar todas las pruebas no equivale a 100 % de cobertura de líneas.
