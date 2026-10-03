# Rutas Mínimas con Distintas Colas de Prioridad: Red Vial del Cusco

Algoritmo de Dijkstra evaluado con tres estructuras de cola de prioridad sobre la red vial del Centro Histórico del Cusco.

**Curso:** Algoritmos Avanzados (2026-II) · UNSAAC  
**Grupo 5:** Choquenaira Q., Porroa S., Quispe R., Yaranga A.  
**Repositorio Oficial:** [https://github.com/frankich99/PROYECTO_Algoritmos-Avanzados-UNSAAC](https://github.com/frankich99/PROYECTO_Algoritmos-Avanzados-UNSAAC)

## Estructuras Comparadas

| Estructura | Decrease-Key | Extract-Min | Dijkstra Total |
|:--|:--|:--|:--|
| Binary Heap Indexado | O(log V) | O(log V) | O((V+E) log V) |
| 4-ary Heap (d=4) | O(log₄ V) | O(4 log₄ V) | O((4V+E) log₄ V) |
| Fibonacci Heap | O(1) amort. | O(log V) amort. | O(V log V + E) |

## Ejecución

```bash
cd python/
pip install -r requirements.txt

# Ejecutar pipeline completo
python main.py

# Ejecutar tests
pytest tests/ -v
```

## Salidas

Tras ejecutar `python main.py`:

- `results/tables/`: Tablas LaTeX (aristas, traza, benchmark)
- `results/figures/`: Figuras PNG (mapa, escalabilidad, comparativas)
- `data/processed/`: Datos JSON (red vial, benchmark)

## Estructura del Proyecto

```
python/
├── main.py                         # Pipeline principal
├── requirements.txt
├── src/
│   ├── algorithms/dijkstra.py      # Dijkstra con inyección de cola
│   ├── datastructures/
│   │   ├── indexed_min_heap.py     # Binary Heap + tabla de posiciones
│   │   ├── d_ary_heap.py           # Heap d-ario (d=4)
│   │   └── fibonacci_heap.py       # Fibonacci Heap
│   ├── models/cusco_network.py     # Red: 6 nodos, 9 aristas
│   ├── utils/
│   │   ├── cost_model.py           # Impedancia andina (α=2.5)
│   │   └── latex_exporter.py       # Exportador de tablas
│   ├── benchmarks/
│   │   └── scalability_benchmark.py
│   └── visualization/
│       └── generate_figures.py
├── tests/
│   ├── test_dijkstra.py            # 11+ tests unitarios
│   └── conftest.py
├── data/processed/                 # Datos generados
└── results/                        # Tablas y figuras generadas
```

## Instancia Base

Red del Centro Histórico del Cusco con 6 nodos y 9 aristas dirigidas:

```
A (Plaza Mayor) ──180m──> B (Regocijo) ──220m──> D (San Francisco)
       │                      │                       │
     450m                   400m                    250m
       ↓                      ↓                       ↓
C (Qorikancha) ──350m──> F (Limacpampa)          E (San Pedro)
```

Distancias mínimas desde A: B=180, D=400, C=450, E=650, F=800 metros.
