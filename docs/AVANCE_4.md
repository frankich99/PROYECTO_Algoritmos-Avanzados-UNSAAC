# Avance 4 — Implementación del primer algoritmo y estructura principal

**Alternativa 1:** algoritmo de Dijkstra con **Min-Heap binario indexado** (`IndexedMinHeap`).
Grupo 5 · Algoritmos Avanzados 2026-II · UNSAAC

Todos los comandos se ejecutan desde la carpeta `python/`.

---

## 1. Guion de demostración (directamente sobre el sistema)

| Paso | Comando | Qué se muestra |
|---|---|---|
| 1. Cargar instancia y ejecutar | `python main.py run --trace` | Red del Cusco (6 nodos, 9 tramos), métrica tiempo, origen A. Tabla de rutas, traza paso a paso, contadores y verificación. |
| 2. Instancia resuelta a mano | `python main.py run -i data/instances/clrs_24_6.txt --trace` | Ejemplo de Cormen (Fig. 24.6): s=0, y=5, z=7, t=8, x=9. Se compara en pizarra con la traza. |
| 3. Salida verificable | `python main.py run -i data/instances/clrs_24_6.txt -o results/clrs.json` y luego `python main.py verify -i data/instances/clrs_24_6.txt -r results/clrs.json` | El resultado se exporta a JSON y se valida **sin volver a ejecutar Dijkstra** (certificado de optimalidad). |
| 4. Generar instancia | `python main.py generate --type random --nodes 200 --seed 7 -o results/r200.json` y `python main.py run -i results/r200.json -t N150` | Generación reproducible con semilla y ejecución sobre ella. |
| 5. Entrada inválida | `python main.py run -i data/instances/invalidas/peso_negativo.txt` | Mensaje claro y código de salida 2 (Dijkstra exige pesos ≥ 0). |
| 6. Pruebas automatizadas | `python -m pytest tests/test_dijkstra_manual.py tests/test_priority_queues.py tests/test_validation_io.py -v` | Casos básicos, límite y adversos. |

### Salida esperada del paso 1 (resumen)

```
Instancia 'cusco_centro_time': |V|=6, |E|=9, métrica=time, origen=A: Plaza Mayor del Cusco
Destino                       | Costo    | Ruta óptima
A: Plaza Mayor del Cusco      | 0.00 s   | A
B: Plaza Regocijo (Cusipata)  | 44.82 s  | A -> B
C: Qorikancha (Santo Domingo) | 108.00 s | A -> C
D: Plaza San Francisco        | 101.58 s | A -> B -> D
E: Mercado Central San Pedro  | 165.33 s | A -> B -> D -> E
F: Plazoleta Limacpampa       | 144.45 s | A -> C -> F
Operaciones: insert_ops=6, extract_min_ops=6, decrease_key_ops=5, relax_attempts=8, ...
Verificación: OK (9 aristas sin relajación pendiente, 5 rutas con costo = distancia)
```

> Con la métrica **tiempo** hay 8 intentos de relajación; con **distancia** (`--metric distance`), 9.
> Con tiempo, el orden de extracción es A, B, D, C, F, E: cuando se extrae E, F ya es permanente y la
> arista E→F no se evalúa (línea 16 del pseudocódigo). Con distancia el orden es A, B, D, C, E, F.

---

## 2. Decisiones de implementación

1. **Interfaz abstracta de cola (`src/datastructures/base.py`).** Dijkstra solo conoce `insert`, `extract_min`, `decrease_key` e `is_empty`. La estructura se elige por nombre en un registro (`src/datastructures/registry.py`). Así la segunda alternativa (Avance 5) reutiliza exactamente el mismo código algorítmico.
2. **Tabla de posiciones `pos: vértice → índice`.** Es lo que permite `decrease_key` en O(log V): el vértice se ubica en O(1) y luego flota. Toda modificación del arreglo pasa por `_swap(i, j)`, que actualiza arreglo y tabla en la misma operación (evita la desincronización detectada en la Unidad 1).
3. **Inserción de todos los vértices al inicio (como `Q.BUILD`).** Se respetó el pseudocódigo del informe en lugar de la variante "lazy" con reinserciones; así cada vértice se extrae exactamente una vez y los conteos se comparan directamente con la traza manual.
4. **Contrato tolerante en `decrease_key`.** Si la nueva clave no es menor, o el vértice ya salió de la cola, la operación es un no-op. Dijkstra puede invocarla sin consultar antes.
5. **Validación previa (`src/io/graph_io.py`).** Antes de ejecutar se comprueba: grafo no vacío, ids únicos, destinos existentes, pesos numéricos, finitos y no negativos, origen existente. Los errores se informan con la arista o línea exacta.
6. **Salida verificable (`src/verification/certificate.py`).** Para pesos ≥ 0, `d` es la distancia mínima si y solo si: (a) `d[s]=0`; (b) ninguna arista admite relajación (`d[v] ≤ d[u]+w`); (c) cada vértice alcanzado tiene un predecesor que realiza su distancia; (d) cada ruta reportada existe y cuesta `d[v]`. La comprobación es O(V+E) e independiente del algoritmo.
7. **Implementación de referencia.** `bellman_ford` (programación dinámica sobre aristas, sin colas) y `dijkstra_array` (arreglo no ordenado, O(V²)). Además, en las pruebas se compara con `networkx` cuando está instalado.
8. **Traza opcional (`record_trace`).** La traza copia el estado completo en cada iteración (O(V) por paso, O(V²) total). Se activa para la demostración y las tablas LaTeX y se desactiva para medir.

### Estructuras de datos utilizadas

| Estructura | Dónde | Por qué |
|---|---|---|
| Lista de adyacencia `dict[v] → [(w, peso)]` | Grafo | Red vial dispersa (E ≈ 3V): recorre solo los vecinos reales. |
| Arreglo contiguo de pares `(clave, vértice)` | `IndexedMinHeap.heap` | Heap implícito: hijos en `2i+1`, `2i+2`, sin punteros. |
| Diccionario `vértice → índice` | `IndexedMinHeap.pos` | Ubicación O(1) para `decrease_key`. |
| Diccionarios `dist`, `prev` | Dijkstra | Distancias tentativas y árbol de caminos mínimos. |
| Conjunto `visited` | Dijkstra | Conjunto `S` de vértices permanentes. |

---

## 3. Correspondencia pseudocódigo ↔ código

Algoritmo 1 del informe (Sección 5) frente a `src/algorithms/dijkstra.py`. En el código cada línea lleva la etiqueta `[Lk]`.

| Línea | Pseudocódigo | Código |
|---|---|---|
| 1–6 | `d[v] ← ∞`, `π[v] ← NIL`, `d[s] ← 0` | `dist = {v: INF ...}`, `prev = {v: None ...}`, `dist[source] = 0.0` |
| 7 | `Q.BUILD(V, d)` | `heap = create_queue(queue_type)`; `heap.insert(v, dist[v])` para cada v |
| 8 | `S ← ∅` | `visited = set()` |
| 9 | `while not Q.IS_EMPTY()` | `while not heap.is_empty():` |
| 10 | `(u, d_u) ← Q.EXTRACT_MIN()` | `d_u, u = heap.extract_min()` |
| 11–13 | `if d_u = ∞: break` | `if d_u == INF: break` |
| 14 | `S ← S ∪ {u}` | `visited.add(u)` |
| 15–16 | `for (u,v) ∈ E: if v ∉ S` | `for v, weight in adj[u]: if v in visited: continue` |
| 17–18 | `cand ← d_u + W(u,v)`; `if cand < d[v]` | `candidate_d = d_u + weight`; `relaxed = candidate_d < old_d` |
| 19–21 | `d[v] ← cand`, `π[v] ← u`, `Q.DECREASE_KEY(v, d[v])` | `dist[v] = ...`, `prev[v] = u`, `heap.decrease_key(v, candidate_d)` |
| 26 | `return (d, π)` | Diccionario con `distances`, `predecessors` y, como extensión, `paths`, `stats`, `history`. |

---

## 4. Modificaciones respecto del diseño inicial (Unidad 1)

| # | Diseño inicial / estado anterior | Cambio | Motivo |
|---|---|---|---|
| 1 | Contrato de colas solo descrito en el informe; `extract_min` documentado como `(item, clave)` | Clase abstracta `PriorityQueue`; `extract_min` devuelve `(clave, item)`, como ya hacía el código | Una sola interfaz verificable por las pruebas; el informe se corrige. |
| 2 | `if/elif` por tipo de cola + `try/except ImportError` y una cola de respaldo `_FallbackBinaryHeap` | Registro de colas; sin importaciones silenciosas | El `try/except` ocultaba que `d_ary_heap.py` no existía: las pruebas fallaban al importar. |
| 3 | Sin validación de entradas | Capa de lectura y validación (JSON vial, JSON genérico, lista de aristas, en línea) | Requisito de manejo de entradas inválidas. |
| 4 | Traza siempre activa | `record_trace` y `build_paths` opcionales | La traza incluida en la medición distorsionaba el benchmark (O(V²)). |
| 5 | Claves de traza distintas entre módulos (`k`/`extracted` vs `iteration`/`extracted_node`) | Formato de traza único | `python main.py` terminaba con `KeyError: 'iteration'`. |
| 6 | Contadores `decrease_count` vs `decrease_key_ops` | Nombres unificados (con alias de compatibilidad) | El benchmark fallaba con `KeyError`. |
| 7 | Sin referencia ni verificador | `bellman_ford`, `dijkstra_array`, certificado de optimalidad | Validación objetiva de resultados. |
| 8 | Inserción duplicada o clave NaN aceptadas en silencio | Se rechazan con `ValueError` / `TypeError` | Un NaN rompe las comparaciones del heap sin dar error. |

---

## 5. Pruebas automatizadas

```
cd python
python -m pytest -v            # 219 pruebas, ~12 s
```

| Archivo | Tipo | Contenido |
|---|---|---|
| `test_dijkstra_manual.py` | Básicos y límite | Red del Cusco por distancia y por tiempo con los valores esperados escritos como aritmética manual; conteos 6/6/5/9 de la traza por distancia; CLRS 24.6; un solo nodo; inalcanzables; origen sin salidas; aristas de peso 0 y ciclos; lazos y aristas paralelas; pesos 1e12 y 1e-9; ids enteros; cadena de 3000 nodos. |
| `test_priority_queues.py` | Básicos, límite, adversos | Contrato común en las 3 colas: orden de extracción, decrease-key, cola vacía, claves iguales, duplicados, NaN y tipos inválidos; 3000 operaciones aleatorias contra un modelo con `heapq` (aridades 2, 3, 4 y 8); cortes en cascada; consolidación con 20 000 elementos. |
| `test_validation_io.py` | Adversos | Pesos negativos, NaN, ∞ y texto; nodos inexistentes o duplicados; JSON mal formado; archivos inexistentes o no UTF-8; extensión no soportada; el verificador detecta salidas manipuladas. |
| `test_dijkstra.py` | Unidad 1 | Suite original (ahora pasa: antes no importaba). |

### Validación con instancias resueltas manualmente

**Red del Cusco, métrica distancia (origen A):**
B = 180; D = 180+220 = 400; C = min(450, 180+400) = 450; E = min(400+250, 450+600) = 650; F = min(450+350, 650+700) = 800.

**Métrica tiempo:** `t = L / v · (1 + 2.5·max(0, p/100))`, con calle_centro 15 km/h y avenida 35 km/h:

| Tramo | Cálculo | Tiempo (s) |
|---|---|---|
| A→B | 180 / 4.167 × 1.0375 | 44.82 |
| A→C | 450 / 4.167 × 1 (bajada) | 108.00 |
| B→D | 220 / 4.167 × 1.075 | 56.76 |
| C→F | 350 / 9.722 × 1.0125 | 36.45 |
| D→E | 250 / 4.167 × 1.0625 | 63.75 |

Resultado: D = 44.82 + 56.76 = 101.58; E = 101.58 + 63.75 = 165.33; F = 108.00 + 36.45 = 144.45. El programa coincide exactamente.

**Instancia CLRS 24.6:** orden de extracción s, y, z, t, x; distancias 0, 5, 7, 8, 9.

---

## 6. Pendientes, errores conocidos y dificultades

**Funcionalidades pendientes**
- Red vial real del Cusco a mayor escala (p. ej. desde OpenStreetMap). Hoy el caso de estudio tiene 6 nodos; las instancias grandes son sintéticas.
- Pairing Heap: en el informe figura solo como perspectiva teórica.
- Interfaz gráfica: `streamlit` está en `requirements.txt` pero no se usa; la interfaz es la CLI y el menú (`python main.py menu`).

**Errores y limitaciones conocidos**
- El cuaderno de Colab duplica el código del prototipo de la Unidad 1 y no está sincronizado con `src/`.
- La tabla preliminar del Capítulo 10 (55.0 / 86.6 / 125.3 µs) no es reproducible con el repositorio, porque el 4-ary heap no existía. Debe reemplazarse por las mediciones del Avance 5.
- Los tiempos en Python incluyen el sobrecosto del intérprete; las comparaciones de rendimiento son relativas al entorno.

**Dificultades encontradas**
- Integrar módulos escritos por distintos integrantes sin un contrato ejecutable: las claves de diccionario no coincidían. Se resolvió con la interfaz abstracta y las pruebas de integración de la CLI.
- El `try/except ImportError` daba la impresión de que todo funcionaba aunque faltaba un módulo.
- Defecto latente en `FibonacciHeap._consolidate`: un arreglo de grados de tamaño fijo podía descartar árboles con n > ~65 000. No se observó en pruebas y se corrigió de forma preventiva.
