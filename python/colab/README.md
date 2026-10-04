# Cuaderno Google Colab: Rutas Mínimas en Redes del Cusco

Este directorio contiene el cuaderno interactivo de Jupyter (`.ipynb`) preparado para ejecutarse directamente en **Google Colab** o en cualquier entorno local con Jupyter Notebook / JupyterLab.

## Contenido del Cuaderno (`rutas_minimas_cusco.ipynb`)

1. **Configuración del entorno:** Importación de librerías (`matplotlib`, `networkx`, `time`, `math`).
2. **Red vial del Cusco:** Definición de los 6 nodos clave del Centro Histórico y función de impedancia topográfica ($\alpha=2.5$).
3. **Estructuras de colas de prioridad puras:**
   - `IndexedMinHeap`: Montículo binario indexado con tabla de posiciones $O(1)$.
   - `DAryHeap`: Montículo cuaternario ($d=4$) con alta localidad de caché.
   - `FibonacciHeap`: Montículo de Fibonacci con enlaces circulares y consolidación.
4. **Algoritmo de Dijkstra desacoplado:** Inyección de cualquiera de las tres colas de prioridad.
5. **Validación sobre Cusco:** Cálculo de rutas mínimas desde Plaza Mayor y verificación cruzada de distancias.
6. **Visualización:** Gráfico del grafo vial ponderado y gráfico de barras distancia vs. tiempo.
7. **Banco de pruebas de escalabilidad:** Generación de redes viales sintéticas ($|V| \in [10, 500]$) y curvas de tiempo en escala logarítmica.
8. **Discusión y conclusiones técnicas:** Síntesis del comportamiento de la memoria caché y costos asintóticos.

## Cómo ejecutarlo en Google Colab

1. Ingresar a [colab.research.google.com](https://colab.research.google.com/).
2. Seleccionar la pestaña **Subir** (*Upload*) y cargar el archivo `rutas_minimas_cusco.ipynb`.
3. Ejecutar las celdas secuencialmente con `Shift + Enter` o seleccionar **Entorno de ejecución > Ejecutar todas**.
