# Cuaderno Google Colab: Rutas Mínimas en Redes Urbanas del Cusco

Este directorio contiene el cuaderno interactivo de Jupyter (`.ipynb`) preparado para ejecutarse directamente en **Google Colab** o en cualquier entorno local con Jupyter Notebook / JupyterLab.

---

## Estructura del Cuaderno (`rutas_minimas_cusco.ipynb`)

El cuaderno cuenta con **26 celdas** (13 celdas explicativas en Markdown formal y 13 celdas de código reproducible), estructuradas para satisfacer al 100% las exigencias del **Avance 4**, **Avance 5** y las observaciones del docente revisor:

1. **Configuración del Entorno y Dependencias:** Instalación e importación de `networkx`, `graphviz` y `matplotlib`.
2. **Red Vial del Centro Histórico del Cusco y Función de Impedancia:** Definición de los 6 nodos clave, 9 tramos dirigidos con pendientes reales (+/- %) y función de impedancia andina ($\alpha = 2.5$).
3. **Implementación de Tres Colas de Prioridad con `Decrease-Key`:**
   - `IndexedMinHeap`: Montículo binario indexado con tabla de posiciones $O(1)$.
   - `DAryHeap`: Montículo cuaternario ($d=4$) contiguo en memoria, alineado a la línea de caché L1/L2.
   - `FibonacciHeap`: Montículo de Fibonacci con enlaces circulares dobles y cortes en cascada.
4. **Algoritmo de Dijkstra Parametrizado:** Inyección de dependencias (`queue_type`), telemetría de operaciones y reconstrucción de rutas.
5. **Algoritmo A\* ($A^*$):** Búsqueda orientada por heurística admisible y consistente basada en distancia euclidiana física dividida por $V_{\max}$ ($h(u) \le h^*(u)$).
6. **Resolución y Validación Cruzada en Cusco:** Equivalencia matemática estricta entre las 3 colas de prioridad y contrastación contra el oráculo `networkx.single_source_dijkstra_path_length`.
7. **Comparativa Dijkstra vs. A\*:** Evaluación empírica de poda de búsqueda y reducción de nodos expandidos hacia destinos estratégicos (Mercado San Pedro y Limacpampa).
8. **Visualización Vectorial con Graphviz:** Especificación DOT y renderizado interactivo SVG (`graphviz.Source`) con resaltado de la ruta crítica de emergencia.
9. **Visualizaciones Cartográficas y de Barras:** Topología vial en plano coordenado y gráfica comparativa de Distancia Física (m) vs. Tiempo con Pendiente (s).
10. **Batería de Pruebas Automatizadas (Requisito Avance 4):** 7 pruebas automatizadas con `assert` cubriendo casos básicos, límites (grafo desconectado, grafo unitario, caminos simétricos) y adversos (origen inexistente, pesos negativos).
11. **Demostración con Instancia Interactiva (Requisito Avance 5):** Permite al evaluador seleccionar dinámicamente cualquier par origen-destino y verificar la equivalencia instantánea.
12. **Banco de Pruebas Experimental de Escalabilidad:** Generación de redes sintéticas ($|V| \in [10, 500]$, $\bar{d} \approx 3.5$) y curvas de tiempo en microsegundos tras múltiples repeticiones.
13. **Discusión Técnica, Dificultades Encontradas y Trabajo Futuro:** Síntesis del comportamiento de la memoria caché, errores resueltos en sincronización de `Decrease-Key` y trabajo futuro con `OSMnx`.

---

## Cómo Ejecutarlo en Google Colab

1. Ingrese a [colab.research.google.com](https://colab.research.google.com/).
2. Seleccione la pestaña **Subir** (*Upload*) y cargue el archivo `rutas_minimas_cusco.ipynb`.
3. Ejecute las celdas secuencialmente con `Shift + Enter` o seleccione **Entorno de ejecución > Ejecutar todas**.
4. En la celda 11, puede modificar las variables `origen_demo` y `destino_demo` para probar cualquier ruta que solicite el docente en vivo.
