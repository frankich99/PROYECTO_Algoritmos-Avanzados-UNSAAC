# Rutas Mínimas con Colas de Prioridad en Redes Viales Urbanas del Cusco

**Universidad Nacional de San Antonio Abad del Cusco (UNSAAC)**  
**Facultad de Ingeniería Eléctrica, Electrónica, Informática y Mecánica**  
**Escuela Profesional de Ingeniería Informática y de Sistemas**  
**Asignatura:** Algoritmos Avanzados (Semestre 2026-II)  
**Docente:** Ing. Héctor Eduardo Ugarte Rojas  
**Grupo 5:**
- Choquenaira Quispe, Noe Franklin (133962) - Líder y Arquitecto de Software
- Porroa Sivana, Yeni Ruth (120893)
- Quispe Rimachi, Romario (164257)
- Yaranga Achahui, Aldo (103179)

**Repositorio Oficial:** [https://github.com/frankich99/PROYECTO_Algoritmos-Avanzados-UNSAAC](https://github.com/frankich99/PROYECTO_Algoritmos-Avanzados-UNSAAC)

---

## 1. Descripción del Proyecto

El presente proyecto investiga, implementa y evalúa experimentalmente el desempeño del Algoritmo de Dijkstra para la determinación de rutas mínimas en vehículos de emergencia sobre la red vial urbana del Centro Histórico de la ciudad del Cusco.

En la primera unidad (Avances 1 a 3) se estableció la arquitectura base, el modelo de impedancia topográfica andina, la estructura nuclear (`IndexedMinHeap` con diccionario de posiciones $O(1)$) y el algoritmo de Dijkstra con reconstrucción de rutas.

**Avance 4.** Dijkstra con `IndexedMinHeap` integrado en el sistema: carga o generación de instancias, validación de entradas, salida verificable (certificado de optimalidad), referencia independiente (Bellman-Ford) y pruebas básicas, límite y adversas. Guía: [`docs/AVANCE_4.md`](docs/AVANCE_4.md).

**Avance 5.** Segunda alternativa: `DAryHeap` (d = 4) y `FibonacciHeap` con las mismas entradas y salidas, interfaz común para elegir y ejecutar algoritmos (`python main.py run/compare/...`), comparación de resultados con clasificación de diferencias y benchmark de escalabilidad. Guía: [`docs/AVANCE_5.md`](docs/AVANCE_5.md).

---

## 2. Estructura del Repositorio (Núcleo del Sistema)

```text
.
|-- docs/                       # Guías de sustentación de los Avances 4 y 5
|-- documento/                  # Informe técnico académico en formato LaTeX (APA 7ma edición)
|   |-- main.pdf                # Documento compilado base (22 páginas)
|   |-- main.tex                # Archivo maestro del informe
|   |-- compilar.bat            # Script de compilación automática para Windows CMD
|   |-- compilar.ps1            # Script de compilación automática para PowerShell
|   |-- capitulos/              # Capítulos del núcleo (02, 05, 06, 07)
|   |-- config/                 # Paquetes y estilos de listings
|   |-- tablas/                 # Tablas formales en formato booktabs
|   |-- figuras/                # Escudo oficial y diagramas
|   \-- referencias.bib         # Fuentes bibliográficas en formato BibLaTeX
|-- python/                     # Prototipo mínimo ejecutable modular
|   |-- main.py                 # Demostración del prototipo mínimo
|   |-- requirements.txt        # Dependencias de Python
|   |-- README.md               # Documentación interna del módulo Python
|   |-- data/                   # Instancias de demostración (válidas e inválidas)
|   |-- tests/                  # Suite pytest (básicos, límite, adversos, equivalencia, CLI)
|   \-- src/                    # Código fuente del sistema
|       |-- cli.py              # Interfaz común para seleccionar y ejecutar alternativas
|       |-- algorithms/         # Dijkstra con inyección de colas + referencias (Bellman-Ford)
|       |-- datastructures/     # IndexedMinHeap, DAryHeap (d=4), FibonacciHeap
|       |-- io/                 # Lectura y validación de instancias
|       |-- generators/         # Instancias sintéticas reproducibles
|       |-- verification/       # Certificado de optimalidad y comparación
|       |-- models/             # Red vial del Centro Histórico (6 nodos, 9 aristas)
|       \-- utils/              # Modelo de impedancia andina y penalizaciones
\-- README.md                   # Documentación general del proyecto
```

---

## 3. Instrucciones de Ejecución

### A. Sistema en Python

```bash
cd python
pip install -r requirements.txt
python main.py              # demostración completa
python main.py --help       # interfaz común: list, run, compare, generate, verify, benchmark, menu
python -m pytest            # 219 pruebas automatizadas
```

Ejemplos rápidos:

```bash
python main.py run --trace                                       # red del Cusco con Binary Heap
python main.py compare --metric distance                         # 3 colas + Bellman-Ford sobre la misma instancia
python main.py run --inline "A B 4; A C 1; C B 2" -s A -q all    # instancia propuesta en la sesión
```

Detalle de comandos, formatos e instancias en [`python/README.md`](python/README.md).

### B. Compilación del Informe en LaTeX

```powershell
cd documento
.\compilar.ps1
```
o en CMD:
```cmd
cd documento
compilar.bat
```
> Compila `documento/main.tex` con `pdflatex` y `biber`, produciendo el archivo `documento/main.pdf`.
