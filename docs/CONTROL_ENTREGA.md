# Control de requisitos y cierre del Grupo 5

**Revisión de la segunda entrega (06/11/2026):** consultar [SEGUNDA_ENTREGA.md](SEGUNDA_ENTREGA.md),
[BITACORA_GITHUB.md](BITACORA_GITHUB.md) y los resultados fechados en
`web/public/data/delivery_evidence.json`. El texto de abajo es histórico: sus conteos
y algunos hashes no representan necesariamente la rama vigente. La bitácora nueva
se genera del historial alcanzable real, sin reconstruir reuniones ni atribuir
commits grupales a personas.

Referencia: `Descripcion del proyecto.pdf`, apartados 5, 6, 8, 9 y 12.
Estado revisado al **05/11/2026**. La fecha objetivo comunicada por el equipo
fue el **04/11/2026**; ninguna de las dos es una fecha oficial ni constancia de
recepción. Las fechas históricas citadas abajo proceden de commits o registros
guardados.

## Alcance comprobable

- **Apartado 5:** Dijkstra con tres colas implementadas, oráculos, instancias
  sintéticas y OSM. La red de seis nodos es ilustrativa; la consulta OSM no
  contiene pendiente ni congestión por arista. Ver `DATOS_Y_MODELO.md`.
- **Apartado 6:** formulación, comparación, corrección y experimentación están
  documentadas. El proceso individual y la defensa requieren evidencias de
  cada integrante; un resultado grupal no acredita ambas actividades.
- **Apartado 8:** Entrega 1 exige plan de aprendizaje y prototipo temprano;
  Entrega 2 exige integración, pruebas, complejidad y bitácora actualizada;
  Entrega 3 exige sistema, repositorio, datos, informe, manuales, presentación,
  demostración y defensa individual. Los archivos de los avances se retiraron
  del árbol actual; el historial Git conserva versiones. La presentación y
  defensas no están verificadas en este repositorio.
- **Apartado 9:** `latex/main.tex` contiene las secciones requeridas. Las
  tablas y figuras de resultados usan JSON guardados; la captura OSM es solo
  referencia visual. El piloto figura en el informe y su JSON es del 04/11.
  La presencia de una sección no demuestra el trabajo individual del apartado 12.

## Apartado 12: evidencia frente a requisito

`Presente` = archivo o commit identificado; `Parcial` = hay relato, pero falta
constancia específica; `Pendiente` = no hay evidencia en este repositorio.
No transformar registros retrospectivos en actas antiguas.

| Indicador | Elemento exigido | Estado y evidencia / pendiente |
| --- | --- | --- |
| AG-C06.01 | Plan grupal e individual | **Pendiente**: el capítulo 3 reconstruye áreas de aprendizaje, pero no equivale a un plan presentado en la Entrega 1; planes originales no localizados. |
| AG-C06.01 | Brechas de conocimiento | **Presente** a nivel grupal en capítulo 3; cada persona debe confirmar las suyas. |
| AG-C06.01 | Bitácora de fuentes, actividades y aprendizajes | **Parcial**: anexo C contiene commits fechados, no registros originales de fuentes y aprendizaje de cada integrante. |
| AG-C06.01 | Compromisos de seguimiento cumplidos | **Pendiente**: anexo F declara ausencia de actas con meta, responsable, fecha prometida y verificación. |
| AG-C06.01 | Resolución autónoma de dificultades | **Parcial**: narrada en capítulos 3 y 4; vincular incidencias y pruebas/commits concretos. |
| AG-C06.01 | Contribuciones verificables | **Presente** para autoría de commits: anexo E cita hashes; falta confirmar la defensa individual. |
| AG-C06.02 | Herramientas candidatas, matriz, criterios, stack | **Presente** en capítulo 4; ajustar afirmaciones que exceden la implementación. |
| AG-C06.02 | Reflexión individual sobre aprendizajes y necesidades futuras | **Pendiente**: una por estudiante, escrita y validada por su autor. |
| AG-C06.02 | Prototipo de adopción temprana | **Parcial**: commits del 02–04/10 muestran código inicial; confirmar correspondencia con Entrega 1. |
| AG-C06.02 | Instalación, configuración e integración | **Parcial**: instrucciones y módulos presentes; probar instalación limpia y no afirmar versiones fijadas con `>=`. |
| AG-C06.02 | Pruebas de herramienta seleccionada | **Parcial**: pruebas OSM, Open-Meteo y aplicación sin red; no hay prueba de consulta TomTom en vivo. |
| AG-C06.02 | Dificultades y soluciones, manual reproducible | **Parcial**: capítulo 4 y anexo A/B; enlazar evidencia fechada y confirmar comandos en copia limpia. |
| AG-C06.03 | Fuentes razonadas y comparación | **Presente** en capítulos 3, 4 y referencias. |
| AG-C06.03 | Supuestos, métricas y experimento reproducible | **Presente** para benchmark y clima en capítulos 5 y 9 y JSON; **no** para tráfico canónico. |
| AG-C06.03 | Tablas, gráficos, teoría, límites y conclusiones | **Presente** para la comparativa principal; la caché y las asignaciones son explicaciones posibles, no mediciones del proyecto. |
| Transversal | Presentación, demostración, defensa individual | **Pendiente de acreditación**: preparar y realizar con cada integrante; solo el docente puede evaluar la defensa. |

El peso de AG-C06.01, AG-C06.02 y AG-C06.03 es 40 %, 40 % y 20 %. No se
calcula una calificación sin evaluación individual.

## Cronología verificable y responsables

El historial acredita **autoría del commit**, no permite inferir horas de
trabajo ni verificar retrospectivamente una reunión. El anexo C contiene
únicamente fechas y cambios de Git. Las sesiones citadas en borradores
anteriores no tenían actas comprobables y no se presentan como hechos. En
particular, el snapshot OSM está fechado el **28/10**, no el 05/10.

Los archivos locales `ficha_aprendizaje_grupo5.tex` y
`guia_ficha_aprendizaje.tex` están ignorados por Git y contienen indicaciones
para completar registros. No acreditan planes ni bitácoras firmadas.

| Rama / Integrante | Commit fechado y alcance registrado en Git |
| --- | --- |
| `ramaFRANKI`<br>Noe Franklin Choquenaira Quispe (Líder) | Núcleo, Dijkstra y heap binario (`592589a`); A* consistente e informe general (`b307be4`, `f0799bf`); API FastAPI y cliente React v1.5.0. |
| `ramaAldo`<br>Aldo Yaranga Achahui | Suite de pruebas automatizadas QA (`d50e67b`); opciones de CLI y exportador Graphviz (`65d303d`). |
| `ramaYeni`<br>Yeni Ruth Porroa Sivana | Montículo 4-ario indexado (`77983b7`); análisis de localidad de caché y comparativa de montículos (`3b91a5e`). |
| `RamaRomario`<br>Romario Quispe Rimachi | Fibonacci heap y modelo de impedancia vial (`72df976`); benchmark de escalabilidad y datos de percentiles (`e3af921`). |

Los cambios grupales posteriores tienen esta cronología verificable:

| Fecha | Archivo o commit | Alcance comprobable |
| --- | --- | --- |
| 28/10 | `7922f52` y `benchmark_results.json` | Integración OSM, clima, aplicación y banco de 1,350 muestras. |
| 30/10–01/11 | Secciones históricas de verificación abajo | Pruebas y revisión descritas en los registros; no son actas individuales. |
| 03/11 | `4025f8f` | Índice e informe revisados; PDF incluido en el commit. |
| 04/11 | `ced0b82`, `c119aa6` y `pilot_benchmark_results.json` | Referencia OSM, piloto de 18 muestras y figura; el piloto es posterior al banco canónico. |

No se reconstruyen reuniones ni compromisos cumplidos a partir de estas fechas.

## Criterios de cierre

1. `python -m pytest python/tests -q` termina sin fallos; guardar fecha, Python
   usado y conteo real. Los casos adversos deben rechazar ciclos de peso cero
   desconectados y caminos reportados incompletos.
2. `latex/`, `colab/`, datos y el PDF figuran en el árbol seguido por Git.
   El PDF de
   requisitos (`Descripcion del proyecto.pdf`) está ignorado en Git: confirmar
   si el docente exige adjuntarlo por un canal separado.
3. `python/scripts/reproduce_canonical.py --skip-benchmark --skip-applied`
   regenera tablas y figuras sin alterar las mediciones; `latex/compilar.ps1`
   produce PDF actualizado. El benchmark completo puede variar en tiempo.
4. Informe, README, guía y JSON coinciden en cifras, supuestos y unidades;
   ausencia de datos meteorológicos se muestra como tal, no como medición.
5. Adjuntar evidencias individuales auténticas y presentar la defensa.
   Hasta entonces no afirmar «cumplimiento total de AG-C06».

## Verificación técnica del 30/10/2026

Esta verificación automatizada no acredita participación individual en las
metas del calendario. Con el entorno Python disponible:

- Suite desde la raíz: **255 passed in 19.68s**. En una copia independiente
  del paquete de entrega: **255 passed in 21.71s**.
- La copia regeneró tablas y tres figuras usando `--skip-benchmark` y
  `--skip-applied`; los SHA-256 de ambos JSON, las tres tablas y las tres
  figuras comparados con el original coincidieron.
- `latex/compilar.ps1` produjo `latex/main.pdf` de **53 páginas A4**. No
  quedaron referencias ni marcadores PDF indefinidos, ni cajas desbordadas;
  persiste solo una sustitución de tamaño de fuente de hasta 0.5 pt.
- Los enlaces locales de los README, GUIA y documentos de control existen en
  el paquete. `git diff --check` no encontró defectos de espacio; solo
  avisos de normalización LF/CRLF de Git.

La copia independiente reutilizó el entorno Python ya instalado. **No** se
ha comprobado instalación de dependencias en una máquina sin ellas. La nota
sobre archivos sin seguimiento Git corresponde a ese momento y no al estado
actual.

## Actualización de la web e informe (31/10–01/11/2026)

La aplicación presenta Ruta y Comparación como áreas principales. La consulta
OSM compara las tres colas sobre el mismo par; la pestaña experimental filtra
mediciones y acepta un benchmark JSON temporal. Procedencia, consultas API y
traza didáctica quedan en segundo plano. Se corrigieron los títulos del
apartado 9 y se separó la observación Open-Meteo del experimento canónico de
un snapshot OpenWeatherMap posterior. La presión de suelo en este último se
rectificó desde `main.grnd_level` de la respuesta original, no desde
`main.pressure` (nivel del mar). En esa revisión pasaron **274 pruebas**;
el conteo aumentó después. Estas verificaciones técnicas no prueban
aprendizaje, seguimiento ni defensa individual de ningún integrante.
En navegador se comprobaron el cálculo nominal y el escenario uniforme,
el filtrado con estado vacío, las importaciones JSON válida e inválida,
ambas descargas CSV y los avisos sin clave. A 373 px de ancho no hubo
desbordamiento horizontal; los controles ajustados tuvieron áreas de 44 px
y no se registraron errores en la consola.
La web exige ahora una clave introducida explícitamente para OpenWeatherMap;
no reutiliza de forma implícita credenciales del entorno ni de archivos
locales. **Pendiente del propietario:** revocar y rotar la clave que apareció
en una captura; no utilizarla en la CLI hasta sustituirla.

## Ampliación de la interfaz (01/11/2026)

Se recuperó la navegación directa a cinco secciones. Ruta y Comparación
siguen primero; Clima y tráfico, Traza manual, y Datos y método ya no están
escondidos en un desplegable. El plano vial usa solo coordenadas guardadas,
con teselas externas opcionales. La consulta muestra la observación histórica,
el snapshot posterior o una lectura temporal como opciones distintas. La
traza permite examinar distancias y predecesores por paso; la comparación
añade la relación entre medianas sin afirmar significación estadística.
El botón de despliegue de Streamlit se oculta mediante configuración de
cliente y estilo de la aplicación. En esa fecha, la suite tenía **278 pruebas
aprobadas**; el PDF sigue exigiendo evidencias individuales que la interfaz no
genera.

## Comprobación del 04/11/2026

- El piloto de 18 tiempos se guardó el 04/11; el banco de 1,350 tiempos es
  del 28/10. El primero comprueba el procedimiento, no precede al segundo.
- Desde la raíz, con `.venv/Scripts/python.exe -B -m pytest python/tests -q
  -p no:cacheprovider`: **278 pruebas aprobadas en 34.95 s**. Este tiempo es
  la duración de la suite en el entorno de revisión, no un tiempo de ruta
  ni un resultado del benchmark.
- `c119aa6` incluye el JSON, la figura y el PDF del piloto. La fecha del
  commit no acredita horas de dedicación ni una presentación.
- `latex/compilar.ps1` generó `latex/main.pdf` de **62 páginas**. Se revisaron
  visualmente las páginas finales; el log no registra referencias indefinidas
  ni cajas desbordadas. El ciclo CLI generar--ejecutar--verificar--comparar
  funcionó con archivos de prueba fuera del repositorio.
- Sigue sin comprobarse la instalación limpia y sin constancia de bitácoras
  individuales, actas, recepción de la segunda entrega o defensa. Confirmar
  además la revocación de la clave expuesta indicada arriba.

## Actualización del 05/11/2026

- **Interfaz única.** Se retiraron `python/app.py`, `python/tests/test_streamlit_app.py`
  y `python/.streamlit/`. También se quitaron `streamlit` y `plotly` de
  `python/requirements.txt`. La interfaz vigente es React/TypeScript en `web/`
  con API FastAPI en `python/web_api.py`; no queda una segunda web que mantener.
- **Suite.** Al retirar las 11 pruebas de Streamlit, la suite pasa de 298 a
  **287 casos**. Con las pruebas de persistencia, clima, claves seguras de
  proveedor y tráfico puntual añadidas en la versión 1.2.1 (06/11/2026),
  la suite vigente es de **296 casos**. Las pruebas cubren catálogo,
  validación de coberturas, credenciales seguras, geometría OSM, instancias
  personalizadas, escenarios uniformes y separación entre banco canónico
  y experimentos de sesión.
- **Cobertura ampliada.** Se publicó `python/data/processed/cusco_urbano_drive.json`
  como snapshot **independiente**: consulta radial de 3000 m alrededor de
  `(-13.5165, -71.9788)`, recortada por distancia de red, base OSM del
  10/08/2026, 1938 nodos y 4753 aristas colapsadas (4798 registros). El 47,0 %
  de las aristas conserva geometría vial; la mayor componente fuertemente
  conexa cubre el 99,9 % y la débil el 100 %. La distancia máxima al centro es
  2735 m. Cuatro rutas de muestra resultaron finitas.
- **Revisión en dos pasos.** `python/scripts/build_urban_snapshot.py --xml`
  escribe un `*.pending.json`, comprueba límites, distancia, conectividad y
  rutas, y solo con `--publish --reviewed` escribe `coverage_reviewed: true`.
  La API mantiene la cobertura oculta si el campo falta, el archivo es inválido
  o se superan 5000 nodos o 30000 aristas.
- **Verificación en vivo.** La API en `127.0.0.1:8000` anunció la cobertura
  ampliada, validó 1938 nodos y 4753 aristas, y resolvió una ruta por ID y por
  coordenadas con costo de 348,22 s y cuatro comparaciones de cola. El mismo
  par se rechazó correctamente cuando el punto estaba a 443 m de un nodo vial.
- **Alcance.** El snapshot ampliado **no es todo Cusco** ni una cobertura
  administrativa completa; su etiqueta visible es «Centro ampliado, snapshot
  OSM (radio 3 km)». La web y la documentación declaran ese límite. Ampliar más
  la cobertura exige una extracción y una revisión nuevas.
- **Pendiente.** Repetir la suite y el build en un entorno limpio, revisar el
  PDF recompilado y confirmar la rotación de la clave expuesta. Las evidencias
  individuales de aprendizaje y defensa siguen fuera del alcance del código.
