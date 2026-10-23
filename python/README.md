# Rutas mínimas con distintas colas de prioridad: red vial del Cusco

Algoritmo de Dijkstra con tres colas de prioridad intercambiables y una referencia independiente (Bellman-Ford), sobre la red vial del Centro Histórico del Cusco y sobre instancias sintéticas.

**Curso:** Algoritmos Avanzados (2026-II) · UNSAAC
**Grupo 5:** Choquenaira Q., Porroa S., Quispe R., Yaranga A.
**Guías de sustentación:** [Avance 4](../docs/AVANCE_4.md) · [Avance 5](../docs/AVANCE_5.md)

## Alternativas

| Nombre en la CLI | Estructura | Decrease-Key | Extract-Min | Dijkstra total |
|:--|:--|:--|:--|:--|
| `binary_heap` (Avance 4) | Binary Heap indexado | O(log V) | O(log V) | O((V+E) log V) |
| `4ary_heap` (Avance 5) | 4-ary Heap indexado | O(log₄ V) | O(4 log₄ V) | O((4V+E) log₄ V) |
| `fibonacci_heap` (Avance 5) | Fibonacci Heap | O(1) amort. | O(log V) amort. | O(V log V + E) |
| `bellman_ford` | Referencia de validación | — | — | O(V·E) |

## Instalación y ejecución

```bash
cd python
pip install -r requirements.txt

python main.py                 # demostración completa (rutas, verificación, tablas, benchmark, figuras)
python main.py --help          # interfaz común
python -m pytest               # 219 pruebas
```

## Comandos

```bash
python main.py list                                            # alternativas disponibles
python main.py run                                             # red del Cusco, tiempo, origen A, binary_heap
python main.py run --metric distance -q all --trace            # las 3 colas + comparación + traza
python main.py run -i data/instances/clrs_24_6.txt -q fib -o results/r.json
python main.py verify -i data/instances/clrs_24_6.txt -r results/r.json
python main.py run --inline "A B 4; A C 1; C B 2" -s A -q all  # instancia dictada en la sesión
python main.py compare -i data/instances/empates_grid_3x3.json # todas + Bellman-Ford, diferencias clasificadas
python main.py generate --type random --nodes 500 --seed 7 -o results/r500.json
python main.py generate --type grid --rows 4 --cols 4 --weights unit -o results/grid.json
python main.py benchmark --scales 100 500 1000 --runs 5
python main.py menu                                            # menú interactivo
```

Códigos de salida: `0` correcto · `1` la verificación encontró errores · `2` entrada inválida.

## Formatos de entrada

- **JSON vial** (`data/instances/cusco_centro.json`): aristas con `length_m`, `street_type` y `gradient_pct`; el peso se calcula con la impedancia andina según `--metric time|distance`.
- **JSON genérico:** `{"name", "directed", "source", "nodes": [...], "edges": [{"origin","destination","weight"}] | [[u, v, w]]}`.
- **Lista de aristas** (`.txt` / `.csv`): `u v w` por línea; `#` para comentarios; directivas `source X`, `node X` (vértice aislado) y `undirected`.
- **En línea:** `--inline "u v w; u v w"` (más `--undirected` si corresponde).

## Instancias incluidas (`data/instances/`)

| Archivo | Uso |
|---|---|
| `cusco_centro.json` | Caso de estudio: 6 intersecciones, 9 tramos. |
| `clrs_24_6.txt` | Resuelta a mano (Cormen, Fig. 24.6): s=0, y=5, z=7, t=8, x=9. |
| `desconectado.txt` | Vértices inalcanzables y aislados. |
| `empates_rombo.txt`, `empates_grid_3x3.json` | Varios caminos óptimos (rutas pueden diferir con igual costo). |
| `cuadricula_vial_6x6.json` | Cuadrícula sintética con pendientes y tipos de vía. |
| `invalidas/*` | Peso negativo, ciclo negativo, peso no numérico, campos incompletos, nodo inexistente, JSON mal formado, nodos duplicados. |

## Estructura

```
python/
├── main.py                          # entrada: demo sin argumentos; CLI con argumentos
├── src/
│   ├── cli.py                       # interfaz común (run/compare/generate/verify/benchmark/menu)
│   ├── algorithms/
│   │   ├── dijkstra.py              # Dijkstra con inyección de cola ([Lk] = línea del pseudocódigo)
│   │   ├── reference.py             # Bellman-Ford y Dijkstra con arreglo (referencias)
│   │   └── registry.py              # solve(instancia, origen, método)
│   ├── datastructures/
│   │   ├── base.py                  # contrato PriorityQueue
│   │   ├── indexed_min_heap.py      # Binary Heap + tabla de posiciones
│   │   ├── d_ary_heap.py            # Heap d-ario (d = 4)
│   │   ├── fibonacci_heap.py        # Fibonacci Heap
│   │   └── registry.py              # selección de cola por nombre
│   ├── io/graph_io.py               # lectura + validación de instancias
│   ├── generators/instance_generator.py
│   ├── verification/certificate.py  # certificado de optimalidad + comparación clasificada
│   ├── models/cusco_network.py      # red del Centro Histórico
│   ├── utils/                       # cost_model, measurement, presentation, latex_exporter
│   ├── benchmarks/scalability_benchmark.py
│   └── visualization/generate_figures.py
├── tests/                           # 219 pruebas (pytest)
├── data/instances/                  # instancias de demostración e inválidas
└── results/                         # salidas generadas (ignorado por git)
```
