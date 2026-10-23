# Avance 5 — Segunda alternativa e integración del sistema

**Alternativa 2:** Dijkstra con **4-ary Heap indexado** (`DAryHeap`, d = 4) y con **Fibonacci Heap** (`FibonacciHeap`), las dos estructuras previstas en el diseño. Ambas usan las mismas entradas, el mismo formato de salida y el mismo código de Dijkstra que la alternativa 1.
**Referencia de validación:** Bellman-Ford.

Todos los comandos se ejecutan desde la carpeta `python/`.

---

## 1. Guion de demostración

| Paso | Comando | Qué se muestra |
|---|---|---|
| 1. Interfaz común | `python main.py list` | Alternativas seleccionables por nombre: `binary_heap`, `4ary_heap`, `fibonacci_heap`, `bellman_ford`, `all`. |
| 2. Instancia pequeña con todas las alternativas | `python main.py compare --metric distance` | Red del Cusco: distancias por alternativa, veredicto **EQUIVALENTES**, contadores por estructura y certificado OK para las 4. |
| 3. Seleccionar una alternativa | `python main.py run -q fibonacci --trace` | Misma entrada y misma salida que el Avance 4, ahora con otra cola. |
| 4. Diferencias explicadas | `python main.py compare -i data/instances/empates_grid_3x3.json` | Distancias iguales; rutas distintas **con el mismo costo** (empates). |
| 5. **Instancia propuesta en la sesión** | `python main.py run --inline "A B 4; A C 1; C B 2; B D 5; C D 8" -s A -q all` o `python main.py menu` → opción 4 | El docente dicta las aristas y se ejecutan las tres alternativas al momento. Para un grafo no dirigido se agrega `--undirected`. |
| 6. Entrada inválida | `python main.py run -i data/instances/invalidas/json_mal_formado.json` y `python main.py run -s ZZ` | El mismo módulo de validación rechaza la entrada para todas las alternativas (código de salida 2). |
| 7. Criterios distintos | `python main.py run -i data/instances/invalidas/peso_negativo.txt` y luego `-q bellman_ford` | Dijkstra rechaza los pesos negativos (precondición); Bellman-Ford los resuelve. |
| 8. Escalabilidad | `python main.py benchmark --scales 100 500 1000 2000 5000 --runs 7` | Tabla LaTeX, JSON y figura en `results/benchmark/`. |
| 9. Pruebas | `python -m pytest tests/test_equivalence.py tests/test_cli.py -v` | Equivalencia con 40 grafos aleatorios contra Bellman-Ford y `networkx`, e integración de la CLI. |

---

## 2. Integración: módulos reutilizados por todas las alternativas

```
 main.py / src/cli.py   (run · compare · generate · verify · benchmark · menu · demo)
          │
          ├── src/io/graph_io.py                    lectura (JSON vial, JSON genérico, TXT/CSV, en línea) + validación
          ├── src/generators/instance_generator.py  instancias aleatorias, cuadrículas y cuadrículas viales (semilla fija)
          ├── src/algorithms/registry.py            solve(instancia, origen, método)  ← interfaz común
          │       ├── dijkstra.py ── datastructures/registry.py ─┬─ IndexedMinHeap   (alternativa 1)
          │       │                                              ├─ DAryHeap(d=4)    (alternativa 2)
          │       │                                              └─ FibonacciHeap    (alternativa 2b)
          │       └── reference.py  (Bellman-Ford, Dijkstra con arreglo)
          ├── src/verification/certificate.py       certificado de optimalidad + comparación clasificada
          ├── src/utils/measurement.py              medición de tiempos (calentamiento + n pasadas)
          └── src/utils/presentation.py             tablas en consola, exportación/lectura de JSON
```

- **Mismo formato de entrada:** cualquier archivo que acepte una alternativa lo aceptan todas (`load_instance`).
- **Mismo formato de salida:** `distances`, `predecessors`, `paths`, `stats`, `elapsed_ms`; exportable con `-o` y verificable con `verify`.
- **Mismo código algorítmico:** las colas se inyectan por nombre en `dijkstra_solver`. Una diferencia de distancias solo podría venir de la cola, y eso es lo que comprueban las pruebas.

### Manejo de entradas inválidas

| Entrada | Mensaje (resumen) | Código |
|---|---|---|
| Archivo inexistente, directorio, extensión no soportada, no UTF-8 | `No existe el archivo...`, `Extensión no soportada...` | 2 |
| JSON mal formado | `JSON mal formado en X (línea L, columna C)` | 2 |
| Línea con campos de menos o de más | `Línea 2: se esperaban 3 campos...` | 2 |
| Peso no numérico, NaN o infinito | `el peso 'abc' no es numérico` | 2 |
| Peso negativo (Dijkstra) | `peso negativo... use 'bellman_ford'` | 2 |
| Ciclo negativo (Bellman-Ford) | `Ciclo de peso negativo alcanzable desde A` | 2 |
| Vértice no declarado o repetido; origen o destino inexistente | `el vértice 'X' no fue declarado`, `El vértice origen 'ZZ' no existe` | 2 |
| Alternativa desconocida | `Método no soportado: 'pairing'` | 2 |
| Resultado manipulado (`verify`) | `FALLÓ: (b) arista u->v: d[v] > d[u]+w` | 1 |

---

## 3. Equivalencia y explicación de diferencias

**Propiedad esperada.** Con pesos no negativos, Dijkstra es exacto con cualquier cola, así que las distancias deben coincidir con las de Bellman-Ford para todo vértice (tolerancia relativa 1e-6). `compare_results` clasifica cada diferencia:

| Tipo de diferencia | Clasificación | Explicación |
|---|---|---|
| Distancia distinta en algún vértice | **Error** | No debe ocurrir. Ninguna prueba ni benchmark lo ha registrado. |
| Ruta distinta con el mismo costo | **Propiedad esperada** | Hay varios caminos óptimos. Dijkstra solo cambia `π[v]` ante una mejora estricta, así que la ruta depende de qué vértice empatado se extrae primero, y cada estructura desempata distinto. Ambas rutas pasan el certificado. |
| Distinto número de comparaciones, intercambios, enlaces o cortes | **Propiedad de cada estructura** | El 4-ary tiene la mitad de niveles, pero compara hasta 4 hijos al hundir; el Fibonacci difiere el trabajo a la consolidación. |
| Distinto número de `decrease_key` o de relajaciones (solo con empates) | **Propiedad esperada** | Depende del orden de extracción entre vértices de igual distancia. Ejemplo: con N = 5000, Fibonacci hizo 6309 `decrease_key` frente a 6310 de los heaps de arreglo, con distancias idénticas. |
| Dijkstra rechaza la instancia y Bellman-Ford la resuelve | **Criterio de solución distinto** | Dijkstra exige pesos ≥ 0 (invariante de la Sección 5); Bellman-Ford no. |

### Ejemplo de la sesión: cuadrícula 3×3 de pesos unitarios

```
Distancias: EQUIVALENTES
Rutas distintas con el mismo costo (empates; propiedad esperada, no es error):
  1_2 (costo 3.00): bellman_ford: 0_0->0_1->0_2->1_2 | binary_heap: 0_0->0_1->1_1->1_2
  2_1 (costo 3.00): bellman_ford: 0_0->0_1->1_1->2_1 | 4ary_heap:   0_0->1_0->2_0->2_1
  ...
```

### Red del Cusco (instancia pequeña procesada con todas las alternativas)

Distancias idénticas en las 4 alternativas y rutas idénticas (no hay empates). Contadores con la métrica distancia:

| Método | extract_min | decrease_key | relajaciones | comparaciones | propios |
|---|---|---|---|---|---|
| binary_heap | 6 | 5 | 9 | 23 | 5 intercambios |
| 4ary_heap | 6 | 5 | 9 | 25 | 3 intercambios |
| fibonacci_heap | 6 | 5 | 9 | 22 | 3 enlaces, 1 corte |
| bellman_ford | — | — | 18 | — | 2 rondas |

---

## 4. Resultados de escalabilidad (medidos con el repositorio)

`python main.py benchmark --scales 100 500 1000 2000 5000 --runs 7`, con grafos viales sintéticos de grado medio 3.5 (semilla 12345 + N). Python 3.13, x86_64. Tiempo medio en ms:

| \|V\| | \|E\| | Binary | 4-ary | Fibonacci | Comparaciones (bin / 4-ary / fib) |
|---|---|---|---|---|---|
| 100 | 350 | 0.50 | 0.52 | 0.69 | 1101 / 1347 / 844 |
| 500 | 1750 | 3.17 | 2.98 | 3.85 | 6835 / 8340 / 4853 |
| 1000 | 3500 | 7.42 | 6.84 | 8.94 | 14709 / 17914 / 10197 |
| 2000 | 7000 | 17.49 | 15.39 | 19.52 | 31548 / 37813 / 21202 |
| 5000 | 17500 | 50.94 | 49.11 | 48.80 | 85898 / 100730 / 55948 |

**Lectura.**
- El Fibonacci Heap hace siempre **menos comparaciones** (entre 23 % y 35 % menos), como predice su análisis amortizado, pero es más lento hasta N ≈ 2000 porque cada nodo es un objeto con 8 campos y punteros.
- El 4-ary hace **más comparaciones** que el binario y aun así es igual o más rápido desde N = 500: al tener la mitad de niveles hace ≈ 40 % menos intercambios (N = 5000: 27 603 frente a 46 311), y en Python cada intercambio, que también actualiza la tabla `pos`, cuesta más que una comparación.
- En N = 5000 las tres quedan dentro de una desviación estándar: no hay ganador concluyente a esa escala.
- Estos tiempos reemplazan la tabla preliminar del Capítulo 10, que no era reproducible.

---

## 5. Pruebas de la integración

| Archivo | Contenido |
|---|---|
| `test_equivalence.py` | 40 grafos aleatorios (pesos enteros con empates, reales y con aristas de peso 0) donde las 3 colas = Bellman-Ford y las 4 pasan el certificado; igualdad con `dijkstra_array` y `networkx`; empates producen rutas alternativas de igual costo; instancia de óptimo único sin diferencias; el comparador detecta un error real; d-ario con d = 2, 3, 5 y 16; escala de 1000 y 3000 nodos. |
| `test_cli.py` | Cada comando y cada alternativa; instancia en línea; códigos de salida 2 para entradas inválidas; generar → ejecutar → exportar → verificar, y verificar un resultado manipulado (código 1); benchmark; menú interactivo guiado. |

Total del repositorio: **219 pruebas**, todas aprobadas (`python -m pytest`).

Se comprobó además que la suite detecta errores reales: al introducir un fallo en el `_sift_down` del 4-ary heap (ignorar el último hijo), fallaron 54 pruebas.

---

## 6. Pendientes, errores conocidos y dificultades

**Pendientes**
- Pairing Heap (en el informe solo como perspectiva teórica).
- Red vial real a mayor escala; medición de memoria (`memory-profiler` está en `requirements.txt` pero no se usa).
- Sincronizar el cuaderno de Colab con `src/`.

**Errores y limitaciones conocidos**
- No hay errores de corrección abiertos: ninguna prueba ni benchmark registró distancias distintas.
- Los tiempos dependen del intérprete y de la máquina; para conclusiones de rendimiento conviene repetir el benchmark en el equipo de la sustentación.
- El conteo de `decrease_key` puede variar entre estructuras cuando hay empates (esperado, ver la Sección 3).

**Dificultades**
- Una prueba ingenua de "rutas idénticas" fallaba en cuadrículas por los empates: fue necesario separar la equivalencia de distancias (obligatoria) de la de rutas (solo si el óptimo es único).
- Medir sin contaminar: la traza y la reconstrucción de rutas dominaban el tiempo medido. Se separaron del núcleo con `record_trace` y `build_paths`.
