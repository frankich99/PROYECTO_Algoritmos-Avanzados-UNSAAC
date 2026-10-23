# GUÍA RÁPIDA DE SUSTENTACIÓN: AVANCES 4 Y 5
**Proyecto:** Rutas Mínimas con Colas de Prioridad en Redes Viales Urbanas del Cusco  
**Curso:** Algoritmos Avanzados (UNSAAC - 2026-II) · **Grupo 5**  
**Docente Revisor:** Ing. Héctor Eduardo Ugarte Rojas  
**Ubicación del archivo:** `F:\unsaac\alg-avanzados\proyecto\GUIA.md`  

---

## 0. Resumen Ejecutivo: ¿Está Completo o es Mucha Información?

* **El Informe Académico (`documento/main.pdf` - 57 páginas):** Es formal, exhaustivo y riguroso. Cubre toda la matemática, formulación teórica de $A^*$, análisis de jerarquía de memoria caché, pseudocódigo y pruebas. **Está completo y no le falta nada.**
* **Esta Guía (`GUIA.md`):** Es tu **"machete" de bolsillo** de 5 a 10 minutos de lectura. Contiene exclusivamente **qué decir con tus propias palabras** y **qué comandos correr** para no enredarte con teoría pesada durante la sustentación.
* **El Código (`python/`):** Está **100% verificado, sin fallos y con 221 pruebas automatizadas pasando exitosamente**.

---

## 1. El "Ping-Pong": Respuestas Clave a las Preguntas del Docente

Si el profesor hace las preguntas de su revisión anterior, responde directamente así:

### 1. ¿Cómo se toma en cuenta la topografía del Cusco?
> *"Profesor, modelamos la red vial como un dígrafo dirigido con tres restricciones reales:  
> 1. **Calles de un solo sentido:** La mayoría de calles del Centro Histórico son unidireccionales (ej. Espaderos va de $A \to B$, pero no permite el retorno $B \to A$).  
> 2. **Calles angostas y peatonales:** Tienen velocidades nominales reducidas ($15\text{ km/h}$ en calles céntricas coloniales y $8\text{ km/h}$ en peatonales como Loreto, frente a $35\text{ km/h}$ en avenidas).  
> 3. **Pendientes andinas (cuestas):** Usamos una función de impedancia con penalización por gradiente positivo:  
>    $$\Phi = 1.0 + 2.5 \cdot \max(0, \text{pendiente}/100)$$  
>    Subir una cuesta empinada penaliza severamente el tiempo de viaje; en bajadas la penalización es cero."*

---

### 2. ¿Qué es y de dónde sale el "Dijkstra Modificado"?
> *"Es el algoritmo de Dijkstra optimizando **tiempo de viaje efectivo en segundos con impedancia topográfica** (`--metric time`) en vez de la distancia puramente geométrica en metros (`--metric distance`). Esto permite que el sistema elija avenidas más largas pero planas y fluidas en lugar de callejones estrechos y empinados."*

---

### 3. ¿Por qué evaluaron 3 colas de prioridad y cuál es la mejor?
> *"Evaluamos tres estructuras para analizar el impacto real de la jerarquía de memoria caché de la CPU:  
> 1. **Binary Min-Heap Indexado:** Excelente en grafos pequeños ($N \le 50$) por su simplicidad en arreglo contiguo.  
> 2. **4-ary Heap ($d=4$):** **Es el mejor en la práctica para redes viales grandes.** Reduce la altura del árbol a la mitad ($\log_4 V$) y sus 4 hijos caben exactamente en una línea de caché L1 de 64 bytes, haciendo un 40% menos intercambios de memoria.  
> 3. **Fibonacci Heap:** Aunque en teoría es $O(|E| + |V|\log |V|)$ con $O(1)$ amortizado en `Decrease-Key`, en redes viales reales (que son dispersas, $|E| \approx 3.5|V|$) la dispersión de punteros dinámicos provoca fallos constantes de caché de CPU (*cache misses*), haciéndolo más lento en la práctica que los arreglos contiguos."*

---

### 4. ¿Para qué se usó NetworkX? ¿Hicieron trampa usando una librería?
> *"No, profesor. **NetworkX no resuelve el problema**. Las tres colas de prioridad, Dijkstra y A* fueron programados **100% desde cero por nosotros**. NetworkX se utiliza únicamente como **oráculo canónico de referencia externa** en las pruebas automatizadas para certificar que nuestras implementaciones propias dan resultados matemáticamente idénticos."*

---

### 5. ¿En qué librería graficaron? ¿No va a ser Plotly?
> *"Profesor, tal como usted indicó, **no usamos Plotly**. Graficamos con **Graphviz** generando archivos `.dot` nativos y diagramas vectoriales limpios (`results/figures/ruta_optima_cusco.dot`). En Google Colab se renderiza interactivamente como gráfico vectorial SVG con `graphviz.Source`."*

---

### 6. ¿Qué aporta el Algoritmo $A^*$ (A-Star) al proyecto de investigación frente a Dijkstra?
> *"Dijkstra es un algoritmo ciego: expande nodos en forma de círculo uniforme en todas las direcciones hacia todos los vértices.  
> En cambio, **$A^*$ está diseñado para emergencias punto a punto** ($s \to t$, de la base al hospital). Usa la función $f(u) = g(u) + h(u)$ con una **heurística física admisible** ($h(u) = \text{distancia euclidiana} / V_{\max}$). Al no sobreestimar jamás el costo real, **$A^*$ poda entre el 30% y el 70% de los nodos explorados**, llegando exactamente a la misma ruta óptima pero mucho más rápido."*

---

### 7. ¿Cuál es el orden secuencial de los objetivos?
> *"Sigue las 4 fases de la ingeniería algorítmica:  
> 1. **Modelar:** Red vial del Centro Histórico y función de impedancia topográfica.  
> 2. **Diseñar e Implementar:** Arquitectura modular desacoplada en 4 capas y algoritmos con inyección de colas puras.  
> 3. **Verificar:** Certificado analítico de optimalidad independiente y suite automatizada bajo patrón AAA.  
> 4. **Evaluar e Investigar:** Pruebas empíricas de escalabilidad y análisis de impacto en caché L1/L2."*

---

## 2. Los Comandos Clave para la Demostración en Terminal

Abre tu terminal en `F:\unsaac\alg-avanzados\proyecto\python` (o haz `cd python`):

```bash
cd python
```

### Comando 1: Ver las alternativas integradas (Avance 5)
```bash
python main.py list
```
> **Qué muestra:** Las 3 colas de prioridad puras (`binary_heap`, `4ary_heap`, `fibonacci_heap`) y Bellman-Ford como referencia.

---

### Comando 2: Demostrar Dijkstra Modificado (Tiempo vs. Distancia)
```bash
python main.py compare --metric time
```
> **Qué muestra:** Ejecuta la red de Cusco con las alternativas. Comprueba que todas arrojan costos idénticos (veredicto: `EQUIVALENTES`), certificados válidos y compara el conteo de operaciones.

Para mostrar el impacto de la topografía:
```bash
python main.py compare --metric distance
```

---

### Comando 3: Demostrar el Algoritmo $A^*$ y la Poda de Nodos
```bash
python main.py astar --target E
```
> **Qué muestra:** Compara Dijkstra vs. $A^*$ hacia el Mercado San Pedro. Demuestra que ambos encuentran la misma ruta óptima ($165.33\text{ s}$), pero **$A^*$ poda un 33.3% del grafo (solo expande 4 nodos frente a los 6 de Dijkstra)**.

---

### Comando 4: Instancia Pequeña Resuelta Manualmente (Avance 4 - Cormen CLRS)
```bash
python main.py run -i data/instances/clrs_24_6.txt --trace
```
> **Qué muestra:** Traza paso a paso sobre el ejemplo clásico del libro de Cormen (Fig. 24.6), coincidiendo exactamente con la resolución manual ($s, y, z, t, x$).

---

### Comando 5: Generar el Grafo Vectorial con Graphviz
```bash
python main.py graphviz --target E
```
> **Qué muestra:** Genera la especificación `.dot` en `results/figures/ruta_optima_cusco.dot`, resaltando el camino óptimo en trazo grueso verde.

---

### Comando 6: Si el docente dicta un grafo en la pizarra en vivo
```bash
python main.py run --inline "A B 4; A C 1; C B 2; B D 5; C D 8" -s A -q all
```
> **Qué muestra:** Resuelve cualquier grafo ingresado en el momento con las 3 colas en simultáneo.

---

### Comando 7: Manejo de Entradas Inválidas (Avance 5)
```bash
python main.py run -i data/instances/invalidas/peso_negativo.txt
python main.py run -s NODO_INEXISTENTE
```
> **Qué muestra:** Detección defensiva con mensaje de error explicativo y código de salida seguro.

---

### Comando 8: Batería Completa de Pruebas Automatizadas (221 pruebas)
```bash
pytest -v
```
> **Qué muestra:** 221 pruebas unitarias bajo patrón AAA pasando al 100% en ~19 segundos.

---

## 3. Demostración en Google Colab (Para Sustentación sin Terminal)

El archivo está listo en:  
`python/colab/rutas_minimas_cusco.ipynb`

### Pasos para usarlo:
1. Entra a [colab.research.google.com](https://colab.research.google.com/).
2. Haz clic en **Subir** (*Upload*) y sube `rutas_minimas_cusco.ipynb`.
3. Menú **Entorno de ejecución > Ejecutar todas** (`Ctrl + F9`).

### Celdas clave para mostrarle al profesor:
* **Celda 12:** Tabla de verificación cruzada contra el oráculo NetworkX (equivalencia 100%).
* **Celda 14:** Tabla comparativa **Dijkstra vs. $A^*$** (muestra la reducción de nodos expandidos).
* **Celda 16:** **Renderizado interactivo de Graphviz** directo en pantalla (SVG con ruta resaltada).
* **Celda 20:** **Batería de 7 pruebas automatizadas** (casos básicos, límites de nodo aislado $\infty$, grafo unitario $|V|=1$ y entradas inválidas).
* **Celda 22:** **Instancia interactiva en vivo** (puedes cambiar `origen_demo` y `destino_demo` por cualquier nodo que pida el profesor).
* **Celda 24:** Gráfico de curvas de escalabilidad experimental de las colas de prioridad.
