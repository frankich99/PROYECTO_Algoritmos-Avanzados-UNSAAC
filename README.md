# Rutas Mínimas con Colas de Prioridad en Redes Viales Urbanas del Cusco

[![Python 3.12](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-221%20passed%20(100%25)-brightgreen.svg)](python/tests/)
[![Documento](https://img.shields.io/badge/documento-60%20páginas%20(LaTeX)-orange.svg)](documento/main.pdf)
[![Google Colab](https://img.shields.io/badge/Google%20Colab-26%20celdas%20(interactivo)-yellow.svg)](python/colab/rutas_minimas_cusco.ipynb)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/frankich99/PROYECTO_Algoritmos-Avanzados-UNSAAC/blob/main/python/colab/rutas_minimas_cusco.ipynb)
[![License](https://img.shields.io/badge/license-Académica%20UNSAAC-lightgrey.svg)](LICENSE)

**Universidad Nacional de San Antonio Abad del Cusco (UNSAAC)**  
**Facultad de Ingeniería Eléctrica, Electrónica, Informática y Mecánica**  
**Escuela Profesional de Ingeniería Informática y de Sistemas**  
**Asignatura:** Algoritmos Avanzados (Semestre 2026-II)  
**Docente Revisor:** Ing. Héctor Eduardo Ugarte Rojas  

---

### Integrantes del Grupo 5 y Ramas de Trabajo

| Integrante | Código | Rol y Responsabilidad Principal | Rama en GitHub |
| :--- | :---: | :--- | :--- |
| **Noe Franklin Choquenaira Quispe** | **133962** | **Líder de Proyecto & Arquitecto:** Arquitectura modular desacoplada en 4 capas, diseño e implementación del **Algoritmo $A^*$** con heurística admisible, visualización vectorial con **Graphviz**, desarrollo del cuaderno **Google Colab** (26 celdas) e informe final de 60 páginas. | [`ramaFRANKI`](https://github.com/frankich99/PROYECTO_Algoritmos-Avanzados-UNSAAC/tree/ramaFRANKI) |
| **Aldo Yaranga Achahui** | **103179** | **QA & Validación:** Suite de 221 pruebas automatizadas bajo el patrón **AAA (Arrange-Act-Assert)**, implementación del certificador de optimalidad de Bellman $O(\|V\|+\|E\|)$ y opciones avanzadas de la interfaz CLI. | [`ramaAldo`](https://github.com/frankich99/PROYECTO_Algoritmos-Avanzados-UNSAAC/tree/ramaAldo) |
| **Yeni Ruth Porroa Sivana** | **120893** | **Estructuras de Datos & Caché:** Implementación y optimización de **`DAryHeap` ($d=4$)** alineado a líneas de caché de CPU (64 bytes), estudio comparativo de montículos y matriz de selección técnica. | [`ramaYeni`](https://github.com/frankich99/PROYECTO_Algoritmos-Avanzados-UNSAAC/tree/ramaYeni) |
| **Romario Quispe Rimachi** | **164257** | **Benchmarking & Modelado:** Generador de redes sintéticas reproducibles ($\bar{d} \approx 3.5$), protocolo experimental de escalabilidad en tiempo de CPU ($\mu s$) y calibración de la función de impedancia andina ($\alpha = 2.5$). | [`RamaRomario`](https://github.com/frankich99/PROYECTO_Algoritmos-Avanzados-UNSAAC/tree/RamaRomario) |

---

## 📌 Enlaces Rápidos del Proyecto

* 📖 **[GUIA.md](GUIA.md):** Guía rápida de sustentación oral (el "machete" con preguntas del docente y comandos en vivo).
* 📑 **[documento/main.pdf](documento/main.pdf):** Informe académico completo de **60 páginas** compilado en LaTeX con rigor matemático y experimental.
* 🚀 **[python/colab/rutas_minimas_cusco.ipynb](python/colab/rutas_minimas_cusco.ipynb):** Cuaderno interactivo listo para ejecutar en Google Colab con 26 celdas, Graphviz interactivo y batería de pruebas.
* 📋 **[docs/AVANCE_4.md](docs/AVANCE_4.md):** Guion de demostración y requisitos del Avance 4 (Algoritmo 1: Binary Min-Heap).
* 📋 **[docs/AVANCE_5.md](docs/AVANCE_5.md):** Guion de demostración y requisitos del Avance 5 (Segunda alternativa: 4-ary Heap, Fibonacci Heap, integración y equivalencia).

---

## 1. Descripción del Proyecto

El proyecto modela, implementa y evalúa experimentalmente algoritmos de rutas mínimas para la atención rápida de unidades de emergencia en la red vial urbana del **Centro Histórico de la ciudad del Cusco**, incorporando las particularidades geográficas y urbanísticas de la ciudad andina.

```
                              [Capa 4: Presentación y CLI]
                               (main.py, cli.py, tests/)
                                          │
                                          ▼
                         [Capa 3: Algoritmos y Verificación]
                      (dijkstra.py, a_star.py, certificate.py)
                                          │
                                          ▼
                       [Capa 2: Estructuras de Datos Puras]
                    (IndexedMinHeap, DAryHeap, FibonacciHeap)
                                          │
                                          ▼
                      [Capa 1: Modelos Viales y Datos Urbanos]
                      (cusco_network.py, cost_model.py, .json)
```

### Particularidades Topográficas del Cusco y "Dijkstra Modificado"
1. **Sentidos de circulación estrictos:** Calles coloniales estrechas donde el tránsito es estrictamente unidireccional (dígrafo dirigido $E \subseteq V \times V$).
2. **Calles angostas y peatonales:** Velocidades nominales diferenciadas ($8\text{ km/h}$ en pasajes peatonales como Loreto, $15\text{ km/h}$ en calles coloniales céntricas como Marqués o Santa Clara, y $35\text{ km/h}$ en avenidas como El Sol o Tullumayo).
3. **Pendientes andinas (subidas pronunciadas):** Se formula una función de costo e impedancia con penalización por gradiente positivo:
   $$\Phi(u, v) = 1.0 + 2.5 \cdot \max\left(0, \frac{\text{pendiente}(u, v)}{100}\right)$$
   El **Dijkstra Modificado** minimiza el **tiempo de viaje efectivo en segundos** (`--metric time`) en lugar de la distancia puramente geométrica en metros (`--metric distance`), permitiendo que el sistema priorice avenidas fluidas y planas sobre callejones empinados y estrechos.

### Algoritmo $A^*$ (Búsqueda Heurística Orientada a Objetivos)
Para el ruteo de emergencia punto a punto ($s \to t$, de la base al hospital), se implementó el algoritmo **$A^*$ (A-Star)** evaluando:
$$f(u) = g(u) + h(u)$$
Se formuló una **heurística física admisible y consistente**:
$$h(u, t) = \frac{\text{Distancia Euclídea}(u, t)}{V_{\max}} \quad \text{con } V_{\max} = 35\text{ km/h} \approx 9.72\text{ m/s}$$
Dado que $h(u) \le h^*(u)$ en todo momento, **$A^*$ garantiza la misma solución óptima podando entre el 30% y el 70% del espacio de búsqueda** (hacia Mercado San Pedro, Dijkstra expande 6 nodos mientras que $A^*$ solo necesita expandir 4 nodos).

---

## 2. Comparativa de Alternativas y Estructuras de Datos

Todas las estructuras fueron implementadas **100% desde cero** en Python puro sin dependencias de terceros para la resolución:

| Algoritmo / Estructura | Inserción | Extract-Min | Decrease-Key | Memoria / Caché | ¿Cuándo usarlo en el proyecto? |
| :--- | :---: | :---: | :---: | :--- | :--- |
| **Dijkstra + Binary Min-Heap** | $O(\log V)$ | $O(\log V)$ | $O(\log V)$ | Arreglo contiguo + tabla hash inversa `pos` | Redes pequeñas ($N \le 250$) y prototipado rápido. |
| **Dijkstra + 4-ary Heap ($d=4$)** | $O(\log_4 V)$ | $O(4 \log_4 V)$ | $O(\log_4 V)$ | Arreglo contiguo, 4 hijos alineados en línea de caché L1 (64B) | **Estructura recomendada para redes viales urbanas medianas y grandes ($N \ge 500$).** Reduce 40% los swaps. |
| **Dijkstra + Fibonacci Heap** | $O(1)$ | $O(\log V)$ amort. | $O(1)$ amort. | Listas circulares dobles dinámicas | Grafos densos ($E \gg V$). En redes viales dispersas ($E \approx 3.5V$) la sobrecarga de punteros degrada el rendimiento. |
| **Algoritmo $A^*$ (A-Star)** | $O(\log V)$ | $O(\log V)$ | $O(\log V)$ | Abanico elíptico orientado al destino | **Ruteo de emergencia punto a punto** ($s \to t$), reduciendo la cantidad de llamadas a la cola de prioridad. |
| **Bellman-Ford (Referencia)** | — | — | — | Arreglos lineales directos | Oráculo independiente para validar consistencia matemática ante aristas negativas ($O(V \cdot E)$). |
| **NetworkX (Oráculo)** | — | — | — | C-optimizado externo | **Oráculo externo de prueba** en el test suite automatizado para contrastar equivalencia estricta ($10^{-6}$). |

---

## 3. Visualización Vectorial con Graphviz

Atendiendo expresamente las observaciones académicas (*se descartó Plotly por su excesivo peso y dinamismo no determinista*), se integró el motor **Graphviz** para generar:
1. **Especificaciones `.dot` nativas:** Almacenadas en `python/results/figures/ruta_optima_cusco.dot`.
2. **Resaltado de ruta crítica:** Los tramos mínimos de emergencia se renderizan en trazo grueso rojo/verde con información de longitud (m), tiempo (s) y pendiente (+/- %).
3. **Renderizado vectorial SVG en Google Colab:** Se visualiza directamente en el navegador mediante `graphviz.Source`.

Comando para generar el diagrama:
```bash
python main.py graphviz --target E
```

---

## 4. Instrucciones de Instalación y Ejecución

### A. Ejecución del Prototipo en Python

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/frankich99/PROYECTO_Algoritmos-Avanzados-UNSAAC.git
   cd PROYECTO_Algoritmos-Avanzados-UNSAAC/python
   ```

2. **Crear entorno virtual e instalar dependencias:**
   ```bash
   python -m venv .venv
   # En Windows:
   .venv\Scripts\activate
   # En Linux/macOS:
   source .venv/bin/activate

   pip install -r requirements.txt
   ```

3. **Ejecutar la demostración integral:**
   ```bash
   python main.py
   ```

### B. Los Comandos Esenciales para Sustentación (CLI)

```bash
# 1. Comparativa de las 3 colas de prioridad con Dijkstra Modificado (Tiempo):
python main.py compare --metric time

# 2. Comparativa con métrica puramente física (Distancia):
python main.py compare --metric distance

# 3. Demostración del Algoritmo A* y poda de búsqueda frente a Dijkstra:
python main.py astar --target E

# 4. Exportar el grafo vial con ruta óptima en Graphviz (.dot):
python main.py graphviz --target E

# 5. Instancia pequeña resuelta manualmente (Cormen CLRS Fig. 24.6):
python main.py run -i data/instances/clrs_24_6.txt --trace

# 6. Grafo personalizado dictado en vivo por el docente:
python main.py run --inline "A B 4; A C 1; C B 2; B D 5; C D 8" -s A -q all

# 7. Demostración de manejo defensivo ante entradas inválidas:
python main.py run -i data/instances/invalidas/peso_negativo.txt
python main.py run -s NODO_INEXISTENTE

# 8. Menú de navegación interactivo por consola:
python main.py menu
```

### C. Ejecución de la Suite de Pruebas Automatizadas (AAA)

La suite de 221 pruebas automatizadas cubre casos básicos, límites (grafo desconectado $\infty$, grafo unitario $\|V\|=1$), adversos y equivalencia cruzada:

```bash
pytest -v
```
> **Resultado verificado:** `221 passed in 19.16s` (100% de éxito).

---

## 5. Demostración en Google Colab

El cuaderno interactivo está ubicado en [`python/colab/rutas_minimas_cusco.ipynb`](python/colab/rutas_minimas_cusco.ipynb) y cuenta con **26 celdas integrales**:

1. Ingrese a [Google Colab](https://colab.research.google.com/).
2. Cargue el archivo `rutas_minimas_cusco.ipynb` o ábralo directamente con el botón:  
   [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/frankich99/PROYECTO_Algoritmos-Avanzados-UNSAAC/blob/main/python/colab/rutas_minimas_cusco.ipynb)
3. Seleccione **Entorno de ejecución > Ejecutar todas** (`Ctrl + F9`).
4. **Celdas clave para la sustentación:**
   * **Celda 12:** Verificación cruzada estricta contra el oráculo `NetworkX`.
   * **Celda 14:** Comparativa **Dijkstra vs. $A^*$** (reducción en nodos expandidos).
   * **Celda 16:** **Renderizado vectorial SVG interactivo con Graphviz**.
   * **Celda 20:** **Batería de 7 pruebas unitarias automatizadas** con `assert`.
   * **Celda 22:** **Instancia interactiva en tiempo real** (permite evaluar cualquier origen y destino solicitado por el docente en vivo).
   * **Celda 24:** Curvas de escalabilidad experimental de tiempos de CPU ($\mu s$).

---

## 6. Estructura del Repositorio

```text
.
├── GUIA.md                               # Guía rápida de sustentación oral (preguntas y comandos)
├── README.md                             # Documentación principal del repositorio en GitHub
├── docs/                                 # Especificaciones de los avances del curso
│   ├── AVANCE_4.md                       # Especificación técnica del Avance 4 (Binary Heap)
│   └── AVANCE_5.md                       # Especificación técnica del Avance 5 (4-ary, Fibonacci, integración)
├── documento/                            # Informe formal académico en LaTeX (60 páginas)
│   ├── main.tex                          # Archivo raíz de LaTeX
│   ├── main.pdf                          # Informe final compilado en PDF
│   ├── compilar.ps1 / compilar.bat       # Scripts de compilación con pdflatex
│   ├── capitulos/                        # 14 capítulos temáticos y anexos
│   ├── tablas/                           # Tablas formales booktabs de trazas y complejidades
│   └── figuras/                          # Diagramas vectoriales, escudo y gráficos
└── python/                               # Núcleo del software científico ejecutable
    ├── main.py                           # Punto de entrada principal (demo y CLI)
    ├── requirements.txt                  # Dependencias de Python
    ├── colab/                            # Cuaderno interactivo Google Colab
    │   ├── rutas_minimas_cusco.ipynb     # Cuaderno de 26 celdas reproducible
    │   └── README.md                     # Guía de uso en Colab
    ├── data/                             # Instancias de prueba
    │   ├── processed/                    # Red del Centro Histórico y resultados benchmark
    │   └── instances/                    # CLRS 24.6, desconectado, empates e inválidas
    ├── src/                              # Código fuente modular en 4 capas
    │   ├── cli.py                        # Parser unificado de comandos de consola
    │   ├── algorithms/                   # Dijkstra desacoplado, A-Star (A*) y referencias
    │   ├── datastructures/               # IndexedMinHeap, DAryHeap (d=4) y FibonacciHeap
    │   ├── io/                           # Lectura y validación defensiva de grafos
    │   ├── generators/                   # Generadores sintéticos de redes viales
    │   ├── verification/                 # Certificados de optimalidad y comparador
    │   ├── models/                       # Definición de la red vial del Cusco
    │   ├── utils/                        # Modelo de costos, telemetría y exportadores
    │   └── visualization/                # Generación de figuras y código DOT Graphviz
    └── tests/                            # 221 pruebas automatizadas con Pytest (patrón AAA)
```

---

## 7. Compilación del Informe Académico en LaTeX

Para compilar el informe de 60 páginas desde el código fuente en LaTeX:

* **En PowerShell (Windows):**
  ```powershell
  cd documento
  .\compilar.ps1
  ```
* **En Símbolo del Sistema (CMD):**
  ```cmd
  cd documento
  compilar.bat
  ```
* **Con `pdflatex` directamente:**
  ```bash
  cd documento
  pdflatex -interaction=nonstopmode main.tex
  pdflatex -interaction=nonstopmode main.tex
  ```
> Produce el archivo [documento/main.pdf](documento/main.pdf) con numeración de páginas, bibliografía cruzada e índices de figuras y tablas.

---

## 8. Licencia y Créditos

Proyecto desarrollado con fines estrictamente académicos para la asignatura de **Algoritmos Avanzados (2026-II)** de la **Universidad Nacional de San Antonio Abad del Cusco (UNSAAC)**.

Docente: **Ing. Héctor Eduardo Ugarte Rojas**  
Grupo 5: **Choquenaira Q., Yaranga A., Porroa S., Quispe R.**
