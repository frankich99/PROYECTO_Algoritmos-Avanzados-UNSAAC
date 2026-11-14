# Rutas Mínimas con Colas de Prioridad en Redes Viales Urbanas del Cusco

[![Python 3.12](https://img.shields.io/badge/Python-3.12%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI v1.5.0](https://img.shields.io/badge/FastAPI-v1.5.0-009688.svg?logo=fastapi&logoColor=white)](https://rutas-cusco-unsaac.onrender.com/docs)
[![React 19](https://img.shields.io/badge/React-19%20%7C%20TypeScript-61DAFB.svg?logo=react&logoColor=black)](https://frankich99.github.io/PROYECTO_Algoritmos-Avanzados-UNSAAC/)
[![Flutter 3.47](https://img.shields.io/badge/Flutter-3.47%20%7C%20Dart-02569B.svg?logo=flutter&logoColor=white)](docs/MOVIL_FLUTTER.md)
[![Android APK](https://img.shields.io/badge/Android%20APK-v1.2%20Pro-3DDC84.svg?logo=android&logoColor=white)](#-aplicación-móvil-android--rutas-cusco-pro-v12-pro)
[![Tests Multiplataforma](https://img.shields.io/badge/Tests-433%20passed%20(349%20Py%20%7C%2044%20Web%20%7C%2040%20Móvil)-brightgreen.svg)](python/tests/)
[![Informe Académico](https://img.shields.io/badge/Informe-LaTeX%20(2.93%20MB)-orange.svg?logo=latex&logoColor=white)](latex/main.pdf)
[![Red OSM Cusco](https://img.shields.io/badge/OSM%20Cusco-891%20nodos%20%7C%202139%20aristas-informational.svg)](python/data/processed/cusco_osm_drive.json)

**Universidad Nacional de San Antonio Abad del Cusco (UNSAAC)**  
**Facultad de Ingeniería Eléctrica, Electrónica, Informática y Mecánica**  
**Escuela Profesional de Ingeniería Informática y de Sistemas**  
**Asignatura:** Algoritmos Avanzados (Semestre 2026-II)  
**Docente Revisor:** Ing. Héctor Eduardo Ugarte Rojas  
**Equipo de Trabajo:** Grupo 5  

---

## Enlaces del Ecosistema en Producción

* **🌐 Aplicación Web Oficial (GitHub Pages):** [frankich99.github.io/PROYECTO_Algoritmos-Avanzados-UNSAAC](https://frankich99.github.io/PROYECTO_Algoritmos-Avanzados-UNSAAC/)
* **🚀 Backend API REST Oficial (Render):** [rutas-cusco-unsaac.onrender.com](https://rutas-cusco-unsaac.onrender.com)
* **📖 Documentación Interactiva OpenAPI (Swagger):** [rutas-cusco-unsaac.onrender.com/docs](https://rutas-cusco-unsaac.onrender.com/docs)
* **📱 Aplicación Móvil Android (Rutas Cusco Pro):** [Guía y Descarga del APK](#-aplicación-móvil-android--rutas-cusco-pro-v12-pro)
* **📄 Informe Académico Final en PDF:** [latex/main.pdf](latex/main.pdf) (Compilado, 2.93 MB, 14 secciones y anexos completos)
* **📓 Cuaderno Didáctico Google Colab:** [colab/rutas_minimas_cusco.ipynb](colab/rutas_minimas_cusco.ipynb)

---

## Estructura del Grupo 5 y Ramas de Trabajo

El proyecto se organizó en cuatro frentes técnicos coordinados bajo control de versiones Git, con autoría verificable por commit:

| Rama Git | Integrante | Código | Responsabilidades y Aportes Verificables |
| :--- | :--- | :---: | :--- |
| **`ramaFRANKI`**<br>(Líder / Fullstack) | **Noe Franklin Choquenaira Quispe** | **133962** | **Arquitectura Global:** API REST FastAPI (`v1.5.0`) en Render, aplicación web React 19 + TypeScript con MapLibre GL JS, y aplicación móvil nativa Flutter/Dart (**Rutas Cusco Pro v1.2 Pro**) con base SQLite interna.<br>**Solvers Algorítmicos:** Dijkstra y $A^*$ consistente con heurística euclidiana admisible ($D / v_{\max}$), Montículo Binario Indexado.<br>**Geoprocesamiento:** Extracción y saneamiento de redes OSM de Cusco (Centro 891 nodos, Urbano 1938 nodos), algoritmo de snapping Haversine.<br>**Condiciones en Vivo:** Clima (Open-Meteo / OpenWeatherMap), congestión vehicular TomTom y geolocalización GPS.<br>**Redacción Transversal:** Informe de investigación en LaTeX de 60+ páginas y manuales de integración. |
| **`ramaAldo`**<br>(Pruebas & CLI) | **Aldo Yaranga Achahui** | **103179** | **Aseguramiento de Calidad:** Suite de pruebas unitarias y de integración bajo patrón AAA (Arrange-Act-Assert) para validación algorítmica.<br>**CLI y Herramientas:** Módulo interactivo de consola por línea de comandos (`src/cli.py`), exportador de grafos Graphviz (`.dot`), certificado de optimalidad $O(\|V\|+\|E\|)$ y validación en Google Colab. |
| **`ramaYeni`**<br>(Montículo 4-ario) | **Yeni Ruth Porroa Sivana** | **120893** | **Estructuras Avanzadas:** Montículo 4-ario indexado (*D-ary Heap* con $d=4$), algoritmo de flotado y hundimiento cuadrario (`d_ary_heap.py`).<br>**Análisis de Hardware:** Evaluación de localidad espacial y temporal de memoria, reducción de saltos de caché (*cache misses*) en jerarquías L1/L2/L3 y matriz formal de selección de colas. |
| **`RamaRomario`**<br>(Fibonacci & Benchmark) | **Romario Quispe Rimachi** | **164257** | **Estructuras Teóricas:** Montículo de Fibonacci indexado con inserción y disminución de clave en $O(1)$ amortizado (`fibonacci_heap.py`).<br>**Modelado e Impedancia:** Calibración de la función de costo vial e impedancia urbana.<br>**Benchmarking:** Módulo de experimentación sistemática sintética y recolección estadística de percentiles (medianas, Q1, Q3, IQR). |

---

## 📱 Aplicación Móvil Android — Rutas Cusco Pro (v1.2 Pro)

<p align="center">
  <img src="mobile/assets/icon/app_icon.png" width="128" height="128" alt="Rutas Cusco Pro Logo" />
  <br>
  <b>Rutas Cusco Pro · v1.2 Pro</b><br>
  <i>Cliente móvil oficial para Android con almacenamiento SQLite interno y sincronización FastAPI</i>
</p>

La aplicación móvil en **Flutter 3.47 / Dart 3.13** (`mobile/`) traslada todo el ecosistema algorítmico a dispositivos móviles bajo una interfaz táctil adaptativa, diseñada conforme a la identidad institucional de la UNSAAC (granate `#681C32`, dorado `#8A6418` y papel `#F7F3EA`).

### Características Principales

1. **Rutas y Mapa Interactivo:** Selección de origen y destino por identificador de vértice, coordenadas GPS en vivo o toque directo sobre el mapa. Visualizador cartográfico con OpenStreetMap (`flutter_map`) y plano vectorial abstracto sin conexión, controles flotantes táctiles (modo origen/destino, bloqueo contra toques involuntarios, centrado de ruta, ajuste de red y pantalla completa).
2. **Contraste Algorítmico Simultáneo:** Resuelve la ruta óptima mediante la API y presenta de inmediato la comparación entre las 4 variantes: **Dijkstra Binario**, **Dijkstra 4-ario**, **Dijkstra Fibonacci** y **$A^*$ con heurística euclidiana consistente**, separando el tiempo de ejecución del solver en servidor ($\mu$s/ms) de la latencia total de red del dispositivo.
3. **Persistencia Interna SQLite (Sin Base de Datos Externa):** Base de datos SQLite local (`rutas_cusco_local.db`) en el dispositivo mediante `sqflite`. Permite guardar borradores de instancias, consultas de rutas y experimentos para inspeccionarlos sin conexión a Internet.
4. **Editor Táctil e Importación Políglota:** Catálogo de 16 instancias incluidas, editor táctil de vértices/aristas con validación sintáctica local preliminar, duplicación editable, importador de archivos JSON, CSV o TXT, y generador reproducible oficial con semillas.
5. **Análisis Experimental:** Visualización gráfica de las 1\,350 corridas del banco canónico con bandas de dispersión IQR, piloto histórico de 18 muestras y ejecutor de nuevos experimentos.
6. **Biblioteca y Referencia Académica:** Tablas formales de complejidad asintótica, modelo de impedancia vial y visualizador/compartidor del informe final en PDF.
7. **Sección «Acerca de» y Diagnóstico:** Monitor de salud y latencia del backend, guía de operación offline y sección institucional con lectura dinámica de la versión instalada (`1.2.0 Pro`), filiación institucional y créditos oficiales del Grupo 5.

---

### 📦 Dónde está el APK y Cómo Instalarlo en tu Celular

Los paquetes APK compilados se encuentran generados en la carpeta del repositorio:
`mobile/build/app/outputs/flutter-apk/`

| Archivo APK | Tamaño | Destino Recomendado |
| :--- | :---: | :--- |
| **`app-arm64-v8a-debug.apk`** | **100.8 MB** | **⭐ Recomendado para celulares Android modernos** (Samsung, Xiaomi, Motorola, Pixel, etc. con procesador de 64 bits). |
| **`app-debug.apk`** | **174.2 MB** | **Universal** (compatible con cualquier celular, tablet o emulador Android de 32 o 64 bits). |
| **`app-x86_64-debug.apk`** | **87.5 MB** | Para emuladores de PC (Android Studio, BlueStacks, etc.). |
| **`app-armeabi-v7a-debug.apk`** | **80.8 MB** | Para dispositivos Android antiguos (32 bits). |

#### Ruta Absoluta en este Repositorio
```text
F:\unsaac\alg-avanzados\proyecto\mobile\build\app\outputs\flutter-apk\app-arm64-v8a-debug.apk
F:\unsaac\alg-avanzados\proyecto\mobile\build\app\outputs\flutter-apk\app-debug.apk
```

#### Paso a Paso para Instalar el APK en tu Celular Android:
1. **Copiar el APK a tu celular:**
   * Conecta tu celular a la PC mediante cable USB y copia el archivo `app-arm64-v8a-debug.apk` a la carpeta *Descargas* (*Downloads*) de tu teléfono.
   * *O bien:* Envíate el archivo por WhatsApp, Telegram, Google Drive o correo electrónico y descárgalo en el celular.
2. **Habilitar instalación de aplicaciones desconocidas:**
   * Abre el archivo `.apk` descargado desde el explorador de archivos de tu celular.
   * Si el sistema muestra el aviso de seguridad de Android, pulsa en **Configuración / Ajustes** y activa la opción **«Permitir desde esta fuente»** o **«Instalar aplicaciones desconocidas»**.
3. **Completar la instalación:**
   * Pulsa en **«Instalar»**.
   * Una vez finalizado, pulsa en **«Abrir»** o busca el nuevo icono andino granate y dorado con el nombre **Rutas Cusco Pro** en tu pantalla de inicio.

---

## 🏛️ Formulación Matemática y Modelo de Costo Vial

El sistema modela la red vial urbana del Cusco como un dígrafo $G=(V, E)$ con costos de viaje deterministas no negativos:

$$
w(u, v) = \frac{L(u, v)}{v_{\text{nom}}(u, v)} \cdot \left( 1 + 2.5 \cdot \max(0, \theta(u, v)) \right) \cdot \Omega_{\text{clima}} \cdot \Omega_{\text{tráfico}}
$$

* $L(u, v)$: Longitud del segmento vial en metros (obtenida mediante geodésica de Haversine).
* $v_{\text{nom}}(u, v)$: Velocidad nominal según la jerarquía vial urbana (Avenidas: 35 km/h, Calles centro: 15 km/h, Peatonales: 8 km/h).
* $\theta(u, v)$: Pendiente topográfica en porcentaje; las pendientes positivas penalizan fuertemente el tiempo por la orografía andina.
* $\Omega_{\text{clima}} \ge 1.0$: Factor de fricción por lluvia, visibilidad reducida o ráfagas de viento.
* $\Omega_{\text{tráfico}} \ge 1.0$: Coeficiente horario de saturación vehicular urbana.

---

## 📊 Síntesis de Resultados del Benchmark Canónico

El banco canónico contiene **1\,350 muestras cronometradas** (10 escalas de tamaño $\times$ 3 instancias independientes $\times$ 15 repeticiones por cola) y la consulta sobre el recorte vial OpenStreetMap de Cusco (891 nodos, 2\,139 aristas):

| Cola de Prioridad | Complejidad Teórica | Mediana Disperso ($E=4V$) | Mediana Denso ($8\%$) | Mediana Caso OSM Cusco (891 nodos) |
| :--- | :---: | :---: | :---: | :---: |
| **Binary Heap Indexado** | $O((V+E)\log V)$ | Gana 2 de 5 escalas | Gana 1 de 5 escalas | **15.65 ms (Menor tiempo)** |
| **4-ary Heap Indexado ($d=4$)** | $O((V+E)\log_4 V)$ | **Gana 3 de 5 escalas** (Razón 0.964) | **Gana 4 de 5 escalas** (Razón 0.954) | 19.87 ms (+26.9 %) |
| **Fibonacci Heap** | $O(E + V\log V)$ amort. | 1.12--1.59$\times$ más lento | 1.05--1.44$\times$ más lento | 26.09 ms (+66.7 %) |

* **Extensión $A^*$:** En la red vial de Cusco, con la heurística euclidiana escalada consistente, $A^*$ redujo las expansiones de 887 a 823 vértices (7.2 % de poda) obteniendo el mismo costo óptimo (387.197 s).
* **Certificado de Optimalidad:** Toda solución generada se valida en $O(\|V\|+\|E\|)$ contra las condiciones de holgura complementaria de Bellman.

---

## 🧪 Batería de Pruebas Automatizadas (433 Pasadas)

El proyecto cuenta con **433 pruebas automatizadas** que garantizan la integridad matemática y la compatibilidad multiplataforma:

```text
Suite Automatizada Total: 433 pruebas aprobadas (100 %)
├── Python (pytest, python/tests/)    ── 349 pruebas (Contratos de colas, Dijkstra, A*, certificado, OSM, API)
├── Web (Vitest, web/tests/)          ──  44 pruebas (Componentes React, validaciones, fallback estático)
└── Móvil (Flutter, mobile/test/)      ──  40 pruebas (Contrato API, SQLite local, 16 ejemplos, responsive, Acerca de)
```

Para ejecutar las suites en cada entorno:

```powershell
# 1. Pruebas del núcleo Python (349 pruebas)
.\.venv\Scripts\python.exe -m pytest python/tests -q

# 2. Pruebas de la interfaz Web (44 pruebas)
cd web; npm test -- --run; cd ..

# 3. Pruebas de la aplicación Móvil (40 pruebas)
cd mobile; flutter test; cd ..
```

---

## 🛠️ Guía Rápida de Instalación y Ejecución

### 1. Entorno Python y Backend FastAPI
```powershell
# Crear y activar entorno virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r python/requirements.txt

# Iniciar servidor backend FastAPI en puerto 8000
python -m uvicorn web_api:app --app-dir python --host 127.0.0.1 --port 8000 --reload
```

### 2. Cliente Web React + TypeScript
```powershell
cd web
npm install
npm run dev
# Abrir en navegador: http://127.0.0.1:5173/
```

### 3. Cliente Móvil Flutter (Rutas Cusco Pro)
```powershell
cd mobile
flutter pub get
flutter analyze
flutter test
flutter run
```

### 4. Compilación del Informe Académico LaTeX
```powershell
cd latex
.\compilar.ps1
# Produce: latex/main.pdf (2.93 MB)
```

---

## 📂 Estructura del Repositorio

```text
.
├── README.md                      # Documentación maestra del proyecto
├── CHANGELOG.md                   # Registro histórico de versiones (v1.5.0)
├── VERSION                        # Versión canónica del sistema (1.5.0)
├── colab/                         # Cuaderno didáctico interactivo para Google Colab
│   └── rutas_minimas_cusco.ipynb
├── docs/                          # Documentación técnica, contratos y evidencias
│   ├── CONTRATO_MOVIL_API.md      # Especificación formal del contrato API v1.5.0
│   ├── MOVIL_FLUTTER.md           # Guía de arquitectura y mantenimiento móvil
│   ├── DATOS_Y_MODELO.md          # Procedencia de datos y formulación matemática
│   └── DESPLIEGUE.md              # Configuración de Docker, Render y GitHub Pages
├── latex/                         # Código fuente del informe académico formal
│   ├── main.tex                   # Documento principal (14 secciones y anexos)
│   ├── main.pdf                   # Informe final compilado (2.93 MB)
│   ├── capitulos/                 # Capítulos modulares del informe
│   ├── figuras/                   # Diagramas TikZ y capturas de pantallas del sistema
│   └── compilar.ps1               # Script PowerShell de compilación automatizada
├── mobile/                        # Aplicación móvil Flutter (Rutas Cusco Pro v1.2 Pro)
│   ├── android/                   # Configuración nativa Android y manifiestos
│   ├── assets/                    # Datos canónicos, documentos y PDF offline
│   ├── lib/                       # Código fuente Dart (arquitectura por capas MVVM)
│   │   ├── app/                   # Enrutamiento go_router y shell adaptativo
│   │   ├── core/                  # Cliente HTTP, base de datos SQLite y temas
│   │   ├── data/                  # Repositorios y modelos tipados
│   │   └── features/              # Módulos: Rutas, Instancias, Análisis, Biblioteca, Ajustes
│   └── test/                      # 40 pruebas automatizadas unitarias y de widgets
├── python/                        # Núcleo algorítmico y API backend
│   ├── web_api.py                 # API REST FastAPI v1.5.0 con OpenAPI 3.1
│   ├── main.py                    # Interfaz CLI de demostración y comandos
│   ├── src/                       # Algoritmos, colas, servicios y verificación
│   ├── tests/                     # 349 pruebas unitarias y de integración (pytest)
│   └── data/                      # Instancias viales de Cusco y resultados de benchmarks
└── web/                           # Aplicación web oficial en React 19 + TypeScript
    ├── src/                       # Vistas interactivas, componentes y mapas MapLibre
    └── tests/                     # 44 pruebas automatizadas con Vitest
```

---

## 📜 Licencia y Acreditación

Este proyecto fue desarrollado con fines de investigación formativa académica en la **Universidad Nacional de San Antonio Abad del Cusco (UNSAAC)**, semestre 2026-II. Distribuido bajo licencia MIT. Ver archivo [LICENSE](LICENSE) para más detalles.
