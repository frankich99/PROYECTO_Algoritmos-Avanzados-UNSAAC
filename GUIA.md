# Guía de sustentación

**Proyecto:** Rutas mínimas con colas de prioridad en redes viales urbanas del Cusco  
**Curso:** Algoritmos Avanzados (UNSAAC, 2026-II) · **Grupo 5**  
**Docente:** Ing. Héctor Eduardo Ugarte Rojas

Esta guía resume qué afirmar y qué comandos ejecutar. Las cifras proceden de los JSON en `python/data/processed/`. Consultar [`docs/DATOS_Y_MODELO.md`](docs/DATOS_Y_MODELO.md) para unidades y campos faltantes y [`docs/CONTROL_ENTREGA.md`](docs/CONTROL_ENTREGA.md) para el estado al 05/11/2026 y las evidencias individuales pendientes.

---

## 1. El argumento en cinco minutos

1. **Problema.** Se resuelve el camino mínimo desde un origen en un dígrafo dirigido con pesos no negativos que representa una red vial.
2. **Modelo.** Para la instancia didáctica de seis nodos:
   $$w(u,v)=\frac{L(u,v)}{v_{\text{nom}}(u,v)}\left(1+2.5\max(0,\theta(u,v))\right)m_{\text{clima}},$$
   con $L$ en metros, $v_{\text{nom}}$ en m/s, $\theta$ una pendiente supuesta y $m_{\text{clima}}\ge 1$ un factor uniforme. Para distancia, $w=L$. OSM usa `travel_time_sec`, **no** la pendiente del ejemplo. Tráfico horario y clima no son tiempos medidos.
3. **Comparación.** Se usa el mismo solver Dijkstra y la misma instancia con tres colas: binary heap indexado, 4-ary heap indexado ($d=4$) y Fibonacci heap.
4. **Corrección.** Las tres colas deben producir las mismas distancias. Se verifica contra Bellman-Ford, NetworkX y un certificado que exige caminos de predecesores hasta el origen. Sin caminos explícitos cuesta $O(|V|+|E|)$; si hay caminos materializados añade el tiempo de leerlos.
5. **Experimento.** Perfiles sintéticos reproducibles: disperso ($|E|=4|V|$) y denso ($|E|=0.08|V|(|V|-1)$), cinco escalas por perfil, tres instancias por escala, 15 repeticiones, semilla 12345. Caso aplicado: una consulta sobre la red OSM de Cusco (891 vértices, 2139 aristas).
6. **Resultado.** El 4-ario obtiene la menor mediana en 7 de 10 escalas sintéticas; el binario, en 3, y también en la consulta OSM. Fibonacci no gana ninguna. Los IQR se solapan en las 10 escalas, así que no se declara un vencedor universal.
7. **$A^*$.** Extensión punto a punto con heurística euclidiana escalada y consistente. En OSM reduce las expansiones de 887 a 823 ($-7.2\%$); en la instancia manual, de 6 a 5 ($-16.7\%$). El costo óptimo no cambia.
8. **Clima.** La observación Open-Meteo histórica conservada en `applied_results.json` produce $m_{\text{clima}}=1.0691$ y 413.952 s estimados ($+6.91\%$). Carece de humedad y presión: 50 % es un valor de reserva para humedad y la presión falta. El snapshot local posterior de OpenWeatherMap es distinto y no cambia este resultado. La ruta no cambia porque el factor es uniforme.

---

## 2. Preguntas del docente y respuestas breves

### ¿Cómo se incorpora la topografía?

Con la pendiente $\theta$ en el peso de tiempo **solo para la instancia ilustrativa**. Se penaliza el ascenso: $\max(0,\theta)$. Un 8\,\% se escribe $0.08$. La red OSM no incluye pendiente por arista; no se ha medido allí el efecto de la topografía.

### ¿Qué es el «Dijkstra modificado»?

No es otro algoritmo. Es Dijkstra con pesos de tiempo en lugar de distancias. La modularidad permite inyectar la cola sin reescribir el solver. `--metric distance` usa $w=L$; `--metric time` usa la fórmula anterior **en la red manual** o el campo temporal del snapshot **en OSM**.

### ¿Por qué tres colas y cuál es mejor?

Para separar el efecto de la estructura del efecto del algoritmo. Resultados medidos:

| Cola | Victorias sintéticas | Consulta OSM (mediana) | Lectura |
| :--- | :---: | :---: | :--- |
| Binary heap | 3 de 10 | **15.65 ms** | Menor tiempo en OSM; opción por defecto. |
| 4-ary heap | **7 de 10** | 19.87 ms (+26.9\,\%) | Ventaja mediana de 3.6--4.6\,\% en sintéticos, con IQR solapados. |
| Fibonacci heap | 0 de 10 | 26.09 ms (+66.7\,\%) | 1.05--1.59 veces más lento que el binario. |

La respuesta correcta no es «el 4-ario siempre gana». Es: **depende de la escala, la densidad y el entorno**. En esta implementación de Python, el Fibonacci no traduce su cota asintótica en ventaja práctica.

### ¿Usaron NetworkX para resolver el problema?

No. Dijkstra, las tres colas, $A^*$ y el certificado son código propio. NetworkX y Bellman-Ford se usan solo como oráculos externos de verificación.

### ¿Plotly o Graphviz?

La web oficial usa React/TypeScript y MapLibre; Plotly se retiró junto con la aplicación Streamlit. Graphviz se usa para exportar la especificación `.dot` de la ruta desde la CLI.

### ¿Cuánto poda $A^*$?

Lo medido: 887 $\to$ 823 expansiones en OSM ($-7.2\%$) y 6 $\to$ 5 en la instancia manual ($-16.7\%$). No se afirma un rango universal del 30--70\,\%: no fue medido y dependería de la heurística y del grafo.

### ¿Cómo se valida que la ruta es óptima?

Con comparación de distancias contra NetworkX y un certificado propio: comprueba $d[s]=0$, desigualdades en cada arista y que los predecesores de distancias finitas lleven realmente al origen. Cuando se reportan rutas, verifica también sus aristas y costos. Las desigualdades solas no descartan un ciclo de peso cero desconectado.

### ¿El clima puede cambiar la ruta?

No con un factor uniforme. Si $w_m(P)=m\,w(P)$ para todo camino $P$ y $m>0$, el camino que minimiza $w$ también minimiza $w_m$. El clima es un análisis de sensibilidad temporal. Para que cambiara la ruta, el factor tendría que depender del tramo.

### ¿Midieron memoria?

No. No se reportan métricas de memoria residente ni de asignaciones. Las cotas espaciales del informe son teóricas.

### ¿La instancia de seis nodos es real?

Los nombres son reales; longitudes, pendientes y topología son ilustrativas. La red real es el snapshot OSM de 891 vértices y 2139 aristas.

---

## 3. Comandos para la demostración

Desde la raíz del repositorio, entrar en `python/`:

```powershell
cd python
```

El Python del proyecto está en el `.venv` de la raíz. Desde `python/`, se invoca con `..\.venv\Scripts\python.exe`.

### 3.1 Alternativas disponibles

```powershell
..\.venv\Scripts\python.exe main.py list
```

Muestra `binary_heap`, `4ary_heap`, `fibonacci_heap`, `bellman_ford` y `all`.

### 3.2 Dijkstra con las tres colas

```powershell
..\.venv\Scripts\python.exe main.py compare --metric time
..\.venv\Scripts\python.exe main.py compare --metric distance
```

Verifica que las distancias sean equivalentes, que los certificados sean válidos y compara los contadores de operaciones. No confundir los contadores de la estructura con el tiempo de pared: la comparación de rendimiento usa el benchmark canónico.

### 3.3 $A^*$ frente a Dijkstra

```powershell
..\.venv\Scripts\python.exe main.py astar --target E
```

Salida esperada: Dijkstra expande 6 nodos y $A^*$ 5, ambos con costo $165.33$ s y la ruta `A -> B -> D -> E`. La reducción es $16.7\%$.

### 3.4 Traza manual (Cormen, Fig. 24.6)

```powershell
..\.venv\Scripts\python.exe main.py run -i data/instances/clrs_24_6.txt --trace
```

Muestra la extracción de nodos, las relajaciones y la verificación final. Es la traza que se puede seguir en la pizarra.

### 3.5 Grafo dictado en vivo

```powershell
..\.venv\Scripts\python.exe main.py run --inline "A B 4; A C 1; C B 2; B D 5; C D 8" -s A -q all
```

Resuelve el grafo con las tres colas en simultáneo.

### 3.6 Entrada inválida

```powershell
..\.venv\Scripts\python.exe main.py run -i data/instances/invalidas/peso_negativo.txt
```

Debe imprimir un error explicativo y salir con código `2`. No debe producir una ruta.

### 3.7 Graphviz

```powershell
..\.venv\Scripts\python.exe main.py graphviz --target E
```

Genera `results/figures/ruta_optima_cusco.dot` con la ruta resaltada.

### 3.8 Suite de pruebas

Desde la raíz del repositorio:

```powershell
cd ..
.\.venv\Scripts\python.exe -m pytest python/tests -q
```

Última verificación de esta revisión: **291 passed** (duración variable).

### 3.9 Reproducción canónica

```powershell
.\.venv\Scripts\python.exe python/scripts/reproduce_canonical.py
```

Este comando repite la medición y **sobrescribe** `benchmark_results.json` y `applied_results.json`. Ejecutarlo solo en una copia separada para preservar las muestras del 28/10/2026. Reutiliza los snapshots OSM y meteorológico; no necesita Internet si ya existen.

Para reescribir solo tablas y figuras:

```powershell
.\.venv\Scripts\python.exe python/scripts/reproduce_canonical.py --skip-benchmark --skip-applied
```

### 3.10 Aplicación web (React + FastAPI)

En dos terminales, desde la raíz y desde `web/`:

```powershell
.\.venv\Scripts\python.exe -m uvicorn web_api:app --app-dir python --host 127.0.0.1 --port 8000
```

```powershell
cd web
npm run dev
```

Abrir <http://127.0.0.1:5173/>. La API queda en <http://127.0.0.1:8000/docs>. La antigua aplicación Streamlit fue retirada.

### 3.11 Informe

```powershell
cd latex
.\compilar.ps1
```

Genera `latex/main.pdf`.

---

## 4. Recorrido de la aplicación

| Vista | Qué mostrar |
| :--- | :--- |
| **Rutas** | Elegir red central o ampliada, IDs o coordenadas, costo, cola y $A^*$. Contrastar tres colas con $A^*$ sin usar la ejecución interactiva como benchmark; seleccionar clima histórico/local y descargar JSON. |
| **Instancias** | Crear un grafo desde tabla, JSON o TXT/CSV, o generarlo con semilla; validar nodos, aristas y pesos antes de resolver. |
| **Comparar** | Revisar el banco canónico por perfil y escala, y agregar consultas de la sesión sin mezclarlas con las mediciones históricas. |
| **Experimentos** | Medir redes sintéticas nuevas, separadas del informe y etiquetadas como resultados de sesión. |
| **Cobertura Cusco** | Distinguir el snapshot central de 1,5 km del centro ampliado de 3 km; ninguno es todo Cusco. |
| **Datos y método** | Mostrar fuentes, verificación, límites y enlaces al contrato OpenAPI. |

El cálculo, el benchmark y el plano local funcionan sin Internet; solo el mapa base necesita teselas. Una consulta meteorológica opcional no borra el snapshot si falla.

---

## 5. Cifras para memorizar

| Dato | Valor |
| :--- | :--- |
| Red OSM | 891 vértices, 2139 aristas dirigidas |
| Consulta OSM | 17 vértices, 2810.6 m, costo base 387.197 s |
| Tiempos OSM | Binary 15.65 ms · 4-ary 19.87 ms · Fibonacci 26.09 ms |
| Victorias sintéticas | 4-ary 7/10 · Binary 3/10 · Fibonacci 0/10 |
| Razón mediana 4-ary/Binary | 0.964 disperso · 0.954 denso · 0.959 global |
| Razón mediana Fibonacci/Binary | 1.345 disperso · 1.374 denso · 1.360 global |
| Rango Fibonacci/Binary | 1.05--1.59 veces más lento |
| Solapamiento de IQR | 10/10 escalas (4-ary vs Binary) |
| $A^*$ en OSM | 887 $\to$ 823 expansiones ($-7.2\%$) |
| $A^*$ manual | 6 $\to$ 5 expansiones ($-16.7\%$) |
| Clima | $m=1.0691$; 413.952 s; $+6.91\%$; ruta sin cambios |
| Pruebas | 291 casos aprobados en esta revisión; repetir en el entorno final |

---

## 6. Afirmaciones que no se deben hacer

* «El 4-ary es siempre el mejor.» Falso: gana 7/10 medianas sintéticas, pero pierde la consulta OSM y los IQR se solapan.
* «$A^*$ poda entre 30\,\% y 70\,\% de los nodos.» No fue medido. Los valores medidos son 7.2\,\% y 16.7\,\%.
* «Usamos SENAMHI.» No hay API pública documentada de SENAMHI en este proyecto. La fuente es Open-Meteo, que entrega datos de modelo.
* «El clima puede cambiar la ruta.» Con un factor uniforme, no.
* «La observación usada para el informe registró humedad y presión.» No las registró. El archivo local posterior de OpenWeatherMap sí reporta 55 % de humedad y 651 hPa de presión de suelo; sus 1013 hPa son presión al nivel del mar, no presión superficial.
* «TomTom o el tráfico por calle cambia la ruta OSM.» No existe ese cálculo por arista ni un experimento canónico de congestión.
* «AG-C06 está cumplido para cada integrante.» Faltan evidencias individuales y defensa; ver el control de entrega.
* «Medimos memoria.» No se midió.
* «La instancia de seis nodos es un levantamiento real.» Es ilustrativa.
* «La web usa Plotly o Streamlit.» Ya no: la interfaz oficial usa React/TypeScript y MapLibre; Streamlit se retiró.
* «El notebook de Colab genera los resultados canónicos.» Es didáctico; la fuente canónica es `python/scripts/reproduce_canonical.py` y los JSON versionados.

---

## 7. Cierre en una frase

La elección de cola de prioridad no se decide por su cota asintótica aislada: en esta implementación, el heap binario es la opción por defecto, el 4-ario es competitivo en redes sintéticas y el Fibonacci, pese a su $O(E+V\log V)$, resulta más lento por el costo constante de sus operaciones en Python.
