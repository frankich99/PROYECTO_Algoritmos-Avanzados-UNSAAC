# Guía de sustentación

**Proyecto:** Rutas mínimas con colas de prioridad en redes viales urbanas del Cusco  
**Curso:** Algoritmos Avanzados (UNSAAC, 2026-II) · **Grupo 5**  
**Docente:** Ing. Héctor Eduardo Ugarte Rojas

Esta guía resume qué afirmar, qué no afirmar y qué comandos ejecutar. Las cifras provienen de los JSON versionados en `python/data/processed/` y del informe `documento/main.pdf` (50 páginas totales, 38 de cuerpo).

---

## 1. El argumento en cinco minutos

1. **Problema.** Se resuelve el camino mínimo desde un origen en un dígrafo dirigido con pesos no negativos que representa una red vial.
2. **Modelo.** Para la métrica de tiempo:
   $$w(u,v)=\frac{L(u,v)}{v_{\text{nom}}(u,v)}\left(1+2.5\max(0,\theta(u,v))\right)m_{\text{clima}},$$
   con $L$ en metros, $v_{\text{nom}}$ en m/s, $\theta$ la pendiente como fracción y $m_{\text{clima}}\ge 1$ un factor uniforme. Para distancia, $w=L$. No es una calibración de tránsito: pendiente y clima son escenarios explícitos.
3. **Comparación.** Se usa el mismo solver Dijkstra y la misma instancia con tres colas: binary heap indexado, 4-ary heap indexado ($d=4$) y Fibonacci heap.
4. **Corrección.** Las tres colas deben producir las mismas distancias. Se verifica contra Bellman-Ford, contra NetworkX y con un certificado de optimalidad $O(|V|+|E|)$.
5. **Experimento.** Perfiles sintéticos reproducibles: disperso ($|E|=4|V|$) y denso ($|E|=0.08|V|(|V|-1)$), cinco escalas por perfil, tres instancias por escala, 15 repeticiones, semilla 12345. Caso aplicado: una consulta sobre la red OSM de Cusco (891 vértices, 2139 aristas).
6. **Resultado.** El 4-ario obtiene la menor mediana en 7 de 10 escalas sintéticas; el binario, en 3, y también en la consulta OSM. Fibonacci no gana ninguna. Los IQR se solapan en las 10 escalas, así que no se declara un vencedor universal.
7. **$A^*$.** Extensión punto a punto con heurística euclidiana escalada y consistente. En OSM reduce las expansiones de 887 a 823 ($-7.2\%$); en la instancia manual, de 6 a 5 ($-16.7\%$). El costo óptimo no cambia.
8. **Clima.** El snapshot de Open-Meteo produce $m_{\text{clima}}=1.0691$ y un tiempo ajustado de $413.952$ s ($+6.91\%$). La ruta no cambia porque el factor es uniforme.

---

## 2. Preguntas del docente y respuestas breves

### ¿Cómo se incorpora la topografía?

Con la pendiente $\theta$ en el peso de tiempo. Solo se penaliza el ascenso: $\max(0,\theta)$. Un 8\,\% de pendiente se escribe $0.08$. La red manual usa nombres reales, pero longitudes, pendientes y topología son esquemáticas; no son levantamiento de campo.

### ¿Qué es el «Dijkstra modificado»?

No es otro algoritmo. Es Dijkstra con pesos de tiempo en lugar de distancias. La modularidad permite inyectar la cola sin reescribir el solver. `--metric distance` usa $w=L$; `--metric time` usa la fórmula anterior.

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

Plotly se usa en la aplicación Streamlit para los gráficos interactivos. Graphviz se usa para exportar la especificación `.dot` de la ruta. No se descartó Plotly.

### ¿Cuánto poda $A^*$?

Lo medido: 887 $\to$ 823 expansiones en OSM ($-7.2\%$) y 6 $\to$ 5 en la instancia manual ($-16.7\%$). No se afirma un rango universal del 30--70\,\%: no fue medido y dependería de la heurística y del grafo.

### ¿Cómo se valida que la ruta es óptima?

Con dos comprobaciones independientes: comparación de distancias contra NetworkX y certificado de Bellman, que recorre todas las aristas y verifica $d[v]\le d[u]+w(u,v)$ para todo camino. Si una arista viola la desigualdad, el certificado falla.

### ¿El clima puede cambiar la ruta?

No con un factor uniforme. Si $w_m(P)=m\,w(P)$ para todo camino $P$ y $m>0$, el camino que minimiza $w$ también minimiza $w_m$. El clima es un análisis de sensibilidad temporal. Para que cambiara la ruta, el factor tendría que depender del tramo.

### ¿Midieron memoria?

No. No se reportan métricas de memoria residente ni de asignaciones. Las cotas espaciales del informe son teóricas.

### ¿La instancia de seis nodos es real?

Los nombres son reales; longitudes, pendientes y topología son ilustrativas. La red real es el snapshot OSM de 891 vértices y 2139 aristas.

---

## 3. Comandos para la demostración

Abrir la terminal en `F:\unsaac\alg-avanzados\proyecto\python`:

```powershell
cd F:\unsaac\alg-avanzados\proyecto\python
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
cd F:\unsaac\alg-avanzados\proyecto
.\.venv\Scripts\python.exe -m pytest python/tests -q
```

Resultado de una ejecución completa: **246 passed in 45.86s**.

### 3.9 Reproducción canónica

```powershell
.\.venv\Scripts\python.exe python/scripts/reproduce_canonical.py
```

Regenera `benchmark_results.json`, `applied_results.json`, las tablas de `documento/tablas/` y las figuras de `documento/figuras/`. Reutiliza los snapshots OSM y meteorológico; no necesita Internet si ya existen.

Para reescribir solo tablas y figuras:

```powershell
.\.venv\Scripts\python.exe python/scripts/reproduce_canonical.py --skip-benchmark --skip-applied
```

### 3.10 Aplicación Streamlit

```powershell
cd python
..\.venv\Scripts\python.exe -m streamlit run app.py
```

Abrir la URL que imprime Streamlit (por defecto `http://localhost:8501`).

### 3.11 Informe

```powershell
cd documento
.\compilar.ps1
```

Genera `documento/main.pdf`.

---

## 4. Recorrido de la aplicación

| Vista | Qué mostrar |
| :--- | :--- |
| **Comparación** | Curvas de mediana e IQR por perfil, tabla de escalas y síntesis de victorias. Señalar que los IQR se solapan. |
| **Ruta OSM** | Elegir origen y destino, ejecutar Dijkstra o $A^*$, comparar costo base y costo con clima. La ruta se dibuja desde el snapshot local. |
| **Traza manual** | Ejecutar paso a paso la instancia de seis nodos y mostrar extracción, relajación y cola. |
| **Procedencia** | Protocolo, fuentes, snapshots y actualización opcional de Open-Meteo. |

La aplicación funciona sin Internet porque lee los snapshots locales. La actualización meteorológica es opcional y no borra el snapshot anterior si falla.

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
| Pruebas | 246 passed in 45.86s |

---

## 6. Afirmaciones que no se deben hacer

* «El 4-ary es siempre el mejor.» Falso: gana 7/10 medianas sintéticas, pero pierde la consulta OSM y los IQR se solapan.
* «$A^*$ poda entre 30\,\% y 70\,\% de los nodos.» No fue medido. Los valores medidos son 7.2\,\% y 16.7\,\%.
* «Usamos SENAMHI.» No hay API pública documentada de SENAMHI en este proyecto. La fuente es Open-Meteo, que entrega datos de modelo.
* «El clima puede cambiar la ruta.» Con un factor uniforme, no.
* «Medimos memoria.» No se midió.
* «La instancia de seis nodos es un levantamiento real.» Es ilustrativa.
* «No usamos Plotly.» Se usa en Streamlit.
* «El notebook de Colab genera los resultados canónicos.» Es didáctico; la fuente canónica es `python/scripts/reproduce_canonical.py` y los JSON versionados.

---

## 7. Cierre en una frase

La elección de cola de prioridad no se decide por su cota asintótica aislada: en esta implementación, el heap binario es la opción por defecto, el 4-ario es competitivo en redes sintéticas y el Fibonacci, pese a su $O(E+V\log V)$, resulta más lento por el costo constante de sus operaciones en Python.
