# Prototipo computacional: rutas mínimas en redes viales del Cusco

Implementación modular en Python de Dijkstra con tres colas de prioridad intercambiables, $A^*$ con heurística consistente, un certificado de optimalidad y un caso aplicado sobre OpenStreetMap.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-278%20passed-brightgreen.svg)](tests/)
[![Datos](https://img.shields.io/badge/snapshots-OSM%20%2B%20clima-informational.svg)](data/processed/)

**Asignatura:** Algoritmos Avanzados (2026-II) · UNSAAC  
**Grupo 5:** Choquenaira Q. Noe, Yaranga A. Aldo, Porroa S. Yeni Ruth, Quispe R. Romario  
**Guía de sustentación:** [GUIA.md](../GUIA.md) · **Informe:** [main.pdf](../latex/main.pdf)

---

## 1. Alternativas implementadas

| Nombre en la CLI | Estructura | Inserción | Decrease-key | Extract-min | Complejidad SSSP | Papel en el estudio |
| :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| `binary_heap` | Binary Min-Heap indexado | $O(\log V)$ | $O(\log V)$ | $O(\log V)$ | $O((V+E)\log V)$ | Línea base; ganó 3 de 10 escalas sintéticas y la consulta OSM. |
| `4ary_heap` | 4-ary Heap contiguo ($d=4$) | $O(\log_4 V)$ | $O(\log_4 V)$ | $O(4\log_4 V)$ | $O((V+E)\log_4 V)$ | Ganó 7 de 10 escalas sintéticas; ventaja mediana 3.6--4.6 %, con IQR solapados. |
| `fibonacci_heap` | Fibonacci Heap | $O(1)$ amort. | $O(1)$ amort. | $O(\log V)$ amort. | $O(E+V\log V)$ | Cota teórica; no ganó ninguna escala y fue 1.05--1.59 veces más lento que el binario. |
| `astar` | $A^*$ con heurística escalada | $O(\log V)$ | $O(\log V)$ | $O(\log V)$ | Depende de $h$ | Extensión punto a punto; en OSM redujo 887 $\to$ 823 expansiones (7.2 %). |
| `bellman_ford` | Bellman-Ford | — | — | — | $O(VE)$ | Oráculo independiente y detector de ciclos negativos. |

La comparación principal usa el mismo solver Dijkstra y la misma instancia para las tres colas. $A^*$ se reporta por separado para no mezclar el efecto de la cola con el de la heurística. NetworkX se usa solo como oráculo externo en las pruebas y en el benchmark.

---

## 2. Instalación

Requiere Python 3.10 o superior (las mediciones guardadas se obtuvieron con 3.12.8). Desde la raíz del repositorio:

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r python/requirements.txt
```

---

## 3. CLI

Los comandos siguientes se ejecutan desde `python/`. Se admiten archivos JSON, TXT y CSV de aristas, además de `--inline`. Los pesos para Dijkstra deben ser finitos y no negativos; `--source` elige un nodo existente. Un resultado exportado con `run -o` contiene distancias, rutas y contadores en JSON; `verify` comprueba ese resultado contra la misma instancia.

```bash
# Alternativas disponibles
python main.py list

# Dijkstra con las tres colas sobre la instancia ilustrativa
python main.py compare --metric time

# A* hacia el Mercado Central San Pedro (instancia de seis nodos)
python main.py astar --target E

# Traza manual de la instancia de seis nodos
python main.py run -i data/instances/cusco_centro.json --trace

# Instancia clásica de Cormen (Fig. 24.6)
python main.py run -i data/instances/clrs_24_6.txt --trace

# Grafo dictado en vivo
python main.py run --inline "A B 4; A C 1; C B 2; B D 5; C D 8" -s A -q all

# Ciclo generación, ejecución y verificación (archivos de ejemplo en python/)
python main.py generate --type random --nodes 40 --seed 3 -o ejemplo.json
python main.py run -i ejemplo.json -q binary -o resultado.json
python main.py verify -i ejemplo.json -r resultado.json

# Exportar Graphviz
python main.py graphviz --target E

# Benchmark exploratorio (no es el protocolo canónico)
python main.py benchmark --scales 50 100 250 500 --runs 5
```

Códigos de salida: `0` ejecución correcta; `1` fallo de verificación; `2` entrada inválida.

---

## 4. Aplicación Streamlit

```bash
python -m streamlit run app.py
```

Cinco secciones visibles: **Ruta** (OSM, Dijkstra/$A^*$, tres colas, plano offline o mapa base, clima histórico/local y CSV), **Comparación** (benchmark filtrable, relación frente al binario, JSON temporal y CSV), **Clima y tráfico** (fuentes separadas, supuestos y consultas API opcionales), **Traza manual** (pasos y certificado) y **Datos y método** (protocolo, límites e informe PDF). Ruta y Comparación son las tareas principales. Las consultas API no sobrescriben el experimento canónico; TomTom solo consulta un segmento. Consulte [datos y modelo](../docs/DATOS_Y_MODELO.md).

---

## 5. Datos y reproducibilidad

| Archivo | Contenido |
| :--- | :--- |
| `data/instances/cusco_centro.json` | Instancia ilustrativa de seis nodos. Nombres reales; longitudes, pendientes y topología esquemáticas. |
| `data/processed/cusco_osm_drive.json` | Snapshot OSM: 891 vértices y 2139 aristas dirigidas, con coordenadas y metadatos. |
| `data/processed/benchmark_results.json` | Protocolo, entorno, muestras, medianas, IQR y operaciones por escala. |
| `data/processed/applied_results.json` | Consulta OSM, tiempos por cola, $A^*$ y sensibilidad climática. |
| `data/processed/pilot_benchmark_results.json` | Piloto del 04/11/2026: 18 muestras, posterior al banco canónico del 28/10/2026. |
| `data/processed/weather_cusco.json` | Lectura local posterior de OpenWeatherMap; la observación Open-Meteo del informe está en `applied_results.json`. |

Desde la raíz del repositorio, regenerar tablas y figuras preservando los
JSON de mediciones históricas:

```bash
.\.venv\Scripts\python.exe python/scripts/reproduce_canonical.py --skip-benchmark --skip-applied
```

Para repetir el protocolo completo, hacerlo **en una copia separada**:

```bash
.\.venv\Scripts\python.exe python/scripts/reproduce_canonical.py
```

El comando completo sobrescribe `benchmark_results.json` y
`applied_results.json` con nuevas mediciones, que pueden diferir del 28/10.
Para reconstruir solo la figura del piloto a partir de su JSON, desde la raíz:

```bash
.\.venv\Scripts\python.exe python/scripts/reproduce_pilot.py --plot-only
```

La imagen se guarda en `latex/figuras/piloto_mediciones.png`. Los archivos del
piloto y del banco separan tiempo de cómputo en microsegundos del tiempo
estimado de viaje de la consulta OSM, expresado en segundos.

---

## 6. Pruebas

```bash
.\.venv\Scripts\python.exe -m pytest python/tests -q
```

La suite contiene **278 pruebas** y cubre:

* contrato común de las tres colas (inserción, extracción, `decrease_key`, claves inválidas y cortes en cascada);
* equivalencia con Bellman-Ford, Dijkstra con arreglo y NetworkX;
* certificado de optimalidad: $O(V+E)$ sin caminos materializados, más $O(L)$ al comprobar caminos explícitos de longitud total $L$; rechaza ciclos de peso cero desconectados;
* validación de JSON, pesos negativos, NaN y estructuras incompletas;
* CLI, carga OSM, clima, modelo horario de tráfico, análisis aplicado y pruebas de humo de Streamlit (no API TomTom en vivo).

No se reporta cobertura porque no se midió con una herramienta de cobertura.

---

## 7. Estructura

```text
python/
├── app.py
├── main.py
├── scripts/reproduce_canonical.py
├── data/
│   ├── instances/
│   └── processed/
├── src/
│   ├── algorithms/      # Dijkstra, A*, Bellman-Ford
│   ├── benchmarks/      # benchmark canónico y caso aplicado
│   ├── datastructures/  # Binary, 4-ary, Fibonacci
│   ├── generators/      # redes sintéticas reproducibles
│   ├── io/              # grafos, JSON y OSM
│   ├── models/          # red ilustrativa del Cusco
│   ├── services/        # Open-Meteo y escenario horario de tráfico
│   ├── utils/           # medición, costo y exportadores
│   ├── verification/    # certificado de optimalidad
│   └── visualization/   # figuras y Graphviz
└── tests/
```

---

## 8. Limitaciones

* Tiempos medidos en Python 3.12 sobre un Ryzen 5 5600H; no son portables a otro lenguaje o CPU.
* Sin métricas de memoria residente ni de asignaciones.
* Una sola consulta OSM y redes sintéticas; no se cubre toda la variabilidad del tráfico.
* El clima es un factor uniforme de sensibilidad, no una calibración de tráfico.
* La observación meteorológica canónica carece de humedad y presión; la lectura local posterior es de otra fuente. No se ha medido congestión ni efecto por arista.
* La instancia de seis nodos es ilustrativa.
