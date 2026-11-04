# Datos, unidades y alcance del modelo

Documento de referencia para el informe y la entrega del Grupo 5. Corte de
revisión: 30 de octubre de 2026. No convierte supuestos en observaciones.

## Tres problemas distintos

| Uso | Fuente de pesos | ¿Pendiente por tramo? | ¿Tráfico por tramo? |
| --- | --- | --- | --- |
| Ejemplo de seis nodos | `python/src/models/cusco_network.py` y `python/src/utils/cost_model.py` | Sí, pero longitudes y pendientes **esquemáticas** | Solo si se pasa explícitamente un factor al modelo |
| Benchmark de colas | `python/src/generators/instance_generator.py` | No; pesos sintéticos | No |
| Consulta OSM canónica | `python/data/processed/cusco_osm_drive.json` | No: el snapshot no contiene elevación ni pendiente | No: usa `travel_time_sec` de flujo nominal |

El snapshot OSM se descargó el **28/10/2026 17:29 UTC**. Incluye 891 nodos,
2139 aristas dirigidas, longitudes en metros y tiempos en segundos. La
conversión usa `travel_time` de OSMnx, o `length_m / speed` con `maxspeed` de
OSM o un valor supuesto según `highway` cuando falta. No equivale a velocidad
medida en tráfico real. El caso canónico elige origen próximo al centro y
destino alcanzable de mayor costo temporal. Su costo base es **387.197 s**,
longitud **2810.6 m** y ruta de **17 vértices**.

La zona puede consultarse visualmente en
<https://www.openstreetmap.org/directions?to=cusco#map=19/-13.517131/-71.978632>.
Ese enlace y la captura incluida en el informe sirven como referencia
geográfica; los resultados no se obtuvieron leyendo la imagen. OSMnx descargó
la red de conducción (`network_type="drive"`) alrededor de
`(-13.5165, -71.9788)` con un radio de 1,500 m y la guardó como
`cusco_osm_drive.json`. El snapshot se usa como entrada congelada para
construir el grafo dirigido y repetir las mediciones sin depender de una
descarga nueva durante cada ejecución.

En `python/app.py`, activar clima y/o un horario simulado multiplica **todos**
los pesos temporales por un mismo número mediante `uniformly_scaled`. La
elección de ruta no cambia. La clase de vía es siempre `avenida`: no se
clasifican aristas OSM ni se asignan factores por tramo. La lectura opcional
de TomTom consulta un solo segmento y no interviene en la ruta. No atribuir
cambios de ruta a TomTom ni presentar los factores horarios como aforos.

## Variables de la consulta meteorológica

Fuente del experimento canónico: `python/data/processed/applied_results.json`,
campo `weather_sensitivity.observation`. Es una respuesta de modelo de
Open-Meteo del **28/10/2026**, originalmente guardada a las 17:33:13 UTC
en un snapshot anterior. Su campo `current.time` era
**28/10/2026 12:30, America/Lima (UTC−5)**. Las coordenadas solicitadas son
(-13.5165, -71.9788); el punto de grilla devuelto es (-13.462214, -71.96707).
No se trata de una estación física en Perayoc o Kayra. `cached: true` al
recargar el archivo significa lectura local, no observación en tiempo real.

| Campo | Valor del snapshot | Unidad / procedencia |
| --- | ---: | --- |
| `temperature_c` | 17.0 | °C; respuesta `current.temperature_2m` |
| `precipitation_mm` | 0.1 | mm por intervalo de 900 s; `current.precipitation` |
| `visibility_m` | 8920 | m; `current.visibility` |
| `wind_speed_kmh` | 12.4 | km/h; `current.wind_speed_10m` |
| `wind_gusts_kmh` | 40.7 | km/h; `current.wind_gusts_10m` |
| `weather_code` | 51 | código WMO; descripción: llovizna ligera |
| `relative_humidity_pct` | **No registrada** | El cargador usa **50 % por defecto**; no es medición. El 46 % citado antes no tiene respaldo en este registro. |
| `surface_pressure_hpa` | **No registrada** | El cargador actual usa `None` (sin dato); 687 hPa en borradores anteriores no fue medición. |
| `rain_mm`, `cloud_cover_pct` | **No registrados** | El cargador tiene valores predeterminados; no atribuirlos al proveedor. |

La función `weather_multiplier` de `python/src/services/weather.py` aplica
coeficientes de **escenario**, no calibrados contra tiempos de viaje: lluvia
0.20 sobre referencia de 10 mm; baja visibilidad 0.15 sobre referencia de
10 000 m; ráfagas 0.10 sobre 80 km/h; humedad 0.08 solo si supera 65 %. Con
estos datos, `m = 1.0691`; la humedad predeterminada de 50 % aporta cero al
cálculo. `387.197 × 1.0691 = 413.952312 s`. El factor es uniforme y conserva
la ruta. El resultado es **sensibilidad estimada**, no tiempo de viaje medido.

El modelo horario de `python/src/services/traffic.py` asigna supuestos
`fluido=1.00`, `moderado=1.25`, `alto=1.65` y `hora_punta=2.20` a partir de
hora local; usa sensibilidades hipotéticas por clase de vía. Sin snapshot de
tráfico canónico ni experimento de tráfico en `applied_results.json`, **no hay
resultado numérico reproducible de congestión para citar en el informe**. La
vista de rutas toma la clase constante `avenida` para toda la red. Si se desea
estudiar tráfico diferencial, harán falta clases por arista, fuente validada,
pruebas, semillas o instantánea, tabla y análisis separado; no se incorpora
automáticamente por existir una fórmula.

## Datos y figuras del informe

- `python/data/processed/benchmark_results.json`: muestras originales,
  semillas, entorno, medianas, IQR y operaciones; **1350** ejecuciones medidas.
  Fue generado el 28/10 antes de corregir el certificado. Su etiqueta
  histórica `certificado O(V+E)` omite el costo de leer caminos explícitos;
  se conserva intacta para no alterar retrospectivamente el registro. La
  versión actual de `certificate.py` añade la detección de ciclos falsos.
- `python/data/processed/applied_results.json`: consulta OSM, tres colas,
  extensión A* y **solo** sensibilidad climática; no incluye tráfico.
- `python/scripts/reproduce_canonical.py`: genera tablas en `latex/tablas/` y
  figuras `benchmark_canonico.png`, `operaciones_canonicas.png` y
  `ruta_osm_cusco.png` en `latex/figuras/`. Las tres se insertan en la sección
  de resultados de `latex/main.tex`.
- `colab/rutas_minimas_cusco.ipynb`: demostración pedagógica independiente; no
  es fuente de las cifras OSM ni del benchmark canónico.

No sobrescribir los JSON canónicos al comprobar un escenario. Las mediciones
de pared cambian al repetir el benchmark en otra máquina o fecha; el costo
óptimo del snapshot y los parámetros de generación sí deben reproducirse.

## Snapshot local posterior y aplicación web

`python/data/processed/weather_cusco.json` se actualizó después del caso
canónico con una respuesta distinta de **OpenWeatherMap**: consulta del
31/10/2026 a las 23:58:57 UTC, guardada el 01/11 a las 00:00:51 UTC.
Reporta 15.13 °C, 55 % de humedad, 0 mm de precipitación, 10 000 m de
visibilidad y 12.96 km/h de ráfagas. La respuesta original trae `main.pressure`
= 1013 hPa (nivel del mar) y `main.grnd_level` = **651 hPa** (suelo). En la
primera serialización el campo `surface_pressure_hpa` tomó erróneamente 1013;
se corrigió a 651 usando la respuesta original, sin inventar una lectura.
OpenWeatherMap no identifica una estación física de la UNSAAC en esa respuesta.
Este archivo posterior **no** es la fuente del factor 1.0691 del informe.

La web muestra cinco secciones de acceso directo, con Ruta y Comparación al
frente. El plano vial local no necesita teselas; el mapa base sí. En Ruta se
puede elegir la observación histórica del informe, el archivo local posterior
o una consulta meteorológica temporal; las fuentes se nombran y nunca se
confunden. La traza manual permite inspeccionar cada estado de Dijkstra y el
certificado. Los resultados de ruta se mantienen en sesión; los benchmarks
cargados por archivo JSON no sobrescriben los datos canónicos y su protocolo
externo no se valida automáticamente. Se muestran ausencia de datos, espera
y errores. La consulta
opcional de APIs no guarda los resultados en disco. Un snapshot local se
etiqueta como tal, no como lectura en vivo. La suite simula proveedores y
prueba el flujo principal sin clave ni Internet. Aún faltan datos de tráfico
por arista y evidencia individual auténtica de AG-C06.
