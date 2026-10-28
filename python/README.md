# Prototipo computacional: rutas mínimas en redes viales del Cusco

Implementación modular en Python de Dijkstra con tres colas de prioridad intercambiables, $A^*$ con heurística consistente, un certificado de optimalidad y un caso aplicado sobre OpenStreetMap.

[![Python 3.12](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-246%20passed-brightgreen.svg)](tests/)
[![Datos](https://img.shields.io/badge/snapshots-OSM%20%2B%20clima-informational.svg)](data/processed/)

**Asignatura:** Algoritmos Avanzados (2026-II) · UNSAAC  
**Grupo 5:** Choquenaira Q. Noe, Yaranga A. Aldo, Porroa S. Yeni Ruth, Quispe R. Romario  
**Guía de sustentación:** [GUIA.md](../GUIA.md) · **Informe:** [main.pdf](../documento/main.pdf)

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

Requiere Python 3.10 o superior (verificado en 3.12.8):

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

---

## 3. CLI

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

Vistas: **Comparación**, **Ruta OSM**, **Traza manual** y **Procedencia**. La aplicación lee los snapshots locales; si no hay red, sigue funcionando. La actualización meteorológica desde Open-Meteo es opcional y nunca elimina el snapshot anterior si falla.

---

## 5. Datos y reproducibilidad

| Archivo | Contenido |
| :--- | :--- |
| `data/instances/cusco_centro.json` | Instancia ilustrativa de seis nodos. Nombres reales; longitudes, pendientes y topología esquemáticas. |
| `data/processed/cusco_osm_drive.json` | Snapshot OSM: 891 vértices y 2139 aristas dirigidas, con coordenadas y metadatos. |
| `data/processed/benchmark_results.json` | Protocolo, entorno, muestras, medianas, IQR y operaciones por escala. |
| `data/processed/applied_results.json` | Consulta OSM, tiempos por cola, $A^*$ y sensibilidad climática. |
| `data/processed/weather_cusco.json` | Snapshot de Open-Meteo (datos de modelo). |

Regeneración completa desde la raíz del repositorio:

```bash
.\.venv\Scripts\python.exe python/scripts/reproduce_canonical.py
```

Para reutilizar los JSON existentes y reescribir solo tablas y figuras:

```bash
.\.venv\Scripts\python.exe python/scripts/reproduce_canonical.py --skip-benchmark --skip-applied
```

---

## 6. Pruebas

```bash
.\.venv\Scripts\python.exe -m pytest python/tests -q
```

La suite contiene **246 pruebas** y cubre:

* contrato común de las tres colas (inserción, extracción, `decrease_key`, claves inválidas y cortes en cascada);
* equivalencia con Bellman-Ford, Dijkstra con arreglo y NetworkX;
* certificado de optimalidad $O(V+E)$ y casos alterados que deben fallar;
* validación de JSON, pesos negativos, NaN y estructuras incompletas;
* CLI, carga OSM, clima, análisis aplicado y pruebas de humo de Streamlit.

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
│   ├── services/        # Open-Meteo y factor climático
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
* La instancia de seis nodos es ilustrativa.
