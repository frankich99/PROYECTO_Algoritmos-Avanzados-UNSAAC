# Rutas Mínimas con Colas de Prioridad en Redes Viales Urbanas del Cusco

[![Python 3.12](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-246%20passed-brightgreen.svg)](python/tests/)
[![Documento](https://img.shields.io/badge/documento-50%20p%C3%A1ginas-orange.svg)](documento/main.pdf)
[![Red OSM](https://img.shields.io/badge/OSM-891%20nodos%20%7C%202139%20aristas-informational.svg)](python/data/processed/cusco_osm_drive.json)
[![License](https://img.shields.io/badge/license-Acad%C3%A9mica%20UNSAAC-lightgrey.svg)](LICENSE)

**Universidad Nacional de San Antonio Abad del Cusco (UNSAAC)**  
**Facultad de Ingeniería Eléctrica, Electrónica, Informática y Mecánica**  
**Escuela Profesional de Ingeniería Informática y de Sistemas**  
**Asignatura:** Algoritmos Avanzados (Semestre 2026-II)  
**Docente Revisor:** Ing. Héctor Eduardo Ugarte Rojas

---

## Integrantes del Grupo 5

| Integrante | Código | Responsabilidad principal |
| :--- | :---: | :--- |
| **Noe Franklin Choquenaira Quispe** | **133962** | Arquitectura modular, modelo de costo, algoritmo $A^*$, aplicación Streamlit y coordinación del informe. |
| **Aldo Yaranga Achahui** | **103179** | Pruebas automatizadas, certificado de optimalidad, CLI, aplicación y documentación. |
| **Yeni Ruth Porroa Sivana** | **120893** | Heap binario indexado y heap 4-ario indexado; análisis de localidad de memoria. |
| **Romario Quispe Rimachi** | **164257** | Fibonacci heap, protocolo de benchmark, carga OSM y servicio meteorológico. |

---

## Enlaces rápidos

* **[documento/main.pdf](documento/main.pdf):** informe académico de 50 páginas (38 de cuerpo), 14 secciones, referencias y anexos.
* **[GUIA.md](GUIA.md):** guía breve de sustentación con respuestas y comandos.
* **[python/app.py](python/app.py):** aplicación Streamlit integrada.
* **[python/scripts/reproduce_canonical.py](python/scripts/reproduce_canonical.py):** regeneración del benchmark, del caso OSM, de las tablas y de las figuras.
* **[python/colab/rutas_minimas_cusco.ipynb](python/colab/rutas_minimas_cusco.ipynb):** cuaderno didáctico de 26 celdas. No es la fuente de los resultados canónicos del informe.

---

## 1. Problema y modelo

Se modela una red vial urbana como un dígrafo dirigido $G=(V,E)$ con pesos no negativos. Para la métrica de tiempo, el costo de una arista es

$$
w(u,v)=\frac{L(u,v)}{v_{\text{nom}}(u,v)}\left(1+2.5\max\left(0,\theta(u,v)\right)\right)m_{\text{clima}},
$$

donde $L$ es la longitud en metros, $v_{\text{nom}}$ la velocidad nominal, $\theta$ la pendiente como fracción y $m_{\text{clima}}\ge 1$ un factor uniforme de sensibilidad meteorológica. La métrica de distancia usa $w=L$. El modelo no es una calibración de tránsito: la pendiente y el clima son escenarios explícitos.

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
* **No se midieron métricas de memoria.** Las cotas espaciales del informe son teóricas.

---

## 3. Aplicación Streamlit

La aplicación integra cuatro vistas:

1. **Comparación:** curvas de mediana e IQR por perfil y tabla de resultados.
2. **Ruta OSM:** cálculo interactivo de Dijkstra o $A^*$ sobre el snapshot local, con o sin factor climático.
3. **Traza manual:** ejecución paso a paso sobre la instancia ilustrativa de seis nodos.
4. **Procedencia:** protocolo, fuentes, snapshots y actualización opcional de Open-Meteo.

```bash
cd python
..\.venv\Scripts\python.exe -m streamlit run app.py
```

La interfaz usa Plotly para las visualizaciones interactivas y Graphviz para exportar especificaciones `.dot`. Los gráficos de la aplicación no dependen de teselas externas: la red se dibuja desde el snapshot local.

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

Resultado esperado: **246 pruebas aprobadas**. La suite cubre el contrato de las tres colas, la equivalencia con Bellman-Ford y NetworkX, el certificado de optimalidad, la CLI, OSM, el clima y la aplicación.

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

```bash
.\.venv\Scripts\python.exe python/scripts/reproduce_canonical.py
```

El script ejecuta el protocolo del informe, reutiliza los snapshots OSM y meteorológico y escribe los JSON, las tablas de `documento/tablas/` y las figuras de `documento/figuras/`. Para regenerar solo tablas y figuras:

```bash
.\.venv\Scripts\python.exe python/scripts/reproduce_canonical.py --skip-benchmark --skip-applied
```

### Informe

```powershell
cd documento
.\compilar.ps1
```

---

## 5. Estructura del repositorio

```text
.
├── GUIA.md
├── README.md
├── documento/
│   ├── main.tex
│   ├── main.pdf
│   ├── capitulos/          # 14 secciones y anexos
│   ├── tablas/             # tablas usadas por el informe
│   └── figuras/            # figuras usadas por el informe
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
    └── tests/              # 246 pruebas
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
