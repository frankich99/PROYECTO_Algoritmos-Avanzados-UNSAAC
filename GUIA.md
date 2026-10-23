# GUÍA RÁPIDA DE SUSTENTACIÓN: AVANCES 4 Y 5
**Proyecto:** Rutas Mínimas con Colas de Prioridad en Redes Viales Urbanas del Cusco  
**Curso:** Algoritmos Avanzados (UNSAAC - 2026-II) · **Grupo 5**  
**Docente:** Ing. Héctor Eduardo Ugarte Rojas  

---

## 1. Respuestas Precisas para las Preguntas del Docente

### A. Topografía del Cusco y "Dijkstra Modificado"
* **¿Cómo se modela la topografía y el trazado urbano?**
  1. **Calles de un solo sentido:** El grafo es estrictamente dirigido ($E \subseteq V \times V$). Si la calle Espaderos va de $A \to B$, una ambulancia no puede ir $B \to A$ porque la calzada colonial no permite el paso en contraflujo.
  2. **Calles angostas y pasajes coloniales:** Tienen velocidad nominal reducida ($15\text{ km/h}$ en calles céntricas coloniales como Marqués o Santa Clara, y $8\text{ km/h}$ en peatonales como Loreto, frente a $35\text{ km/h}$ en avenidas amplias como Tullumayo o El Sol).
  3. **Pendientes andinas (subidas):** Se aplica un modelo de impedancia con penalización por gradiente positivo:
     $$\Phi = 1.0 + 2.5 \cdot \max(0, \text{pendiente}/100)$$
     En subidas pronunciadas, los vehículos pesados de emergencia sufren sobreesfuerzo motriz crítico. En bajadas la penalización es nula ($\max = 0$).
* **¿Qué es el "Dijkstra Modificado"?**
  Es el algoritmo de Dijkstra optimizando **tiempo de viaje efectivo con impedancia topográfica** (`--metric time`) en lugar de la distancia puramente geométrica en metros (`--metric distance`). Permite que el sistema elija avenidas más largas pero planas y fluidas en vez de callejones coloniales empinados y angostos.

---

### B. Objetivos del Proyecto (Orden Secuencial Estricto)
El proyecto sigue el ciclo de vida de la ingeniería de software y análisis de algoritmos en 4 fases:
1. **OE1 (Modelar):** Grafo dirigido del Centro Histórico, calles dirigidas, angostura e impedancia topográfica andina ($\alpha = 2.5$).
2. **OE2 (Diseñar e Implementar):** Arquitectura desacoplada en 4 capas y Dijkstra con inyección de tres colas de prioridad puras (Min-Heap Binario Indexado, 4-ary Heap y Fibonacci Heap).
3. **OE3 (Verificar):** Validación analítica manual, certificado de optimalidad independiente $O(|V|+|E|)$ y suite automatizada de 219 pruebas AAA contra oráculos de referencia (NetworkX y Bellman-Ford).
4. **OE4 (Evaluar e Investigar):** Batería experimental de escalabilidad, micro-benchmarks de CPU y análisis de jerarquía de memoria caché L1/L2 vs punteros dinámicos.

---

### C. Alcance y Delimitación
* **Delimitación Espacial:** Centro Histórico del Cusco (6 intersecciones estratégicas: Plaza Mayor, Regocijo, Qorikancha, San Francisco, San Pedro, Limacpampa). Justificación: concentra la mayor densidad de giros obligados, vías angostas y fuertes pendientes. El sistema está desacoplado y listo para escalar a toda la ciudad mediante ingesta de OpenStreetMap vía OSMnx.
* **Delimitación Algorítmica:** Grafos dirigidos estáticos con pesos no negativos ($w(e) \ge 0$). Bellman-Ford se incluye como referencia para verificar y comparar criterios con pesos negativos.

---

### D. Comparativa de las 3 Alternativas y Rol de NetworkX
* **1. Binary Min-Heap Indexado:** $O((|V|+|E|)\log |V|)$. Arreglo contiguo en memoria y diccionario inverso de posiciones `pos` $O(1)$. Estándar canónico y base de comparación.
* **2. 4-ary Heap ($d=4$):** $O((4|V|+|E|)\log_4 |V|)$. Reduce la altura a la mitad ($\log_4 |V| = 0.5 \log_2 |V|$). Un nodo y sus 4 hijos caben contiguos en una línea de caché de CPU (64 bytes). Hace un 40% menos intercambios de memoria, superando en velocidad al binario a partir de $N \approx 500$ nodos.
* **3. Fibonacci Heap:** $O(|E| + |V|\log |V|)$ amortizado. Óptimo asintótico teórico ($O(1)$ amortizado en `Decrease-Key`). Sin embargo, en redes viales dispersas ($|E| \approx 3.5|V|$), la sobrecarga de alocar objetos dinámicos en memoria y seguir punteros dispersos genera fallos de caché (*cache misses*), haciéndolo más lento en la práctica que los heaps basados en arreglos contiguos.
* **¿Qué rol cumple NetworkX?**
  **NetworkX NO se usa para resolver el problema** (las 3 colas y Dijkstra fueron programados 100% desde cero). NetworkX se utiliza únicamente como **oráculo canónico externo de prueba** (*ground truth oracle*) en la suite automatizada para certificar que nuestras implementaciones propias arrojan resultados exactos.

---

### E. Visualización y Herramientas Gráficas
* **¿Con qué se grafica?**
  * Con **Graphviz** (archivos `.dot` nativos y renderizados vectoriales) para la topología de la red vial, sentidos de giro y rutas óptimas resaltadas.
  * Con **Matplotlib** para las métricas, diagramas de arquitectura y curvas experimentales de escalabilidad.
  * **No se usa Plotly** por requerimiento de ligereza y determinismo vectorial en entornos académicos.

---

### F. Arquitectura del Software: 4 Capas Lógicas Desacopladas
1. **Capa 1 (Modelos Viales y Datos):** `models/cusco_network.py`, `utils/cost_model.py`, `data/processed/cusco_centro_network.json`.
2. **Capa 2 (Estructuras de Datos):** `datastructures/base.py`, `indexed_min_heap.py`, `d_ary_heap.py`, `fibonacci_heap.py`.
3. **Capa 3 (Algoritmos y Verificación):** `algorithms/dijkstra.py`, `algorithms/reference.py`, `verification/certificate.py`.
4. **Capa 4 (Presentación, CLI y Pruebas):** `cli.py`, `main.py`, `visualization/generate_figures.py` (Graphviz y Matplotlib) y `tests/`.

---

### G. Repositorio Oficial y Versionamiento en GitHub
* **URL Oficial:** [https://github.com/frankich99/PROYECTO_Algoritmos-Avanzados-UNSAAC](https://github.com/frankich99/PROYECTO_Algoritmos-Avanzados-UNSAAC)
* **Estructura de Ramas:**
  * `main`: Versión estable consolidada.
  * `ramaFRANKI`: Arquitectura modular y prototipo base (Noe Choquenaira).
  * `ramaAldo`: Suite de pruebas QA, Fibonacci Heap, CLI y guías de avance (Aldo Yaranga).
  * `ramaYeni`: Análisis de stack y montículo d-ario (Yeni Porroa).
  * `RamaRomario`: Pruebas preliminares de escalabilidad (Romario Quispe).

---

## 2. Guion de Demostración: Comandos Paso a Paso

Ejecuta todos los comandos desde la carpeta `python/`:
```bash
cd python
```

### Paso 1: Mostrar alternativas disponibles
```bash
python main.py list
```
> **Qué decir:** *"El sistema expone una interfaz común con tres colas de prioridad puras más el algoritmo canónico de Bellman-Ford como referencia."*

---

### Paso 2: Ejecutar Dijkstra Modificado en la Red de Cusco (Comparativa)
```bash
python main.py compare --metric time
```
> **Qué decir:** *"Procesamos la red vial con las 4 alternativas bajo la métrica tiempo (Dijkstra modificado con topografía andina). Todas arrojan distancias idénticas (veredicto EQUIVALENTES) y certificados de optimalidad válidos, mostrando las diferencias de operaciones primitivas de cada cola."*

---

### Paso 3: Demostrar cómo la topografía cambia la ruta óptima
```bash
python main.py compare --metric distance
```
> **Qué decir:** *"Al comparar contra la distancia euclidiana pura, se aprecia cómo cambian los tiempos y el orden de evaluación frente a la métrica con impedancia andina."*

---

### Paso 4: Instancia Pequeña Resuelta Manualmente (Cormen CLRS Fig. 24.6)
```bash
python main.py run -i data/instances/clrs_24_6.txt --trace
```
> **Qué decir:** *"Demostramos el paso a paso exacto sobre el ejemplo clásico del libro de Cormen. Coincide exactamente con el orden de extracción (s, y, z, t, x) y las distancias manuales (0, 5, 7, 8, 9)."*

---

### Paso 5: Demostrar Salida Verificable (Certificado de Optimalidad)
```bash
python main.py run -i data/instances/clrs_24_6.txt -o results/clrs.json
python main.py verify -i data/instances/clrs_24_6.txt -r results/clrs.json
```
> **Qué decir:** *"Exportamos la solución a JSON y el certificador comprueba las condiciones de Bellman en $O(|V|+|E|)$ de forma independiente sin volver a ejecutar Dijkstra."*

---

### Paso 6: ¿El docente dicta un grafo en la pizarra durante la sesión?
```bash
python main.py run --inline "A B 4; A C 1; C B 2; B D 5; C D 8" -s A -q all
```
*(Si es un grafo no dirigido, agrega el flag `--undirected` al final).*  
> **Qué decir:** *"El sistema permite resolver al instante cualquier grafo ingresado en vivo por línea de comandos para las 3 alternativas simultáneamente."*

---

### Paso 7: Demostrar Manejo de Entradas Inválidas
```bash
python main.py run -i data/instances/invalidas/peso_negativo.txt
python main.py run -i data/instances/invalidas/json_mal_formado.json
python main.py run -s NODO_INEXISTENTE
```
> **Qué decir:** *"El módulo de validación previa detecta de inmediato archivos con pesos negativos, formatos corruptos o vértices inexistentes, devolviendo un mensaje explicativo y código de salida 2."*

---

### Paso 8: Generación y Visualización con Graphviz (.dot)
```bash
python main.py graphviz --target E
```
> **Qué decir:** *"Generamos el archivo de especificación vectorial `.dot` de Graphviz en `results/figures/ruta_optima_cusco.dot`, resaltando el camino mínimo hacia San Pedro (A -> B -> D -> E) en trazo verde grueso y estilizando los nodos."*

---

### Paso 9: Batería de 219 Pruebas Automatizadas con Pytest
```bash
python -m pytest -v
```
> **Qué decir:** *"Ejecutamos la suite automatizada con 219 pruebas que cubren casos básicos, de borde, límites, adversos y de equivalencia cruzada contra NetworkX y Bellman-Ford."*

---

### Paso 10: Menú Interactivo Guiado (Opcional)
```bash
python main.py menu
```
> **Qué decir:** *"Disponemos de un menú de consola interactivo para navegar por todas las funciones sin necesidad de memorizar parámetros."*

---

## 3. Demostración en Google Colab (1 Clic)

1. Ingresar a [Google Colab](https://colab.research.google.com/).
2. Cargar el archivo `python/colab/rutas_minimas_cusco.ipynb`.
3. Seleccionar **Entorno de ejecución > Ejecutar todas**.
4. **Qué muestra:**
   * Implementación pura de las 3 colas de prioridad.
   * Cálculo de rutas del Centro Histórico del Cusco.
   * **Diagrama interactivo vectorial con Graphviz** integrado nativamente en el cuaderno.
   * Gráficos comparativos de Distancia vs. Tiempo de Emergencia.
   * Curvas experimentales de escalabilidad asintótica.
