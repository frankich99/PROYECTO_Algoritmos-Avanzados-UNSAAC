# Historial de versiones

## [1.5.0] - 2026-11-06

### Añadido

- Módulo interactivo de pegado directo y formateo rápido de tablas de nodos y aristas con botones de acción (`Pegar`, `Limpiar`, `Agregar`).
- Carpeta canónica `instancias_pruebas/` con datasets estructurados en tabla, JSON y CSV/TXT de simple a complejo.
- Vista ampliada de `Datos y método` y `Evidencias` en la barra de navegación con fórmulas en formato formal estilo LaTeX con zoom individual.

### Cambiado

- Bordes de nodos con color de alto contraste (`strokeColor`) eliminando el contorno blanco que se perdía en fondos claros.
- Nombres de nodos renderizados en color oscuro de alta legibilidad (`#1f1b1c`) ubicados fuera del círculo con halo del color del lienzo.
- Etiquetas de peso y costo de aristas con fondo perimetral nítido y trazos de flechas estilizadas.
- La versión del proyecto pasa a `1.5.0`.

## [1.2.1] - 2026-11-06

### Añadido

- Desglose explícito de aportes meteorológicos (`weather_contributions`: lluvia, visibilidad, ráfagas, humedad) en la API y visualización en la interfaz web.
- Reutilización de lecturas climáticas puntuales (`weather: "saved"`, `weather: "live"`) sin repetir consultas externas al calcular rutas.
- Persistencia opcional en `localStorage` del navegador para recordar claves de proveedores externos (OpenWeatherMap, TomTom) y lecturas climáticas guardadas (`web/src/localSettings.ts`).
- Controles de mapa mejorados: preservación de la cámara/zoom entre pestañas, botones «Centrar ruta» y «Red completa», y diseño responsivo para móviles.
- Proxy de desarrollo configurable con `ROUTES_API_URL` en Vite.

### Cambiado

- La versión del proyecto pasa a `1.2.1`.

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
