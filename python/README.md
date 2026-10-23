# Prototipo Computacional: Rutas Mínimas en Redes Viales del Cusco

Implementación modular en Python del **Algoritmo de Dijkstra Parametrizado** y la **Búsqueda Heurística A\*** ($A^*$) sobre la red vial urbana del Centro Histórico del Cusco, con inyección desacoplada de tres estructuras de cola de prioridad puras y una referencia canónica independiente.

[![Python 3.12](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-221%20passed-brightgreen.svg)](tests/)
[![Google Colab](https://img.shields.io/badge/Colab-26%20celdas-yellow.svg)](colab/rutas_minimas_cusco.ipynb)

**Asignatura:** Algoritmos Avanzados (2026-II) · UNSAAC  
**Grupo 5:** Choquenaira Q. Noe (Líder), Yaranga A. Aldo, Porroa S. Yeni Ruth, Quispe R. Romario  
**Guías de Sustentación:** [GUIA.md](../GUIA.md) · [Avance 4](../docs/AVANCE_4.md) · [Avance 5](../docs/AVANCE_5.md)

---

## 1. Alternativas de Solución y Algoritmos Integrados

| Nombre en la CLI | Algoritmo / Estructura | Inserción | Decrease-Key | Extract-Min | Complejidad SSSP | Propósito en el Proyecto |
|:--|:--|:--|:--|:--|:--|:--|
| `binary_heap` | **Binary Min-Heap Indexado** | $O(\log V)$ | $O(\log V)$ | $O(\log V)$ | $O((V+E)\log V)$ | Línea base canónica en arreglo contiguo + tabla `pos` $O(1)$. |
| `4ary_heap` | **4-ary Heap Contiguo ($d=4$)** | $O(\log_4 V)$ | $O(\log_4 V)$ | $O(4 \log_4 V)$ | $O((4V+E)\log_4 V)$ | **Óptimo para redes viales grandes ($N \ge 500$):** alta localidad de caché L1 (64B). |
| `fibonacci_heap` | **Fibonacci Heap Dinámico** | $O(1)$ | $O(1)$ amort. | $O(\log V)$ amort. | $O(E + V\log V)$ | Cota teórica óptima mediante postergación perezosa y árboles dinámicos. |
| `astar` | **Algoritmo $A^*$ (A-Star)** | $O(\log V)$ | $O(\log V)$ | $O(\log V)$ | Depende de $h(u)$ | **Ruteo de emergencia punto a punto ($s \to t$):** poda del 30% al 70% de nodos. |
| `bellman_ford` | **Bellman-Ford (Referencia)** | — | — | — | $O(V \cdot E)$ | Oráculo independiente para validar consistencia matemática y ciclos negativos. |

---

## 2. Instalación y Requisitos

Requiere **Python 3.10** o superior:

```bash
cd python

# Crear y activar entorno virtual
python -m venv .venv
# En Windows:
.venv\Scripts\activate
# En Linux/macOS:
source .venv/bin/activate

# Instalar dependencias científicas y de pruebas
pip install -r requirements.txt
```

---

## 3. Comandos de la Interfaz Unificada (CLI)

El punto de entrada es `main.py`, que ofrece subcomandos para todas las funcionalidades:

```bash
# Ejecutar demostración completa del sistema:
python main.py

# Listar las alternativas de algoritmos y colas disponibles:
python main.py list

# Ejecutar Dijkstra en la red de Cusco con métrica de tiempo (Dijkstra Modificado):
python main.py run --metric time

# Ejecutar Dijkstra con métrica física de distancia pura:
python main.py run --metric distance

# Demostración del Algoritmo A* hacia el Mercado Central San Pedro ('E'):
python main.py astar --target E

# Exportar especificación vectorial Graphviz (.dot) con ruta resaltada:
python main.py graphviz --target E

# Comparativa de las 3 colas de prioridad sobre la red de Cusco:
python main.py compare --metric time

# Instancia pequeña resuelta manualmente (Cormen CLRS 3ra Ed. Fig. 24.6):
python main.py run -i data/instances/clrs_24_6.txt --trace

# Salida verificable con certificado de optimalidad independiente de Bellman:
python main.py run -i data/instances/clrs_24_6.txt -o results/r.json
python main.py verify -i data/instances/clrs_24_6.txt -r results/r.json

# Resolver grafo personalizado dictado en vivo por el docente durante la sesión:
python main.py run --inline "A B 4; A C 1; C B 2; B D 5; C D 8" -s A -q all

# Generar redes sintéticas reproducibles con semilla pseudoaleatoria:
python main.py generate --type random --nodes 300 --seed 42 -o results/sintetico_300.json

# Ejecutar banco de pruebas de escalabilidad experimental:
python main.py benchmark --scales 50 100 250 500 --runs 5

# Menú interactivo guiado por consola:
python main.py menu
```

### Códigos de Salida Seguros
- `0`: Ejecución y verificación correctas.
- `1`: Falla en verificación o divergencia de certificados.
- `2`: Entrada inválida detectada por validación defensiva (pesos negativos, JSON mal formado, nodo inexistente).

---

## 4. Batería de Pruebas Automatizadas (Pytest)

Las 221 pruebas automatizadas siguen el patrón **AAA (Arrange - Act - Assert)**:

```bash
python -m pytest -v
```

Cobertura de pruebas:
- `test_cli.py`: Validación de la interfaz CLI, comandos, flags y exportación de Graphviz.
- `test_dijkstra.py`: Correctitud del algoritmo de Dijkstra e inyección de colas.
- `test_dijkstra_manual.py`: Validación contra instancias manuales (Cormen CLRS 24.6) y casos de borde.
- `test_equivalence.py`: Equivalencia estricta entre Binary Heap, 4-ary Heap, Fibonacci Heap y NetworkX.
- `test_priority_queues.py`: Invariantes de montículo, inserción, extracción mínima y `decrease_key`.
- `test_validation_io.py`: Detección defensiva de pesos negativos, ciclos y nodos inexistentes.

---

## 5. Cuaderno Google Colab

En el directorio `colab/` se incluye el cuaderno interactivo `rutas_minimas_cusco.ipynb` (26 celdas), el cual puede ejecutarse directamente en la nube:
- Implementación completa de las 3 colas de prioridad puras.
- Algoritmo Dijkstra desacoplado y algoritmo $A^*$.
- Visualización interactiva vectorial con **Graphviz** (`graphviz.Source`).
- Suite de 7 pruebas unitarias ejecutadas directamente en el cuaderno.
- Celda interactiva en vivo para evaluar cualquier par origen-destino propuesto durante la sustentación.
- Gráficos de escalabilidad empírica de tiempos de CPU en microsegundos.
