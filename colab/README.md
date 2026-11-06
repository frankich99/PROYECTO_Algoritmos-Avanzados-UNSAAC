# Cuaderno didáctico: rutas mínimas en Cusco

[`rutas_minimas_cusco.ipynb`](rutas_minimas_cusco.ipynb) contiene **58 celdas**
(33 de texto y 25 de código). Cada cola tiene su propia sección y celda de
implementación. El cuaderno implementa Dijkstra con tres colas y A* con una
heurística escalada para los pesos de la instancia, validación frente a NetworkX,
visualizaciones y **10 comprobaciones** ejecutables. La red de seis nodos usa
nombres de lugares reales; sus coordenadas, conexiones, longitudes, pendientes y
sentidos son **esquemáticos**. No es la fuente de los resultados OSM ni de los
**1350 tiempos** del banco canónico del 28/10/2026. Véase
[`docs/DATOS_Y_MODELO.md`](../docs/DATOS_Y_MODELO.md).

## Ejecución

1. Suba el archivo a [Google Colab](https://colab.research.google.com/) y use
   **Entorno de ejecución > Ejecutar todas**. La primera celda de código instala los
   paquetes Python `networkx`, `graphviz` y `matplotlib`. El diagrama Graphviz
   requiere además el ejecutable de sistema `dot`; cuando no esté disponible,
   se muestra la representación DOT textual.
2. Para una consulta distinta, cambie `origen_demo`, `destino_demo` y
   `metrica_demo` (`time` o `distance`) en la sección **11**, y vuelva a ejecutar
   esa celda. Para cambiar la red se deben modificar también las coordenadas
   y aristas correspondientes; A* calcula su escala con esos pesos.
3. En Jupyter local, instale los mismos paquetes y el ejecutable `dot` por
   separado si necesita el diagrama. El cuaderno no importa módulos del
   repositorio y no requiere rutas absolutas.

La sección **12** mide 15 repeticiones sobre una instancia sintética por tamaño;
reporta tiempo **transcurrido** en microsegundos, no CPU, memoria ni caché. Sus
medianas cambian al repetirlo en otra máquina. El caso canónico, con perfiles
disperso y denso, instancias múltiples y JSON de muestras, se reproduce desde
[`python/README.md`](../python/README.md) sin sobrescribir archivos históricos
en esta carpeta.

Las salidas guardadas se regeneraron en Jupyter local (Python 3.12) el
05/11/2026: las 24 celdas de cálculo y demostración terminaron, pasaron las 10 comprobaciones
y se obtuvo un SVG de Graphviz. En esa comprobación se omitió la línea `%pip`
porque las dependencias ya estaban instaladas; la línea sigue en el cuaderno
para cuando se suba a Colab. Esto no acredita una ejecución en la plataforma
Colab, los avances entregados ni la defensa individual ante el docente. La
copia de `python/colab/` debe permanecer sincronizada con esta.
