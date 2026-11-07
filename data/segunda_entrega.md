# Segunda entrega: guía técnica y evidencias

La web organiza los siete productos requeridos en **Evidencias**. La matriz usa las secciones del informe: implementación (6/7), pruebas (8), integración (7/8), complejidad (6), experimentos (9/10/11), documentación (7/14) y bitácora (14). No es una calificación ni una acreditación de defensa individual.

## Instalación y ejecución local

Requisitos: Python 3.12, Node 22.12 o posterior y Git. En PowerShell, desde la raíz:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r python\requirements.txt
cd web
npm ci
npm run build
cd ..
.\.venv\Scripts\python.exe -B -m uvicorn web_api:app --app-dir python --host 127.0.0.1 --port 8000
```

Abre http://127.0.0.1:8000/. No inicies otro proceso si 8000 ya está ocupado. Ctrl+C detiene el servidor; reinícialo tras cambiar Python. Para desarrollo, API en una terminal y `npm run dev` en `web` en otra. Vite usa 5173 y reenvía `/api` a 8000. Elimina variables de despliegue ajenas si usas este modo; no copies ni publiques `.env`.

## Módulos y flujo integrado

| Módulo | Responsabilidad |
| --- | --- |
| `web/src/GraphView.tsx` | Grafo/mapa y casillas de nodos, nombres, aristas, pesos y recorrido |
| `web/src/EvidencePage.tsx` | Matriz, resultados guardados, piloto y bitácora |
| `web/src/ComplexityTable.tsx` | Cotas y operaciones dominantes |
| `python/web_api.py` | Validación HTTP, rutas, escenarios y experimentos |
| `python/src/io/` | JSON/CSV/TXT y snapshots OSM |
| `python/src/generators/` | Redes aleatorias, cuadrículas, dispersas y densas |
| `python/src/datastructures/` | Montículos binario indexado, 4-ario y Fibonacci |
| `python/src/algorithms/` | Dijkstra, A*, Bellman-Ford y Dijkstra con arreglo |
| `python/src/verification/` | Certificación y comparación independiente |
| `python/src/benchmarks/` | Verificación previa y medición del núcleo |
| `python/scripts/review_delivery.py` | Pruebas guardadas + piloto + Git → evidencia JSON/Markdown |

El flujo es: cargar/generar → validar → ejecutar → verificar → registrar muestras/operaciones → tablas y gráficos. Las pruebas de integración HTTP repiten los cuatro generadores con semillas 0, 42 y 12345. Las pruebas de algoritmos pequeños usan enumeración exhaustiva, además de las referencias existentes.

## Formatos y parámetros

- Tabla/JSON: ID único por vértice, aristas con `origin`, `destination`, `weight` no negativo y finito. `directed: true` requiere declarar cada sentido. Coordenadas opcionales; no convierten un peso abstracto en metros.
- TXT/CSV: una línea `A B 4` o `A,B,4`, cabecera `origin,destination,weight` opcional.
- Generación: `random`, `grid`, `sparse`, `dense`; semilla entera; 2–500 vértices en la API. Cuadrícula: 1–30 filas/columnas. La UI exige al menos dos vértices.
- Instancias importadas: hasta 5000 nodos, 30000 aristas y 2 MB en la API.
- Resultado: JSON con camino, costo, unidad, comparaciones, contadores y tiempo aislado. No es un benchmark de colas.
- Escenarios: pendientes/velocidades y multiplicadores son supuestos no calibrados. OSM no tiene pendiente medida en este proyecto. Un factor uniforme positivo cambia el costo, no el camino óptimo.

## Pruebas y reproducción

```powershell
.\.venv\Scripts\python.exe -B -m pytest python/tests -q -p no:cacheprovider --junitxml=python/test-results/junit.xml
cd web
npm run test:report
cd ..
.\.venv\Scripts\python.exe -B python/scripts/review_delivery.py --github-check
cd web
npm run build
```

`--github-check` consulta una vez el commit remoto vía GitHub, sin claves. Sin ese argumento, el informe marca que no se verificó el remoto. El programa no hace reset, checkout, commit ni push. Si las pruebas fallan, no genera una evidencia de éxito. Los resultados web con jsdom prueban los componentes, no el renderizado WebGL; ese último requiere navegador.

Resultados: XML en `python/test-results/`, JSON Vitest en `web/test-results/`, `delivery_evidence.json` y `delivery_pilot.json` en `python/data/processed/` y copias publicables en `web/public/data/` y `data/`. Una ejecución nueva varía en tiempo; las semillas reproducen grafos, no latencias idénticas. El reporte conserva fecha, entorno y base Git; los cambios sin commit se identifican como locales.

## Diseño experimental definitivo y piloto

Banco canónico: disperso V = 100, 500, 1000, 2500, 5000; denso V = 50, 100, 200, 400, 800. E ≈ 4V o 0,08V(V−1), respetando los límites de grafo simple del generador. Tres instancias por tamaño, 15 repeticiones por instancia/cola, 2 calentamientos, tres colas: 1350 tiempos. Semilla base 12345; semilla efectiva = base + (10000 si denso) + 31V + índice. Se conservan las semillas efectivas y tiempos crudos.

Piloto de esta revisión: disperso V = 30/100, denso V = 30/60, 2 instancias y 5 repeticiones por cola: 120 tiempos. Comprueba equivalencia contra NetworkX, certificados, reproducción del grafo y orden Q1 ≤ mediana ≤ Q3 antes de publicar. Es distinto del piloto histórico de 18 tiempos y no modifica ninguno de los dos bancos históricos.

Medición: `perf_counter_ns`, microsegundos, GC desactivado durante cada muestra, orden de colas barajado por semilla. Solo solver con `validate=False`, `build_paths=False` y sin traza. I/O, construcción, validación, oráculos y gráficos quedan fuera. Registrar mediana, Q1/Q3, V/E, semillas, muestras y contadores. Mantener máquina/intérprete, grafo, pesos y origen iguales para las tres colas. Evitar cargas concurrentes. No se mide caché ni memoria máxima; no atribuir ventajas a caché sin instrumentación.

## Complejidad temporal y espacial

Con V vértices, E aristas y n elementos en cola:

| Alternativa | Tiempo del núcleo | Espacio auxiliar, sin grafo |
| --- | --- | --- |
| Dijkstra binario/4-ario | O((V+E) log V), peor caso | O(V) |
| Dijkstra Fibonacci | O(E + V log V), amortizado | O(V) |
| A* consistente | Misma cota por cola; h puede ser cero | O(V) |
| Dijkstra arreglo | O(V² + E), peor caso | O(V) |
| Bellman-Ford | O(VE), peor caso | O(V) |

Binario: insertar/extraer/disminuir O(log n), peor caso. 4-ario: insertar/disminuir O(log₄ n), extraer O(4 log₄ n), peor caso. Fibonacci: insertar O(1); disminuir O(1) y extraer O(log n) amortizados; una operación aislada puede alcanzar O(n). No se postula promedio sin distribución de entradas.

Grafo O(V+E). Validar y calibrar h cuestan O(V+E); la calibración conserva solo el mínimo, sin vector de E cocientes. Todos los caminos pueden ocupar O(V²); la traza completa añade O(V² log V + E) de tiempo por ordenaciones y O(V² + E) de espacio en el peor caso. Estas opciones no entran en el cronómetro del benchmark.

## Tendencias y límites

Con E lineal, las extracciones y disminuciones de clave pesan en el costo; al crecer E cuadráticamente dominan las relajaciones y la diferencia amortizada de Fibonacci cobra relevancia asintótica. En instancias pequeñas las constantes pueden dominar. Un ganador por mediana no demuestra significación ni superioridad universal. A* no descarta todas las aristas opuestas a la meta; usa h consistente y puede explorar tanto como Dijkstra. Las cachés no se midieron.

## Correcciones y dificultades pendientes

- Se corrige el modelo para rechazar NaN/infinito/tipos no numéricos antes de calcular.
- Se retiran la falsa cobertura «100 %», el 60 % fijo de A* y las explicaciones causales de caché sin medición.
- Se añaden resultados de pruebas de componentes y referencia exhaustiva con semillas.
- Se separan resultados reales de respaldos sintéticos: no se fabrican observaciones ni benchmarks en Pages.
- La bitácora lista hashes reales. Parte del documento histórico `CONTROL_ENTREGA.md` cita hashes de otra historia; la fuente actual es `BITACORA_GITHUB.md`.
- No se certifica instalación en máquina limpia, aprendizaje individual, reunión, defensa, recepción de entrega ni PDF actualizado. Deben aportarse o verificarse por el equipo/docente.
