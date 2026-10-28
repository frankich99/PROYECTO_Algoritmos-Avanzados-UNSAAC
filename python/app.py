"""Aplicación Streamlit integrada para el estudio de rutas mínimas."""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, Hashable, List

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.algorithms.a_star import a_star_solver
from src.algorithms.dijkstra import dijkstra_solver
from src.benchmarks.applied_analysis import uniformly_scaled
from src.io.osm_loader import load_snapshot as load_osm_snapshot
from src.models.cusco_network import load_cusco_instance
from src.services.weather import OpenMeteoClient, load_snapshot as load_weather_snapshot, weather_multiplier

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data" / "processed"
BENCHMARK_PATH = DATA_DIR / "benchmark_results.json"
OSM_PATH = DATA_DIR / "cusco_osm_drive.json"
WEATHER_PATH = DATA_DIR / "weather_cusco.json"
APPLIED_PATH = DATA_DIR / "applied_results.json"

QUEUE_LABELS = {
    "binary_heap": "Binary Heap indexado",
    "4ary_heap": "4-ary Heap indexado",
    "fibonacci_heap": "Fibonacci Heap",
}
QUEUE_SHORT_LABELS = {
    "binary_heap": "Binary Heap",
    "4ary_heap": "4-ary Heap",
    "fibonacci_heap": "Fibonacci Heap",
}
QUEUE_COLORS = {
    "binary_heap": "#681C32",
    "4ary_heap": "#8A6418",
    "fibonacci_heap": "#4C5866",
}


def apply_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --unsaac-granate: #681C32;
            --unsaac-dorado: #8A6418;
            --tinta: #1F1B1C;
            --papel: #F7F3EA;
            --linea: #D8CCB4;
        }
        html, body, .stApp { font-family: "Segoe UI", sans-serif; color: var(--tinta); }
        .stApp { background: var(--papel); }
        header[data-testid="stHeader"], [data-testid="stSidebar"],
        [data-testid="stExpandSidebarButton"], [data-testid="stToolbar"] { display: none !important; }
        .block-container { padding-top: 1.4rem; }
        .institution-line {
            display: flex;
            align-items: baseline;
            justify-content: space-between;
            gap: 1rem;
            border-bottom: 1px solid var(--linea);
            padding-bottom: .7rem;
            margin-bottom: .7rem;
        }
        .institution-line strong { color: var(--unsaac-granate); font-family: Georgia, serif; font-size: 1.1rem; }
        .institution-line span { color: #4B4244; font-size: .9rem; }
        h1, h2, h3 { font-family: Georgia, "Times New Roman", serif; color: var(--unsaac-granate) !important; }
        h1 { letter-spacing: -0.025em; border-bottom: 2px solid var(--unsaac-granate); padding-bottom: .45rem; }
        [data-testid="stMetric"] {
            background: #FFFFFF;
            border: 1px solid var(--linea);
            border-radius: 4px;
            padding: .85rem 1rem;
        }
        [data-testid="stMetricValue"] { font-family: Georgia, serif; color: var(--unsaac-granate); }
        .stButton > button, .stDownloadButton > button {
            min-height: 44px;
            border-radius: 3px;
            border: 1px solid var(--unsaac-granate);
            background: var(--unsaac-granate);
            color: #FFFFFF;
            font-weight: 650;
        }
        .stButton > button:hover, .stDownloadButton > button:hover {
            border-color: var(--unsaac-dorado);
            background: #511426;
            color: #FFFFFF;
        }
        button:focus-visible, input:focus-visible, [role="radio"]:focus-visible,
        [role="combobox"]:focus-visible, a:focus-visible {
            outline: 3px solid #8A6418 !important;
            outline-offset: 2px;
        }
        [data-testid="stDataFrame"], [data-testid="stPlotlyChart"] {
            background: #FFFFFF;
            border: 1px solid var(--linea);
            border-radius: 4px;
        }
        .evidence-note {
            border-top: 1px solid var(--linea);
            margin-top: 1.25rem;
            padding-top: .75rem;
            color: #4B4244;
            font-size: .92rem;
        }
        @media (max-width: 760px) {
            .block-container { padding: 1.25rem .9rem 3rem; }
            .institution-line { align-items: flex-start; flex-direction: column; gap: .15rem; }
            h1 { font-size: clamp(1.8rem, 9vw, 2.4rem); }
            h2 { font-size: clamp(1.35rem, 7vw, 1.8rem); }
            [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; gap: .75rem !important; }
            [data-testid="column"] { flex: 1 1 240px !important; min-width: 0 !important; width: 100% !important; }
            .stButton > button, .stDownloadButton > button { width: 100%; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def load_json(path: str, modified_ns: int) -> Dict[str, Any]:
    del modified_ns
    return json.loads(Path(path).read_text(encoding="utf-8"))


@st.cache_resource(show_spinner=False)
def load_osm(path: str, metric: str, modified_ns: int):
    del modified_ns
    return load_osm_snapshot(path, metric=metric)


def file_version(path: Path) -> int:
    return path.stat().st_mtime_ns


def benchmark_frame(results: Dict[str, Any], profile: str) -> pd.DataFrame:
    profile_data = results.get("profiles", {}).get(profile, {})
    rows: List[Dict[str, Any]] = []
    for queue in results.get("queue_types", []):
        for item in profile_data.get("data", {}).get(queue, []):
            rows.append(
                {
                    "cola": queue,
                    "estructura": QUEUE_LABELS.get(queue, queue),
                    "vertices": item["nodes"],
                    "aristas": item["edges"],
                    "mediana_us": item["median_us"],
                    "q1_us": item["q1_us"],
                    "q3_us": item["q3_us"],
                    "sample_count": item.get("sample_count", 0),
                    "speedup_binary": item["speedup_vs_binary"],
                }
            )
    return pd.DataFrame(rows)


def benchmark_figure(frame: pd.DataFrame, profile: str) -> go.Figure:
    figure = go.Figure()
    for queue, label in QUEUE_LABELS.items():
        subset = frame[frame["cola"] == queue].sort_values("vertices")
        if subset.empty:
            continue
        figure.add_trace(
            go.Scatter(
                x=subset["vertices"],
                y=subset["mediana_us"],
                name=label,
                mode="lines+markers",
                line={"color": QUEUE_COLORS[queue], "width": 2.4},
                marker={"size": 8, "symbol": {"binary_heap": "circle", "4ary_heap": "square", "fibonacci_heap": "triangle-up"}[queue]},
                error_y={
                    "type": "data",
                    "symmetric": False,
                    "array": subset["q3_us"] - subset["mediana_us"],
                    "arrayminus": subset["mediana_us"] - subset["q1_us"],
                    "thickness": 1.2,
                },
                hovertemplate="V=%{x}<br>mediana=%{y:.1f} µs<extra>%{fullData.name}</extra>",
            )
        )
    figure.update_layout(
        title="Pregunta: ¿qué cola minimiza el tiempo observado?",
        xaxis_title="Vértices |V|",
        yaxis_title="Tiempo, mediana (µs)",
        xaxis_type="log",
        yaxis_type="log",
        template="plotly_white",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        legend={"orientation": "h", "y": 1.12, "x": 0},
        margin={"l": 55, "r": 20, "t": 95, "b": 55},
        height=470,
    )
    x_values = sorted(int(value) for value in frame["vertices"].unique())
    y_min = float(frame["q1_us"].min())
    y_max = float(frame["q3_us"].max())
    y_ticks = [
        10 ** exponent
        for exponent in range(math.floor(math.log10(y_min)), math.ceil(math.log10(y_max)) + 1)
    ]
    figure.update_xaxes(
        showgrid=True,
        gridcolor="#E8E0D2",
        tickvals=x_values,
        ticktext=[f"{value:,}" for value in x_values],
    )
    figure.update_yaxes(
        showgrid=True,
        gridcolor="#E8E0D2",
        tickvals=y_ticks,
        ticktext=[f"{value:,.0f}" for value in y_ticks],
    )
    return figure


def route_figure(instance, path: List[Hashable]) -> go.Figure:
    edge_lon: List[Any] = []
    edge_lat: List[Any] = []
    for u in instance.nodes:
        if u not in instance.coords:
            continue
        for v, _weight in instance.adj.get(u, []):
            if v not in instance.coords:
                continue
            edge_lon.extend([instance.coords[u][0], instance.coords[v][0], None])
            edge_lat.extend([instance.coords[u][1], instance.coords[v][1], None])
    route_lon = [instance.coords[node][0] for node in path]
    route_lat = [instance.coords[node][1] for node in path]
    figure = go.Figure()
    figure.add_trace(
        go.Scattergl(
            x=edge_lon,
            y=edge_lat,
            mode="lines",
            line={"color": "#C8C0B3", "width": 1},
            hoverinfo="skip",
            name="Red OSM",
        )
    )
    figure.add_trace(
        go.Scattergl(
            x=route_lon,
            y=route_lat,
            mode="lines+markers",
            line={"color": "#681C32", "width": 4},
            marker={"color": "#8A6418", "size": 7},
            text=[str(node) for node in path],
            hovertemplate="Nodo %{text}<extra>Ruta</extra>",
            name="Ruta mínima",
        )
    )
    if path:
        figure.add_trace(
            go.Scattergl(
                x=[route_lon[0], route_lon[-1]],
                y=[route_lat[0], route_lat[-1]],
                mode="markers+text",
                marker={"color": ["#2F6B3F", "#681C32"], "size": 13},
                text=["Origen", "Destino"],
                textposition=["top right", "bottom right"],
                hoverinfo="skip",
                name="Extremos",
            )
        )
    figure.update_layout(
        title="Ruta sobre la topología vial congelada",
        xaxis_title="Longitud",
        yaxis_title="Latitud",
        template="plotly_white",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        showlegend=True,
        height=560,
        margin={"l": 50, "r": 20, "t": 60, "b": 45},
    )
    figure.update_yaxes(scaleanchor="x", scaleratio=1)
    return figure


def show_header(title: str, subtitle: str) -> None:
    st.title(title)
    st.markdown(subtitle)


def comparison_view() -> None:
    show_header(
        "Comparación experimental",
        "Mismo Dijkstra, mismos grafos y tres colas de prioridad. La mediana es la medida principal; el IQR expresa dispersión.",
    )
    if not BENCHMARK_PATH.exists():
        st.info("No hay resultados todavía. Ejecute el benchmark canónico para llenar esta vista.")
        return
    try:
        with st.spinner("Cargando resultados verificados..."):
            results = load_json(str(BENCHMARK_PATH), file_version(BENCHMARK_PATH))
    except (OSError, ValueError, KeyError) as exc:
        st.error(f"No se pudo leer el benchmark: {exc}")
        st.caption("Revise el JSON y vuelva a ejecutar el protocolo experimental.")
        return

    profile_label = st.radio(
        "Perfil del grafo",
        options=["sparse", "dense"],
        format_func=lambda value: "Disperso, E = 4V" if value == "sparse" else "Denso, E = 0.08V(V-1)",
        horizontal=True,
    )
    frame = benchmark_frame(results, profile_label)
    if frame.empty:
        st.info("Este perfil no contiene mediciones. Ejecute el benchmark con escalas no vacías.")
        return

    counts = results["profiles"][profile_label]["winner_counts"]
    winner = max(counts, key=counts.get)
    total = sum(counts.values())
    c1, c2, c3 = st.columns(3)
    c1.metric("Más primeros lugares", QUEUE_SHORT_LABELS[winner])
    c2.metric("Escalas ganadas", f"{counts[winner]} de {total}")
    c3.metric("Muestras por punto", str(int(frame["sample_count"].iloc[0])))

    st.plotly_chart(benchmark_figure(frame, profile_label), width="stretch")
    display = frame.rename(
        columns={
            "estructura": "Estructura",
            "vertices": "|V|",
            "aristas": "|E|",
            "mediana_us": "Mediana (µs)",
            "q1_us": "Q1 (µs)",
            "q3_us": "Q3 (µs)",
            "speedup_binary": "Speedup vs. Binary",
        }
    )[["Estructura", "|V|", "|E|", "Mediana (µs)", "Q1 (µs)", "Q3 (µs)", "Speedup vs. Binary"]]
    st.dataframe(display, hide_index=True, width="stretch")
    st.markdown(
        '<p class="evidence-note">Lectura válida: 4-ary presenta la menor mediana en la mayoría de las escalas sintéticas. '
        "Los intervalos se solapan en varios tamaños; no se afirma una victoria universal.</p>",
        unsafe_allow_html=True,
    )


def route_view() -> None:
    show_header(
        "Consulta sobre la red OSM",
        "La red es un snapshot local de OpenStreetMap. La vista funciona sin conexión y conserva su procedencia.",
    )
    if not OSM_PATH.exists():
        st.info("No existe el snapshot OSM. Ejecute la descarga reproducible antes de calcular rutas.")
        return

    metric = st.radio(
        "Costo a minimizar",
        ["time", "distance"],
        format_func=lambda value: "Tiempo estimado" if value == "time" else "Distancia",
        horizontal=True,
    )
    try:
        with st.spinner("Cargando la red vial local..."):
            instance = load_osm(str(OSM_PATH), metric, file_version(OSM_PATH))
    except Exception as exc:
        st.error(f"No se pudo cargar la red OSM: {exc}")
        st.caption("Compruebe el snapshot o regenérelo desde OSMnx.")
        return

    applied = load_json(str(APPLIED_PATH), file_version(APPLIED_PATH)) if APPLIED_PATH.exists() else {}
    default_source = applied.get("query", {}).get("source", instance.nodes[0])
    default_target = applied.get("query", {}).get("target", instance.nodes[-1])
    options = list(instance.nodes)

    def node_label(node: Hashable) -> str:
        lon, lat = instance.coords[node]
        return f"Nodo {node}  ({lat:.5f}, {lon:.5f})"

    left, right = st.columns(2)
    source = left.selectbox(
        "Origen",
        options,
        index=options.index(default_source) if default_source in options else 0,
        format_func=node_label,
    )
    target = right.selectbox(
        "Destino",
        options,
        index=options.index(default_target) if default_target in options else len(options) - 1,
        format_func=node_label,
    )
    c1, c2 = st.columns(2)
    algorithm = c1.selectbox("Algoritmo", ["dijkstra", "astar"], format_func=lambda value: "Dijkstra" if value == "dijkstra" else "A* consistente")
    queue = c2.selectbox("Cola de prioridad", list(QUEUE_LABELS), format_func=QUEUE_LABELS.get)

    use_weather = st.checkbox(
        "Aplicar escenario meteorológico reproducible",
        value=False,
        disabled=metric != "time",
        help="El factor uniforme solo modifica el tiempo. No representa tránsito calibrado.",
    )
    observation = None
    multiplier = 1.0
    if use_weather and metric == "time":
        if WEATHER_PATH.exists():
            try:
                observation = load_weather_snapshot(WEATHER_PATH)
                multiplier = weather_multiplier(observation)
                instance = uniformly_scaled(instance, multiplier)
                st.caption(
                    f"Snapshot {observation.observed_at}; precipitación {observation.precipitation_mm:.1f} mm; "
                    f"visibilidad {observation.visibility_m:.0f} m; factor {multiplier:.4f}."
                )
            except Exception as exc:
                st.error(f"El snapshot meteorológico no es válido: {exc}")
                return
        else:
            st.info("No hay snapshot meteorológico. Use la vista Procedencia para obtenerlo.")
            return

    if not st.button("Calcular ruta", type="primary"):
        st.info("Seleccione origen, destino, algoritmo y cola. Después pulse Calcular ruta.")
        return

    try:
        with st.spinner("Calculando y reconstruyendo la ruta..."):
            if algorithm == "dijkstra":
                result = dijkstra_solver(instance.nodes, instance.adj, source, queue_type=queue, target=target)
                path = result["paths"][target]
                cost = result["distances"][target]
                expanded = result["stats"]["visited_count"]
                relaxations = result["stats"]["relax_attempts"]
            else:
                result = a_star_solver(instance.nodes, instance.adj, source, target, instance.coords, queue_type=queue)
                path = result["path"]
                cost = result["target_distance"]
                expanded = result["stats"]["expanded_nodes"]
                relaxations = result["stats"]["relax_attempts"]
    except Exception as exc:
        st.error(f"La consulta no pudo resolverse: {exc}")
        st.caption("Cambie los nodos o revise la integridad del snapshot.")
        return

    if not path or not math.isfinite(cost):
        st.info("No hay un camino dirigido entre los nodos seleccionados.")
        return
    unit = "s" if metric == "time" else "m"
    s1, s2, s3 = st.columns(3)
    s1.metric("Costo mínimo", f"{cost:.2f} {unit}")
    s2.metric("Nodos expandidos", str(expanded))
    s3.metric("Relajaciones", str(relaxations))
    st.plotly_chart(route_figure(instance, path), width="stretch")
    route_rows = [
        {"orden": index, "nodo": node, "latitud": instance.coords[node][1], "longitud": instance.coords[node][0]}
        for index, node in enumerate(path)
    ]
    st.dataframe(pd.DataFrame(route_rows), hide_index=True, width="stretch")
    st.caption("Cartografía: © OpenStreetMap contributors, ODbL 1.0. El gráfico usa el snapshot local, sin teselas externas.")


def manual_view() -> None:
    show_header(
        "Traza de la instancia manual",
        "Seis nodos y nueve aristas permiten revisar cada extracción, relajación y predecesor.",
    )
    c1, c2, c3 = st.columns(3)
    metric = c1.selectbox("Métrica", ["distance", "time"], format_func=lambda value: "Distancia" if value == "distance" else "Tiempo")
    queue = c2.selectbox("Estructura", list(QUEUE_LABELS), format_func=QUEUE_LABELS.get, key="manual_queue")
    instance = load_cusco_instance(metric)
    target = c3.selectbox("Destino", instance.nodes[1:], format_func=instance.label)
    if not st.button("Ejecutar traza"):
        st.info("Elija una configuración y pulse Ejecutar traza para ver el estado del algoritmo.")
        return
    try:
        with st.spinner("Ejecutando Dijkstra paso a paso..."):
            result = dijkstra_solver(
                instance.nodes,
                instance.adj,
                "A",
                queue_type=queue,
                record_trace=True,
            )
    except Exception as exc:
        st.error(f"No se pudo ejecutar la traza: {exc}")
        return
    path = result["paths"][target]
    unit = "m" if metric == "distance" else "s"
    m1, m2, m3 = st.columns(3)
    m1.metric("Costo hacia el destino", f"{result['distances'][target]:.2f} {unit}")
    m2.metric("Extracciones", str(result["stats"]["extract_min_ops"]))
    m3.metric("Decrease-key", str(result["stats"]["decrease_key_ops"]))
    rows = []
    for step in result["history"]:
        relaxed = [str(item["to_node"]) for item in step["relaxations"] if item["relaxed"]]
        rows.append(
            {
                "k": step["k"],
                "extraído": step["extracted"],
                "d[u]": step["dist_extracted"],
                "cerrados": ", ".join(map(str, step["permanent_set"])),
                "relajados": ", ".join(relaxed) if relaxed else "ninguno",
            }
        )
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    st.code(" -> ".join(map(str, path)), language=None)
    st.caption("Instancia ilustrativa: los nombres son reales; longitudes, pendientes y coordenadas son datos manuales de demostración.")


def provenance_view() -> None:
    show_header(
        "Método y procedencia",
        "Cada cifra de la aplicación proviene de un JSON reproducible o de una ejecución directa del mismo núcleo algorítmico.",
    )
    st.subheader("Protocolo experimental")
    if BENCHMARK_PATH.exists():
        try:
            benchmark = load_json(str(BENCHMARK_PATH), file_version(BENCHMARK_PATH))
            protocol = pd.DataFrame(
                [{"campo": key, "valor": str(value)} for key, value in benchmark.get("protocol", {}).items()]
            )
            st.dataframe(protocol, hide_index=True, width="stretch")
        except Exception as exc:
            st.error(f"No se pudo leer el protocolo: {exc}")
    else:
        st.info("No hay protocolo guardado. Ejecute el benchmark canónico.")

    st.subheader("Fuentes de datos")
    sources = pd.DataFrame(
        [
            {"dato": "Red aplicada", "fuente": "OpenStreetMap vía OSMnx", "modo offline": "snapshot JSON"},
            {"dato": "Condición meteorológica", "fuente": "Open-Meteo, datos de modelo", "modo offline": "snapshot JSON"},
            {"dato": "Perfiles sintéticos", "fuente": "generador con semilla fija", "modo offline": "determinista"},
            {"dato": "Corrección", "fuente": "NetworkX y certificado O(V+E)", "modo offline": "local"},
        ]
    )
    st.dataframe(sources, hide_index=True, width="stretch")

    st.subheader("Actualizar condición meteorológica")
    st.write("La actualización es opcional. Si falla la red, el snapshot existente continúa disponible.")
    if st.button("Actualizar desde Open-Meteo"):
        try:
            with st.spinner("Consultando Open-Meteo y guardando el snapshot..."):
                observation = OpenMeteoClient().fetch_current(snapshot_path=WEATHER_PATH)
                load_json.clear()
            st.success(f"Snapshot actualizado: {observation.observed_at}.")
        except Exception as exc:
            st.error(f"No se pudo actualizar: {exc}")
            st.caption("No se eliminó el snapshot local disponible.")
    if WEATHER_PATH.exists():
        try:
            observation = load_weather_snapshot(WEATHER_PATH)
            st.caption(
                f"Snapshot disponible: {observation.observed_at}; fuente declarada: {observation.source}."
            )
        except Exception as exc:
            st.error(f"El snapshot local no se puede leer: {exc}")

    st.markdown(
        '<p class="evidence-note">Limitación: el clima se aplica como análisis uniforme de sensibilidad. '
        "No estima congestión, incidentes ni velocidad observada por tramo.</p>",
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(
        page_title="Rutas mínimas UNSAAC",
        page_icon=None,
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    apply_styles()
    st.markdown(
        '<div class="institution-line"><strong>UNSAAC · Grupo 5</strong>'
        "<span>Rutas mínimas y colas de prioridad</span></div>",
        unsafe_allow_html=True,
    )
    page = st.radio(
        "Sección de la aplicación",
        ["Comparación", "Ruta OSM", "Traza manual", "Procedencia"],
        horizontal=True,
        label_visibility="collapsed",
    )
    {
        "Comparación": comparison_view,
        "Ruta OSM": route_view,
        "Traza manual": manual_view,
        "Procedencia": provenance_view,
    }[page]()


if __name__ == "__main__":
    main()
