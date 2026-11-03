# Rutas Mínimas con Colas de Prioridad en Redes Viales Urbanas del Cusco

[![Python 3.12](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-278%20passed-brightgreen.svg)](python/tests/)
[![Documento](https://img.shields.io/badge/informe-LaTeX-orange.svg)](latex/main.pdf)
[![Red OSM](https://img.shields.io/badge/OSM-891%20nodos%20%7C%202139%20aristas-informational.svg)](python/data/processed/cusco_osm_drive.json)

**Universidad Nacional de San Antonio Abad del Cusco (UNSAAC)**  
**Facultad de Ingeniería Eléctrica, Electrónica, Informática y Mecánica**  
**Escuela Profesional de Ingeniería Informática y de Sistemas**  
**Asignatura:** Algoritmos Avanzados (Semestre 2026-II)  
**Docente Revisor:** Ing. Héctor Eduardo Ugarte Rojas

---

## Integrantes del Grupo 5

| Integrante | Código | Aportes verificables en Git |
| :--- | :---: | :--- |
| **Noe Franklin Choquenaira Quispe** | **133962** | Dijkstra, heap binario y modelo didáctico (`592589a`); $A^*$ (`b307be4`); informe (`f0799bf`). |
| **Aldo Yaranga Achahui** | **103179** | Pruebas, cuaderno y exportadores (`d50e67b`); CLI y pruebas de CLI (`65d303d`). |
| **Yeni Ruth Porroa Sivana** | **120893** | Heap 4-ario (`77983b7`); análisis de estructuras (`3b91a5e`). |
| **Romario Quispe Rimachi** | **164257** | Fibonacci heap y benchmark inicial (`72df976`); actualización preliminar de resultados (`e3af921`). |

La integración OSM, el clima, el certificado y la aplicación se incluyen en
el commit **grupal** `7922f52` (28/10); el commit no acredita autoría personal
de esos componentes. Seguimiento y defensa individual: [control de entrega](docs/CONTROL_ENTREGA.md).

---

## Enlaces rápidos

* **[latex/main.pdf](latex/main.pdf):** informe académico con 14 partes, referencias y anexos.
* **[GUIA.md](GUIA.md):** guía breve de sustentación con respuestas y comandos.
* **[docs/CONTROL_ENTREGA.md](docs/CONTROL_ENTREGA.md):** requisitos, evidencias individuales pendientes y calendario interno hasta el 04/11/2026.
* **[docs/DATOS_Y_MODELO.md](docs/DATOS_Y_MODELO.md):** procedencia, unidades y alcance de la web y del experimento canónico.
* **[python/app.py](python/app.py):** aplicación Streamlit integrada con mapas cartográficos OpenStreetMap.
* **[python/scripts/reproduce_canonical.py](python/scripts/reproduce_canonical.py):** regeneración del benchmark, del caso OSM, de las tablas y de las figuras.
* **[colab/rutas_minimas_cusco.ipynb](colab/rutas_minimas_cusco.ipynb):** cuaderno didáctico de 26 celdas listo para Google Colab. No es la fuente de los resultados canónicos del informe.

---

## 1. Problema y modelo

Se modela una red vial urbana como un dígrafo dirigido $G=(V,E)$ con pesos no negativos. La siguiente fórmula corresponde a la **instancia ilustrativa de seis nodos**:

$$
w(u,v)=\frac{L(u,v)}{v_{\text{nom}}(u,v)}\left(1+2.5\max\left(0,\theta(u,v)\right)\right)m_{\text{clima}},
$$

donde $L$ es la longitud en metros, $v_{\text{nom}}$ la velocidad nominal, $\theta$ una **pendiente supuesta** y $m_{\text{clima}}\ge 1$ un escenario uniforme. La red OSM usa `travel_time_sec` del snapshot, **sin pendiente ni congestión por tramo**. El tráfico horario de la aplicación es un supuesto global, no una medición ni una ruta distinta. La métrica de distancia usa $w=L$. Detalles y unidades: [datos y modelo](docs/DATOS_Y_MODELO.md).

Se comparan tres colas dentro del mismo Dijkstra:

| Cola | Complejidad de referencia | Resultado medido |
| :--- | :--- | :--- |
| **Binary Heap indexado** | $O((V+E)\log V)$ | Menor mediana en 3 de 10 escalas sintéticas y en la consulta OSM. Opción por defecto. |
| **4-ary Heap indexado ($d=4$)** | $O((V+E)\log_4 V)$ con 4 comparaciones por nivel | Menor mediana en 7 de 10 escalas; razón mediana 0.964 (disperso) y 0.954 (denso). Los IQR se solapan en las 10 escalas. |
| **Fibonacci Heap** | $O(E+V\log V)$ amortizado | Ninguna victoria; 1.05--1.59 veces más lento que el binario en las escalas medidas. |

$A^*$ se incluye como extensión para consultas punto a punto. Usa una heurística euclidiana escalada y consistente; en la consulta OSM redujo las expansiones de 887 a 823 (7.2 %) sin cambiar el costo. Bellman-Ford y NetworkX se usan como oráculos independientes, no como solvers del sistema.

---

## 2. Resultados principales

* **Benchmark canónico:** 1350 muestras cronometradas (2 perfiles $\times$ 5 escalas $\times$ 3 instancias $\times$ 3 colas $\times$ 15 repeticiones). Se reportan mediana e IQR; no se declara un ganador cuando los intervalos se solapan.
* **Perfil disperso ($E=4V$):** el 4-ario ganó 3 de 5 escalas; el binario, 2. La razón mediana 4-ario/binario fue 0.964.
* **Perfil denso ($E=0.08V(V-1)$):** el 4-ario ganó 4 de 5 escalas; el binario, 1. La razón mediana fue 0.954.
* **Consulta OSM:** 891 vértices y 2139 aristas. Tiempos medianos: Binary 15.65 ms, 4-ary 19.87 ms (+26.9 %), Fibonacci 26.09 ms (+66.7 %). Ruta de 17 vértices, 2810.6 m y 387.197 s de costo base.
* **$A^*$:** 823 expansiones frente a 887 de Dijkstra punto a punto; costo idéntico.
* **Clima:** el snapshot de Open-Meteo produce $m_{\text{clima}}=1.0691$ y un tiempo ajustado de 413.952 s (+6.91 %). La ruta no cambia porque el factor es uniforme.
* **Campos no registrados:** la observación histórica usada en `applied_results.json` no contiene humedad ni presión. El código usa 50 % solo como valor de reserva para humedad y no calcula presión faltante. El archivo local posterior de OpenWeatherMap sí incluye humedad y presión de suelo: es otra fuente y otra fecha. No hay resultado canónico de congestión.
* **No se midieron métricas de memoria.** Las cotas espaciales del informe son teóricas.

---

## 3. Aplicación Streamlit

La aplicación recupera cinco secciones accesibles desde la navegación, sin la barra superior de despliegue de Streamlit. Las dos primeras siguen siendo las tareas centrales:

1. **Ruta:** seleccionar recorrido o nodos OSM, costo, Dijkstra o $A^*$ y cola; contrastar las tres colas con $A^*$ sobre la misma consulta (sin afirmar tiempos), visualizar un plano local sin teselas o un mapa base opcional, y descargar la secuencia CSV. Clima histórico, snapshot local, consulta temporal y horario simulado son **escenarios uniformes**, no aforos por tramo.
2. **Comparación:** filtrar topología y escalas, ver medianas, IQR y relación frente al heap binario; descargar CSV e importar temporalmente un benchmark compatible. El archivo externo no acredita que las colas hayan usado las mismas instancias.
3. **Clima y tráfico:** separar el Open-Meteo histórico del informe y la lectura OpenWeatherMap local posterior, explorar supuestos horarios y consultar opcionalmente un proveedor o un segmento TomTom.
4. **Traza manual:** recorrer cada extracción de Dijkstra con distancias, predecesores, relajaciones y certificado de optimalidad; exportar CSV.
5. **Datos y método:** revisar fuentes, protocolo, límites del estudio y descargar el informe PDF si está presente.

Las consultas de API no escriben en los datos del informe. Si una clave se expuso, rótela antes de usar la integración: la web exige introducir explícitamente una clave nueva en el campo de contraseña; la CLI puede usar `OPENWEATHERMAP_API_KEY` tras sustituir la anterior. Nunca guarde claves en Git.

```bash
cd python
..\.venv\Scripts\python.exe -m streamlit run app.py
```

La interfaz usa Plotly para la red y los gráficos interactivos. El cálculo y el plano local funcionan sin Internet; solo el mapa base necesita teselas externas. Graphviz exporta `.dot` desde la CLI.

---

## 4. Instalación y ejecución

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r python/requirements.txt
```

### Suite de pruebas

```bash
.\.venv\Scripts\python.exe -m pytest python/tests -q
```

Última ejecución de esta revisión: **278 pruebas aprobadas**. Cubren las colas, oráculos, certificado, CLI, OSM, clima, validación de benchmark importado y las cinco secciones de la aplicación.

### CLI

```bash
cd python
..\.venv\Scripts\python.exe main.py list
..\.venv\Scripts\python.exe main.py compare --metric time
..\.venv\Scripts\python.exe main.py astar --target E
..\.venv\Scripts\python.exe main.py run -i data/instances/clrs_24_6.txt --trace
..\.venv\Scripts\python.exe main.py run --inline "A B 4; A C 1; C B 2; B D 5; C D 8" -s A -q all
```

### Reproducción canónica

Para regenerar tablas y figuras **sin alterar** los JSON de mediciones del
28/10/2026:

```bash
.\.venv\Scripts\python.exe python/scripts/reproduce_canonical.py --skip-benchmark --skip-applied
```

Para repetir el benchmark completo, ejecutar **en una copia separada**:

```bash
.\.venv\Scripts\python.exe python/scripts/reproduce_canonical.py
```

El comando completo sobrescribe `benchmark_results.json` y
`applied_results.json` con tiempos nuevos; las mediciones históricas no son
idénticas en otra máquina o fecha.

### Informe

```powershell
cd latex
.\compilar.ps1
```

---

## 5. Estructura del repositorio

```text
.
├── GUIA.md
├── README.md
├── colab/
│   ├── README.md
│   └── rutas_minimas_cusco.ipynb   # Cuaderno didáctico para Google Colab
├── latex/
│   ├── main.tex
│   ├── main.pdf
│   ├── capitulos/                  # 14 secciones y anexos
│   ├── tablas/                     # tablas usadas por el informe
│   └── figuras/                    # figuras usadas por el informe
└── python/
    ├── app.py              # aplicación Streamlit
    ├── main.py             # CLI y demostración
    ├── scripts/
    │   └── reproduce_canonical.py
    ├── data/
    │   ├── instances/      # instancia ilustrativa y casos de prueba
    │   └── processed/      # snapshots OSM, clima y resultados JSON
    ├── src/
    │   ├── algorithms/     # Dijkstra, A* y referencias
    │   ├── datastructures/ # Binary, 4-ary y Fibonacci
    │   ├── benchmarks/     # protocolo canónico y caso aplicado
    │   ├── io/             # carga y validación de grafos y OSM
    │   ├── services/       # Open-Meteo y factor climático
    │   ├── verification/   # certificado de optimalidad
    │   └── visualization/  # figuras y Graphviz
    └── tests/              # 278 pruebas
```

---

## 6. Limitaciones

* Los tiempos corresponden a Python 3.12 en un AMD Ryzen 5 5600H; no son extrapolables a otro lenguaje o CPU.
* No se midió memoria residente ni número de asignaciones.
* El benchmark usa redes sintéticas y una sola consulta OSM; no representa todas las distribuciones de tráfico.
* Open-Meteo entrega datos de modelo, no de una estación física. El clima se aplica como factor uniforme y no puede cambiar la ruta óptima.
* La instancia de seis nodos es ilustrativa: los nombres son reales, pero longitudes, pendientes y topología son esquemáticas.

---

## 7. Licencia y créditos

Proyecto desarrollado con fines estrictamente académicos para la asignatura de **Algoritmos Avanzados (2026-II)** de la **Universidad Nacional de San Antonio Abad del Cusco (UNSAAC)**.

Docente: **Ing. Héctor Eduardo Ugarte Rojas**  
Grupo 5: **Choquenaira Q., Yaranga A., Porroa S., Quispe R.**
