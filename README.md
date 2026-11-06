# Rutas Mínimas con Colas de Prioridad en Redes Viales Urbanas del Cusco

[![Python 3.12](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![Versión](https://img.shields.io/badge/versi%C3%B3n-v1.5.0-blue.svg)](CHANGELOG.md)
[![Tests](https://img.shields.io/badge/tests-296%20passed-brightgreen.svg)](python/tests/)
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
* **[docs/CONTROL_ENTREGA.md](docs/CONTROL_ENTREGA.md):** estado técnico al 05/11/2026 y evidencias individuales pendientes; sin calendario retrospectivo de reuniones.
* **[docs/DATOS_Y_MODELO.md](docs/DATOS_Y_MODELO.md):** procedencia, unidades y alcance de la web y del experimento canónico.
* **[docs/DESPLIEGUE.md](docs/DESPLIEGUE.md):** build de producción, paquete publicable y despliegue en Docker, Render o Railway.
* **[CHANGELOG.md](CHANGELOG.md):** historial de versiones; la versión actual es **v1.5.0**.
* **[web/](web/):** aplicación oficial React + TypeScript con API FastAPI, mapas MapLibre e instrucciones en [web/README.md](web/README.md).
* **[python/scripts/build_publicable.py](python/scripts/build_publicable.py):** genera la carpeta y el ZIP publicables con backend, datos y web compilada.
* **[python/scripts/reproduce_canonical.py](python/scripts/reproduce_canonical.py):** regeneración del benchmark, del caso OSM, de las tablas y de las figuras.
* **[colab/rutas_minimas_cusco.ipynb](colab/rutas_minimas_cusco.ipynb):** cuaderno didáctico organizado por modelo, tres colas, Dijkstra, A*, validación y experimento para Colab o Jupyter local; no produce el banco canónico. Véase [su guía](colab/README.md).

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

## 3. Aplicación web

La interfaz oficial es **React + TypeScript** (`web/`), conectada a la API **FastAPI** (`python/web_api.py`). La antigua aplicación Streamlit se retiró. Ocho vistas:

1. **Rutas:** elegir red OSM, instancia ilustrativa o grafo propio; seleccionar origen y destino por nodo o coordenadas; resolver con Dijkstra o $A^*$ y contrastar las tres colas. Permite clima histórico, snapshot local o consulta temporal, y hora simulada o actual como **escenarios uniformes**, no aforos por tramo.
2. **Instancias:** construir un grafo dirigido desde tabla, JSON o lista de aristas TXT/CSV, o generarlo con semilla. Los pesos genéricos se muestran como «peso», no como metros o segundos.
3. **Comparar:** revisar el banco canónico por perfil y escala, y agregar consultas de la sesión sin mezclarlas con el experimento histórico.
4. **Experimentos:** medir redes sintéticas nuevas, separadas del informe y etiquetadas como resultados de sesión.
5. **Cobertura Cusco:** consultar el centro de 1,5 km o el centro ampliado de 3 km; cada uno declara su alcance y ninguno representa todo Cusco.
6. **Evidencias:** revisar la suite de pruebas, la red vial, el benchmark, el informe PDF y el repositorio.
7. **Datos y método:** revisar fuentes, fórmulas, límites, verificación y enlaces al contrato OpenAPI.
8. **Acerca de:** ficha institucional, integrantes del Grupo 5, arquitectura web/API/móvil, stack con versiones y alcance.

Las consultas de API no escriben en los datos del informe. Las claves de OpenWeatherMap y TomTom se configuran en `.env` del servidor y no se envían al navegador; la web permite una clave alternativa opcional para una consulta. Si una clave se expuso, rótela y actualice `.env`. Nunca guarde claves en Git.

En **dos terminales**, desde la raíz y desde `web/`:

```powershell
.\.venv\Scripts\python.exe -m uvicorn web_api:app --app-dir python --host 127.0.0.1 --port 8000
```

```powershell
cd web
npm run dev
```

Abrir <http://127.0.0.1:5173/>. Vite reenvía `/api`, `/docs` y `/openapi.json` al backend. La visualización usa MapLibre; el cálculo y el plano local funcionan sin Internet, y solo el mapa base de calles necesita teselas externas. Graphviz exporta `.dot` desde la CLI.

Para producción, un solo proceso sirve la web compilada y la API en el mismo
origen:

```powershell
cd web
npm run build
cd ..
.\.venv\Scripts\python.exe -m uvicorn web_api:app --app-dir python --host 0.0.0.0 --port 8000
```

Abrir <http://127.0.0.1:8000/>. El paquete publicable se genera con
`python/scripts/build_publicable.py` y se explica en [docs/DESPLIEGUE.md](docs/DESPLIEGUE.md).

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

Última ejecución de esta revisión: **289 pruebas aprobadas**. Cubren las colas, oráculos, certificado, CLI, OSM, clima, validación de benchmark importado y la API de la web nueva.

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
├── web/                  # React, TypeScript y mapa MapLibre
│   ├── README.md         # Inicio de FastAPI + Vite y cobertura real
│   └── src/              # Formularios, resultados y visualización
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
    ├── web_api.py          # API FastAPI; reutiliza python/src/
    ├── main.py             # CLI y demostración
    ├── scripts/
    │   ├── reproduce_canonical.py
    │   ├── build_urban_snapshot.py   # snapshot ampliado con revisión previa
    │   └── build_publicable.py       # backend + datos + web compilada en un ZIP
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
    └── tests/              # 289 pruebas (incluida la API web)
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
