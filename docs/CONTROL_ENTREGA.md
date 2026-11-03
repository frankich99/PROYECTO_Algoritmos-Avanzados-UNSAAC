# Control de requisitos y cierre del Grupo 5

Referencia: `Descripcion del proyecto.pdf`, apartados 5, 6, 8, 9 y 12.
Fecha de revisión: **01/11/2026**. El **04/11/2026** es la fecha objetivo
indicada por el equipo; el PDF remite las fechas oficiales al docente. El
trabajo de cierre se planifica hasta el **03/11/2026**, sin adjudicar como
realizadas actividades futuras.

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
- **Apartado 9:** `latex/main.tex` incluye las 14 partes con los títulos del
  índice del docente. El informe incluye tablas y tres figuras derivadas de
  JSON; la presencia de una parte
  no demuestra por sí sola el cumplimiento individual del apartado 12.

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
| AG-C06.03 | Tablas, gráficos, teoría, límites y conclusiones | **Presente** para comparativa principal; retirar cifras de tráfico sin respaldo y matizar causas no medidas. |
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
`guia_ficha_aprendizaje.tex` están ignorados por Git y redactados como
instrucciones de «lo que debes colocar». Sus fechas y actividades no se
corroboraron con constancias originales: **son borradores**, no planes o
bitácoras firmadas. No incorporarlos a la entrega como hechos sin
confirmación de cada autor.

| Persona | Commit fechado y alcance comprobable | Responsabilidad propuesta para el cierre |
| --- | --- | --- |
| Noe Choquenaira | `592589a` (02/10): arquitectura, modelo y Dijkstra; `b307be4` (23/10): A*; `f0799bf` (23/10): informe. | Contrastar formulación y alcance, revisar informe y exposición. |
| Yeni Porroa | `77983b7` (04/10): heap 4-ario; `3b91a5e` (23/10): comparativa de montículos. | Verificar contrato de colas, figuras y explicación de complejidad. |
| Romario Quispe | `72df976` (04/10): Fibonacci y escalabilidad; `e3af921` (23/10): benchmark. | Comprobar protocolo, datos, semilla y reproducibilidad. |
| Aldo Yaranga | `d50e67b` (04/10): pruebas; `65d303d` (23/10): suite y CLI. | Verificar regresiones, instalación y manuales. |

Asignación **propuesta**, no acta ni aprobación de cada estudiante:

| Fecha | Meta antes del 04/11 | Quién valida / evidencia de cierre |
| --- | --- | --- |
| 30/10 | Alinear informe, código y snapshots; registrar ausencias sin completar datos ficticios. | Noe y Romario; diferencias anotadas en `DATOS_Y_MODELO.md`. |
| 31/10 | Revisar certificado, ejecutar pruebas y contrastar todas las cifras y figuras. | Aldo y Yeni; salida de pytest y JSON. |
| 01/11 | Recoger **de cada persona** plan original si existe, reflexión propia y registros auténticos de seguimiento. | Los cuatro autores; usar `plantilla_evidencia_individual.md`. |
| 02/11 | Validar manuales, bibliografía, presentación y comandos desde copia limpia. | Noe y Aldo; rutas, salida y responsable identificados. |
| 03/11 | Compilar PDF, revisar páginas/referencias, ensayar demostración individual y cerrar paquete. | Los cuatro; verificación final firmada por el equipo. |
| 04/11 | Fecha objetivo de entrega comunicada por el usuario, sujeta a calendario del docente. | Confirmar recepción real; no marcar anticipadamente como cumplida. |

## Criterios de cierre

1. `python -m pytest python/tests -q` termina sin fallos; guardar fecha, Python
   usado y conteo real. Los casos adversos deben rechazar ciclos de peso cero
   desconectados y caminos reportados incompletos.
2. En copia limpia están disponibles `latex/`, `colab/`, datos y el PDF.
   Actualmente `latex/` y `colab/` están sin seguimiento Git: preparar la
   inclusión **sin descartar** los archivos previos del equipo. El PDF de
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
ha comprobado instalación de dependencias en una máquina sin ellas, ni se ha
publicado el árbol sin seguimiento Git; ambas comprobaciones siguen abiertas.

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
cliente y estilo de la aplicación. Última suite: **278 pruebas aprobadas**;
el PDF sigue exigiendo evidencias individuales que la interfaz no genera.
