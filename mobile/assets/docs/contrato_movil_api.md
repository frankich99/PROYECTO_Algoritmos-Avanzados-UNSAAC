# Contrato de compatibilidad Web, Móvil y API (Etapa 1)

Contrato común entre `python/web_api.py`, `web/` y `mobile/`. Ninguna pantalla móvil debe duplicar los algoritmos de optimización ni redefinir límites distintos a los expuestos por FastAPI.

## 1. Versionado independiente

El endpoint `GET /api/v1/version` expone por separado:

- `version` / `api_version`: versión del servicio y contrato HTTP (`1.5.0`).
- `data_version`: fecha de corte de los snapshots canónicos (`2026-10-28`).
- `docs_version`: revisión vigente de documentación y notas metodológicas (`2026-11-06`).
- `generator_version`: versión de los generadores reproducibles en Python (`1.0.0`).
- `web_build`: disponibilidad del compilado React servido por FastAPI.

## 2. Límites unificados (fuente única en `/api/v1/catalog -> limits`)

| Parámetro | Valor | Uso |
| --- | ---: | --- |
| `max_nodes` | 5000 | Máximo de vértices por instancia |
| `max_edges` | 30000 | Máximo de aristas por instancia |
| `max_payload_bytes` | 2000000 | Límite de JSON/texto en bytes UTF-8 (~2 MB) |
| `display_max_nodes` | 1200 | Umbral de simplificación visual en `display_limited` |
| `display_max_edges` | 3000 | Máximo de aristas en `display_edges` (solo vista previa) |
| `generator_nodes_min`..`max` | 2..500 | Nodos para `random`, `sparse` y `dense` |
| `generator_grid_min`..`max` | 1..30 | Filas/columnas para `grid` (mínimo 2 nodos) |
| `experiment_sizes_max_count` | 4 | Cantidad máxima de tamaños en `/experiments` |
| `experiment_size_min`..`max` | 5..200 | Rango válido de tamaños por experimento (sin repetir) |
| `experiment_runs_min`..`max` | 2..10 | Repeticiones medidas por instancia |
| `seed_min`..`seed_max` | 0..2147483647 | Semilla entera reproducible (incluye `0`) |

## 3. Matriz de requisitos, pantallas y endpoints

| Requisito | Pantalla móvil | Endpoint / Origen | Prueba asociada |
| --- | --- | --- | --- |
| Disponibilidad y versiones | Ajustes / Banner de estado | `GET /api/v1/health`, `GET /api/v1/version` | `test_version_endpoint`, `test_contract_versions_limits_and_explicit_openapi_schemas` |
| Catálogo, colas, claves y límites | Rutas / Instancias / Experimentos | `GET /api/v1/catalog` | `test_catalog_and_openapi`, `mobile/test/api_client_test.dart` |
| Validar instancia y previsualizar | Instancias / Editor / Grafo | `POST /api/v1/instances/validate` | `test_invalid_graph_rejected`, `test_preview_large_network_keeps_bounded_edges` |
| Exportar instancia completa sin recorte | Instancias / Biblioteca | `POST /api/v1/instances/export` | `test_export_instance_is_complete_and_reimportable_without_truncation` |
| Calcular ruta y comparar 4 alternativas | Rutas / Comparar | `POST /api/v1/routes/solve` | `test_manual_example_all_queues_and_edges`, `test_arbitrary_new_instance_and_no_path` |
| Benchmark canónico (1350) y piloto (18) | Análisis / Comparar | `GET /api/v1/benchmarks/{profile}`, `GET /api/v1/benchmarks/pilot/summary` | `test_benchmark_read_only_and_new_experiment` |
| Experimentos de sesión | Análisis / Experimentos | `POST /api/v1/experiments` | `test_contract_versions_limits_and_explicit_openapi_schemas`, `web/tests/experimentInput.test.ts` |
| Clima y tráfico puntual | Rutas / Cobertura Cusco | `POST /api/v1/conditions` | `test_live_condition_mock_without_network`, `test_server_keys_used_without_browser_key_and_optional_override` |

## 4. Reglas del contrato que el cliente móvil debe respetar

1. **Valores nulos y rutas inalcanzables:** cuando no hay camino dirigido, `result.cost` es `null`, `result.path` es `[]` y `result.edges` es `[]`. No es un error HTTP ni equivale a costo `0`.
2. **Identificadores mixtos:** los IDs de vértices pueden llegar como `String` (`"A"`, `"N0"`) o `int` (`1008097623`). Conservar el valor original al reenviar solicitudes (`source`, `target`) y usar claves de texto al indexar `coords`.
3. **Unidades y métricas:** `unit` solo vale `"s"` (tiempo vial), `"m"` (distancia vial) o `"peso"` (pesos genéricos/abstractos). Un grafo genérico nunca acredita segundos ni metros aunque su JSON declare `"metric": "time"`.
4. **Coordenadas:** en respuestas de la API (`coords`, `path_coords`, `path_geometry`), cada punto viene en orden **`[lon, lat]`**. En formularios y objetos `Point` (`source_point`, `target_point`, `grid_point`), los campos son nombrados `{ "lat": ..., "lon": ... }`.
5. **Vista previa vs exportación:** `display_edges` de `/instances/validate` puede estar muestreada hasta 3000 aristas (`display_limited: true`). Para guardar, duplicar o compartir una instancia generada o grande, usar siempre `POST /api/v1/instances/export`.
6. **Semillas entre lenguajes:** una semilla en Dart no equivale al PRNG de Python. Toda generación oficial ocurre en el backend y se guarda junto con `generator`, `generator_version`, `seed` y el grafo completo exportado.
7. **Errores HTTP:** los errores de validación devuelven HTTP `422` con `detail` en texto o lista de validaciones Pydantic; errores de servidor (`5xx`) o tiempo de espera deben mostrarse separados de «sin camino».
