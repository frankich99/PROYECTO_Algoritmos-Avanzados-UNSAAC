# Revisión técnica y de interfaz de la segunda entrega

Alcance: web React/FastAPI de la rama `ramaFRANKI`, base `3b8acae`, y sus evidencias. Cambios locales sin commit ni publicación. Se conserva la dirección institucional de `DESIGN.md`: ENERGY 2 / RHYTHM 2 / MOTION 1, tema claro, granate/dorado y títulos Georgia.

## Resultado del análisis

| Requisito | Situación encontrada | Corrección / evidencia |
| --- | --- | --- |
| Implementación e integración | Núcleo y API presentes | Pruebas del flujo de cuatro generadores, semillas 0/42/12345 y cuatro comparaciones por ruta |
| Pruebas | Conteo fijo y afirmación incorrecta de cobertura total | 346 Python y 42 web aprobadas; XML/JSON reales alimentan el registro |
| Complejidad | Cotas de operaciones, pero sin memoria ni alcance del núcleo | Tabla con peor caso/amortización, espacio, operaciones dominantes, costos extra y ausencia de modelo promedio |
| Modelos | Pendientes y coeficientes presentados como hechos físicos; NaN/infinito aceptados por el modelo | Supuestos explícitos, fórmula climática con límites, rechazo de entradas no finitas y referencia de costo conocido |
| Experimentos | Banco real mezclado con capacidades ficticias en respaldo estático | Nuevo piloto de 120 tiempos; históricos intactos; Pages sin API no fabrica benchmarks/proveedores |
| Documentación | Material amplio, pero estado desactualizado y hashes históricos distintos | Guía de reproducción y matriz de los siete productos; el control anterior se marca histórico |
| Bitácora | No había cronología actual en la web | 60 commits con fecha, autor y enlace; consulta remota guardada; sin inventar reuniones o dedicación |

## Verificación de interacción

- PASS: matriz de siete requisitos con enlaces a sus secciones.
- PASS: la bitácora filtra a Yeni Porroa y muestra sus dos commits; expansión/reducción del historial funciona.
- PASS: guía, bitácora, evidencia JSON y piloto descargan con HTTP 200.
- PASS: modelo climático despliega su fórmula; ampliar muestra 115 % y restablecer vuelve a 100 % por botón accesible.
- PASS: experimento con `30, no` muestra error; tamaño 10, semilla 0 y dos repeticiones producen tres filas reales.
- PASS: cuadrícula editable 3×4 produce 12 nodos/34 aristas; solo recorrido muestra 6 nodos/5 aristas; desactivar nombres/pesos elimina los rótulos.
- PASS: vistas desktop y móvil revisadas visualmente; sin desbordamiento horizontal de página. Tablas extensas tienen desplazamiento interno.
- PASS: consola sin errores en los recorridos locales comprobados; `npm run build` completa. Persiste advertencia de tamaño del bundle MapLibre, no un fallo de compilación.
- PASS: suite Python 346/346 y web 42/42; no se afirma cobertura de líneas. Persiste aviso de deprecación de TestClient/httpx.

## Decisiones visuales y puerta de entrega

- R-01/06/20/29/31 PASS: se conserva la paleta y tipografía de DESIGN.md; el granate identifica acciones/enlaces, no decora cada bloque.
- R-03/25/32 PASS: texto oscuro sobre papel claro, foco visible, controles nuevos nativos de al menos 44 px y prueba móvil sin overflow de página.
- R-02/17/18/23/36/38 PASS: sin testimonios, activos inventados, estadísticas promocionales ni afirmaciones empíricas sin fuente en las secciones revisadas.
- R-24/26/35 PASS: enlaces, filtros, descargas, reintentos, pestañas, casillas y formularios comprobados; pruebas automatizadas para carga/error/vacío.
- R-27/28/33/34/37 PASS: estados explícitos, sin FAQ de relleno, sin tema alternativo incompleto ni scripts que reescriban la UI; dirección visual existente preservada.
- Propósito y composición PASS: matriz para encontrar evidencias; listas y tablas para leer resultados; fórmulas bajo desplegables; sin tarjetas uniformes de relleno ni animación decorativa.
- C-1 a C-5 PASS en el alcance revisado: decisiones justificadas, controles funcionales, composición por contenido y límites documentados.

## Pendientes que el código no acredita

Instalación en máquina limpia, bitácoras individuales de aprendizaje, actas, presentación y defensa. El PDF guardado no se recompiló en esta revisión. Ningún conteo de commits constituye una nota ni un porcentaje de participación. La web pública no cambia hasta publicar estos archivos.
