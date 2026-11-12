# Instancias de Prueba del Proyecto (UNSAAC - Algoritmos Avanzados)

Este directorio contiene instancias de grafos clasificadas de menor a mayor complejidad para verificar y contrastar los algoritmos de rutas mínimas (**Dijkstra con Montículo Binario, 4-ario y Fibonacci**, y **A***) tanto en la **interfaz Web** como mediante la **línea de comandos (CLI)**.

---

## 📁 Estructura del Directorio

```text
instancias_pruebas/
├── json/
│   ├── 01_simple_clrs.json               # 6 nodos, pesos planos abstractos (CLRS)
│   ├── 02_intermedio_cusco_centro.json    # 6 nodos, Centro Histórico con pendientes y calles
│   └── 03_complejo_cusco_urbano.json     # 15 nodos, Cusco ampliado (San Blas, Saphy, Wanchaq)
├── csv_txt/
│   ├── 01_simple_lineal.txt              # Formato de aristas 'u v w', bifurcaciones básicas
│   ├── 02_intermedio_cuadricula.csv      # Malla grid 3x3 (9 nodos), múltiples decrease-key
│   └── 03_complejo_topografia_cusco.txt  # 12 nodos de Cusco con relieve y tiempos de viaje
└── nodos_aristas/
    ├── 01_simple_tabla.txt               # Datos tabulados listos para copiar y pegar
    ├── 02_intermedio_tabla.txt           # Datos con coordenadas geográficas de Cusco
    └── 03_complejo_tabla.txt             # Red con 10 nodos para entrada manual directa
```

---

## 🚀 Cómo Usarlas en la Aplicación Web

1. Abre la aplicación web (en [GitHub Pages](https://frankich99.github.io/PROYECTO_Algoritmos-Avanzados-UNSAAC/) o localmente).
2. Ve a la pestaña **`Instancias`** en el menú superior.
3. Elige el modo según el formato que desees probar:
   * **Pestaña `JSON`:** Abre cualquiera de los archivos en `instancias_pruebas/json/`, copia su contenido y pégalo en el recuadro. Haz clic en **«Validar JSON y calcular»**.
   * **Pestaña `CSV / TXT`:** Haz clic en **«Seleccionar archivo»** y sube cualquier archivo de `instancias_pruebas/csv_txt/`, o pega el texto directamente. Haz clic en **«Validar lista y calcular»**.
   * **Pestaña `Nodos y aristas`:** Usa los datos de `instancias_pruebas/nodos_aristas/` para ingresar los vértices y aristas fila por fila. Haz clic en **«Validar tabla y calcular»**.

---

## 💻 Cómo Usarlas desde la Consola (Python CLI)

Desde la raíz del proyecto, puedes ejecutar cualquier instancia con Dijkstra o Bellman-Ford y comparar las tres colas de prioridad:

```powershell
# 1. Probar instancia JSON simple
python -m src.cli run --file instancias_pruebas/json/01_simple_clrs.json --source A --target F

# 2. Comparar las 3 colas de prioridad sobre la red con relieve de Cusco
python -m src.cli compare --file instancias_pruebas/json/02_intermedio_cusco_centro.json --source A --target F --metric time

# 3. Probar instancia TXT / CSV
python -m src.cli run --file instancias_pruebas/csv_txt/01_simple_lineal.txt --source A --target F

# 4. Certificar optimalidad matemática contra Bellman-Ford
python -m src.cli verify --file instancias_pruebas/json/03_complejo_cusco_urbano.json --source A
```

---

## 🏔️ Alcance de las Variables de Cusco (Topografía y Relieve)

> **Nota de procedencia:** Los archivos de `instancias_pruebas/` son instancias **didácticas e ilustrativas** para pruebas manuales y de interfaz. Sus longitudes, pendientes y coordenadas aproximadas permiten demostrar la fórmula del modelo de costos (`CuscoCostModel`), pero **no sustituyen** un levantamiento geoespacial ni velocidades medidas de tráfico. Para la red real extraída de OpenStreetMap, utilice los snapshots revisados en `python/data/processed/`.

* **Pendiente positiva (subida):** En el modelo de costo vial ilustrativo (`CuscoCostModel`), las subidas penalizan el tiempo de viaje mediante la fórmula:
  $$\text{Penalización} = 1 + 2.5 \times \max\left(0, \frac{\text{pendiente \%}}{100}\right)$$
* **Pendiente negativa (bajada):** No incrementa ni reduce adicionalmente el tiempo base de viaje en la fórmula aplicada.
* **Jerarquía de vías del modelo ilustrativo:** Avenidas principales (`avenida`, 35 km/h), calles del centro (`calle_centro`, 15 km/h) y pasajes peatonales (`peatonal`, 8 km/h). En los snapshots OSM reales (`cusco_osm_drive.json`), los tiempos base provienen de `travel_time` de OSMnx o `length_m / maxspeed` según la etiqueta `highway`.
