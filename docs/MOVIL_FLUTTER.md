# Aplicación móvil Flutter (`mobile/`)

Aplicación Android (y estructura compatible con iOS) para **Rutas mínimas en Cusco (UNSAAC)**. Consume el mismo backend FastAPI en Render (`https://rutas-cusco-unsaac.onrender.com`) y guarda el trabajo del usuario en la base de datos interna del dispositivo (SQLite), sin servidor de base de datos externo.

## 1. Requisitos y ejecución local

- Flutter `3.47.x` (Dart `3.13.x`), Android SDK y JDK 17+ (en iOS se requiere macOS con Xcode).
- Desde `mobile/`:

```powershell
flutter pub get
flutter analyze
flutter test
flutter build apk --debug
```

### Conexión al backend

- **Producción (por defecto):** `https://rutas-cusco-unsaac.onrender.com`. En el plan gratuito de Render puede tardar unos segundos al despertar; la app muestra aviso y mantiene utilizables ejemplos, editor y biblioteca local.
- **Emulador Android contra FastAPI local:** usa `http://10.0.2.2:8000` (en el teléfono, `localhost` apunta al propio teléfono, no a tu PC).
- **Teléfono físico por red local:** inicia FastAPI con `--host 0.0.0.0 --port 8000` y configura `http://IP_DE_TU_PC:8000` en **Ajustes → Conexión avanzada**. Teléfono y equipo deben estar en la misma red, con el puerto permitido por el cortafuegos. HTTP local no cifra las solicitudes; úsalo solo en una red de confianza.

FastAPI se ejecuta en Render o en un equipo de pruebas, no dentro del teléfono. La app envía la consulta y muestra el resultado; no hace falta que el usuario instale Python ni configure el servidor. Esta arquitectura mantiene los mismos algoritmos y costos que la web. Un cálculo completamente local necesitaría otra implementación validada de los solvers y los datos necesarios en el dispositivo; no está implementado.

La app comprueba la conexión al iniciar y al volver al primer plano si el servicio no estaba disponible. También permite reintentar manualmente. No comprueba continuamente internet ni garantiza reconexión instantánea. Las imágenes de calles se descargan directamente de OpenStreetMap, independientemente de FastAPI.

## 2. Almacenamiento interno del dispositivo (sin BD externa)

- **SQLite local (`rutas_cusco_local.db`, esquema v1):**
  - `saved_instances`: borradores, copias editables de ejemplos, archivos importados y redes generadas completas (incluye `generator`, `generator_version`, `seed` y todas las aristas).
  - `saved_routes`: resultados de rutas con su solicitud y respuesta completas para consulta sin conexión.
  - `saved_experiments`: experimentos de sesión separados del banco canónico.
- **`SharedPreferences`:** URL del servidor, caché de versión/catálogo, lectura meteorológica guardada voluntariamente y claves opcionales solo si se marca *Recordar*.

## 3. Uso sin conexión

- **Disponible offline:** explorar los 16 ejemplos incluidos, duplicar y editar grafos, validar formato localmente, consultar el banco canónico (1350 ejecuciones) y piloto (18 muestras) incluidos, consultar documentación académica y resultados guardados en SQLite.
- **Requiere conexión al backend:** cálculo oficial de rutas (`Dijkstra` / `A*`), validación definitiva, generación reproducible con semillas, experimentos nuevos y clima/tráfico en vivo.
- **Calles OSM:** necesitan internet para descargar teselas directamente del proveedor, no del backend. No se garantiza su disponibilidad sin conexión. El modo **Plano sin conexión** dibuja una vista previa ya cargada, sin teselas; no descarga por sí mismo una red ni calcula rutas nuevas.

## Interfaz y referencia

- **Ajustes:** estado y reintento de conexión, ayuda de uso sin internet y mapas, sección «Acerca de» (propósito académico, versión instalada vía `package_info_plus`, integrantes del Grupo 5 y desarrollador móvil según el informe de portada). La dirección, versiones de backend y límites quedan en **Conexión avanzada**, cerrada inicialmente.
- **Biblioteca → Referencia:** cobertura de los mapas, evidencias históricas (incluido el piloto de revisión de 120 tiempos), modelo de costos e informe. Se evita duplicar esta información en Ajustes.
- La bitácora y los filtros de commits se retiraron de la interfaz y del catálogo de documentos móviles. Los archivos históricos y la autoría Git del repositorio se conservan, sin alterar el informe académico.
- El aviso de conexión se comparte entre la navegación y Ajustes; no se muestra dos veces en esta pantalla. Cambiar de servidor invalida el catálogo anterior para no atribuirlo al nuevo destino.

### Revisión local de usabilidad (13/11/2026)

Alcance: Ajustes, estado compartido de conexión, catálogo de documentos y tarjetas de referencia/análisis. Se conserva la identidad de `DESIGN.md` (ENERGY 2 / RHYTHM 2 / MOTION 1), los solvers Python y los archivos académicos históricos.

- El estado de conexión tiene prioridad visual; las opciones de desarrollo permanecen cerradas para no exigir configuración al usuario habitual.
- Se mantienen tipografía y colores institucionales. El espaciado separa estado, almacenamiento y ayuda, sin añadir imágenes ni decoración nueva.
- En tarjetas compactas, los campos que ya figuran en título o etiqueta no se repiten. Las tablas anchas mantienen todas las columnas.

| Comprobación | Resultado y evidencia |
| --- | --- |
| Compilación y análisis | PASS: `flutter analyze` sin incidencias y `flutter build apk --debug` correcto. |
| Regresión móvil | PASS: `flutter test --reporter expanded`, 40 pruebas aprobadas (incluye 7 pruebas dedicadas en `about_app_section_test.dart` sobre lectura bajo demanda, timeouts, reintentos y vista de licencias). No se ejecutaron de nuevo las suites Python/web, cuyo código no se cambió en esta revisión. |
| Conexión y errores | PASS: `settings_connection_test.dart` comprueba URL inválida sin envío, guardado de servidor propio, restauración, preset del emulador, reintento tras desconexión, incompatibilidad de versión, invalidación del catálogo anterior y ausencia de solicitudes duplicadas. Las respuestas de estas pruebas son simuladas. |
| Diseño adaptable | PASS: pruebas de Ajustes a 320/390/1100 px, con escala de texto de 1,4 y 2 según el caso; pruebas de tarjetas sin datos repetidos y tabla completa en `responsive_data_view_test.dart`. |
| Navegación y documentos | PASS: `app_responsive_test.dart` abre Ajustes, Biblioteca/Referencia y llega al botón PDF con letra ampliada; `docs_and_equivalence_test.dart` confirma que la bitácora no pertenece al catálogo móvil. |
| Vista nativa | PASS: APK instalada sobre la anterior en `emulator-5554`, con revisión de Ajustes, apertura de ayuda de mapas y Biblioteca/Referencia. También se revisó Ajustes en un viewport de tableta del mismo emulador; tamaño y densidad se restauraron después. No equivale a probar hardware de tableta. |
| Contraste de los textos modificados | PASS: disponible 5,76:1, desconexión 5,81:1, error 6,79:1, texto principal sobre papel 15,39:1, secundario 6,85:1 y etiqueta granate 9,68:1 (cálculo de luminancia sRGB). |
| Detector y registro nativo | PASS: detector Impeccable sin hallazgos en las pantallas de ajustes/referencia y aviso compartido; sin coincidencias de `FATAL EXCEPTION`, `E/flutter`, excepciones no controladas o desbordes en los últimos 600 registros consultados del emulador durante la revisión. |

La revisión no acredita validación en teléfono físico, iOS, firma de distribución, funcionamiento íntegro sin internet ni una auditoría completa de accesibilidad de todas las pantallas. Los cambios permanecen locales, sin commit ni push.

## 4. Actualizaciones y mantenimiento

| Tipo de cambio | Mecanismo |
| --- | --- |
| Correcciones o mejoras compatibles en FastAPI | Despliegue automático en Render; las apps instaladas consumen la API actualizada sin reinstalar. |
| Interfaz Dart, mapa o migración SQLite | Nueva compilación APK/AAB e instalación sobre la versión previa conservando `rutas_cusco_local.db`. |
| Cambio incompatible de API | Incrementar versión mayor de `API_VERSION` y mantener compatibilidad temporal. |

### Publicación Android (APK firmado / AAB)

1. Incrementa `version: X.Y.Z+N` en `mobile/pubspec.yaml` manteniendo sincronizada la versión con `VERSION`.
2. Configura `signingConfigs.release` y `key.properties` fuera del repositorio (nunca subas `.jks` ni contraseñas a Git).
3. Ejecuta `flutter build appbundle --release` para Google Play o `flutter build apk --release` para distribución directa, verificando primero `flutter analyze` y `flutter test`.
4. **Reversión:** conserva el tag de Git de la compilación anterior; en Render puedes revertir al despliegue previo y en Android publicar un nuevo `versionCode` superior basado en la etiqueta estable.
