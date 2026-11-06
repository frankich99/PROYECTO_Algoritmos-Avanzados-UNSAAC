# Historial de versiones

## [1.2.0] - 2026-11-05

### Añadido

- Aplicación web oficial en React + TypeScript (`web/`) con seis vistas: rutas,
  instancias, comparación, experimentos, cobertura Cusco y datos y método.
- API FastAPI (`python/web_api.py`) para validar instancias, resolver rutas con
  Dijkstra/A*, comparar las tres colas, consultar el banco canónico, ejecutar
  experimentos de sesión y consultar condiciones puntuales.
- Cobertura OSM ampliada del centro de Cusco (1938 nodos y 4753 aristas) con
  revisión previa y límites de servicio.
- Servicio de producción que entrega la web compilada y la API en el mismo
  origen, con endpoint `/api/v1/version` y CORS opcional.
- Paquete publicable reproducible con `python/scripts/build_publicable.py`
  (carpeta y ZIP listos para Render, Railway, Docker o un VPS).
- Guía de despliegue en [`docs/DESPLIEGUE.md`](docs/DESPLIEGUE.md).

### Cambiado

- La versión del proyecto pasa a `1.2.0`.
- La interfaz Streamlit y sus dependencias fueron retiradas; la única interfaz
  web es React + TypeScript.
- La API permite configurar la URL del backend con `VITE_API_BASE_URL` cuando
  la web se publica en un origen distinto.

### Conservado

- Los JSON de mediciones canónicas y el informe LaTeX no se recalculan al usar
  la web. Las consultas y experimentos nuevos se etiquetan como resultados de
  sesión.
