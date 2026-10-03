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

En esta primera etapa (Avances 1 a 3), se establece la arquitectura base del sistema, el modelo matemático de impedancia topográfica andina, la estructura de datos nuclear (`IndexedMinHeap` con diccionario de posiciones $O(1)$) y el algoritmo de Dijkstra con soporte de reconstrucción de rutas y verificación de invariantes formales.

---

## 2. Estructura del Repositorio (Núcleo del Sistema)

```text
.
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
|   |-- data/                   # Instancia vial serializada en JSON
|   \-- src/                    # Código fuente del sistema
|       |-- algorithms/         # Dijkstra parametrizado con inyección de colas
|       |-- datastructures/     # IndexedMinHeap con mapa posicional O(1)
|       |-- models/             # Red vial del Centro Histórico (6 nodos, 9 aristas)
|       \-- utils/              # Modelo de impedancia andina y penalizaciones
\-- README.md                   # Documentación general del proyecto
```

---

## 3. Instrucciones de Ejecución

### A. Prototipo en Python (Demostración Directa)

```bash
cd python
pip install -r requirements.txt
python main.py
```

**Salidas generadas:**
- Carga y serialización de la red vial en `data/processed/cusco_centro_network.json`.
- Cálculo de distancias mínimas en metros y tiempos estimados en segundos desde Plaza Mayor ($A$) hacia todos los destinos.
- Verificación de invariantes formales y correctitud del camino óptimo.

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
