# 📱 Aplicación Móvil Android — Rutas Cusco Pro (v1.2 Pro)

<p align="center">
  <img src="../mobile/assets/icon/app_icon.png" width="128" height="128" alt="Rutas Cusco Pro Logo" />
  <br>
  <b>Rutas Cusco Pro · Edición v1.2 Pro</b><br>
  <i>Herramienta móvil oficial para cálculo de rutas mínimas en redes viales del Cusco</i><br>
  <b>Universidad Nacional de San Antonio Abad del Cusco (UNSAAC) — Grupo 5</b>
</p>

---

## 📦 Archivos APK Disponibles para Instalación Directa

Esta carpeta contiene los instaladores oficiales en formato `.apk` listos para ser transferidos e instalados directamente en cualquier teléfono o tablet Android (sin necesidad de compilar ni tener Android Studio instalado):

| Archivo APK | Tamaño | Arquitectura | Recomendación de Uso |
| :--- | :---: | :---: | :--- |
| **[`rutas_cusco_pro_v1.2_arm64.apk`](rutas_cusco_pro_v1.2_arm64.apk)** | **22.87 MB** | `arm64-v8a` | **⭐ RECOMENDADO:** Para la gran mayoría de celulares Android modernos (Samsung, Xiaomi, Motorola, Huawei, Pixel, Honor, etc. de 64 bits). Descarga ultraligera. |
| **[`rutas_cusco_pro_v1.2_universal.apk`](rutas_cusco_pro_v1.2_universal.apk)** | **59.72 MB** | Universal (todas) | Compatible con cualquier teléfono, tablet o emulador Android (32 bits, 64 bits o x86). |

### Verificación de Integridad (SHA-256)
* **`rutas_cusco_pro_v1.2_arm64.apk`**:  
  `2BE22FDCFFAEBD18603BEDA84D8F7DA45912AD2FCF0854879FD1990C718BF457`
* **`rutas_cusco_pro_v1.2_universal.apk`**:  
  `6BD63F2D7CAE9F8A3350ECE269AD272B6975535990C762806D82DB839A257B04`

---

## 📲 Guía Paso a Paso para Instalar en tu Celular Android

### Paso 1: Descargar o transferir el APK al celular
* **Opción A (Desde la PC):** Conecta tu celular a la computadora mediante cable USB y copia el archivo `rutas_cusco_pro_v1.2_arm64.apk` en la carpeta **Descargas** (*Download*) de tu teléfono.
* **Opción B (Sin cables):** Envíate el archivo por WhatsApp, Telegram, Google Drive o correo electrónico y descárgalo directamente en el celular.
* **Opción C (Desde GitHub):** Abre este repositorio en el navegador de tu celular y pulsa sobre `rutas_cusco_pro_v1.2_arm64.apk` para descargarlo.

### Paso 2: Permitir la instalación
1. Abre la aplicación **Archivos** (*Mis Archivos* o *Gestor de archivos*) en tu celular y entra a la carpeta **Descargas**.
2. Toca el archivo `rutas_cusco_pro_v1.2_arm64.apk`.
3. Si Android te muestra el mensaje de seguridad de instalación externa, pulsa en **Configuración / Ajustes** y activa la opción **«Permitir desde esta fuente»** (o *«Instalar aplicaciones desconocidas»*).

### Paso 3: Instalar y abrir
1. Pulsa en **«Instalar»**.
2. En unos segundos verás el mensaje *«Se instaló la app»*.
3. Pulsa en **«Abrir»** o busca el icono andino granate y dorado con el nombre **Rutas Cusco Pro** en la pantalla de inicio de tu celular.

---

## 🚀 Capacidades de la Aplicación

* **Mapa Interactivo de Cusco:** Visualización cartográfica con OpenStreetMap y plano vectorial sin conexión, con barra de herramientas flotante (+, −, candado para bloquear toques accidentales, centrado de ruta, ajuste de red y pantalla completa).
* **Solvers en Paralelo:** Resuelve y contrasta simultáneamente **Dijkstra** (con 3 colas de prioridad: Binaria, 4-aria y Fibonacci) y **$A^*$ consistente**.
* **Almacenamiento Local SQLite:** Base de datos interna en el dispositivo (`rutas_cusco_local.db`) que conserva instancias, rutas y experimentos sin requerir servidor de base de datos externo.
* **Editor Táctil e Importación:** 16 ejemplos integrados, editor táctil de vértices/aristas, importador de archivos JSON, CSV o TXT y generador reproducible oficial con semillas.
* **Sección «Acerca de»:** Diagnóstico de conexión en vivo con el backend FastAPI de Render y lectura dinámica de versión instalada (`1.2.0 Pro`), con acreditación institucional del Grupo 5 (UNSAAC).

---

## 🏛️ Créditos y Filiación Académica

* **Institución:** Universidad Nacional de San Antonio Abad del Cusco (UNSAAC).
* **Carrera:** Ingeniería Informática y de Sistemas.
* **Asignatura:** Algoritmos Avanzados (Semestre 2026-II).
* **Desarrollo móvil e integración:** Noe Franklin Choquenaira Quispe.
* **Equipo del Proyecto (Grupo 5):** Noe Franklin Choquenaira Quispe, Yeni Ruth Porroa Sivana, Romario Quispe Rimachi, Aldo Yaranga Achahui.
