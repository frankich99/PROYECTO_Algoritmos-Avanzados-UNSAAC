"""Interfaz docente para rutas OSM y comparación de colas de prioridad.

Los cálculos interactivos no reemplazan el benchmark ni el caso canónico.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Hashable

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.algorithms.a_star import a_star_solver
from src.algorithms.dijkstra import dijkstra_solver
from src.benchmarks.applied_analysis import nearest_node, uniformly_scaled
from src.io.osm_loader import load_snapshot as load_osm_snapshot
from src.models.cusco_network import load_cusco_instance
from src.services.traffic import (
    TomTomTrafficClient,
    calculate_traffic_multiplier,
    get_traffic_by_schedule,
)
from src.services.weather import (
    OpenMeteoClient,
    OpenWeatherMapClient,
    WeatherObservation,
    WeatherServiceError,
    load_snapshot as load_weather_snapshot,
    weather_multiplier,
)
from src.verification.certificate import verify_shortest_paths

DATA_DIR = Path(__file__).resolve().parent / "data" / "processed"
OSM_PATH = DATA_DIR / "cusco_osm_drive.json"
BENCHMARK_PATH = DATA_DIR / "benchmark_results.json"
APPLIED_PATH = DATA_DIR / "applied_results.json"
WEATHER_PATH = DATA_DIR / "weather_cusco.json"

QUEUES = {
    "binary_heap": "Heap binario",
    "4ary_heap": "Heap 4-ario",
    "fibonacci_heap": "Heap Fibonacci",
}
QUEUE_COLORS = {
    "binary_heap": "#681C32",
    "4ary_heap": "#8A6418",
    "fibonacci_heap": "#315D65",
}


def apply_styles() -> None:
    st.markdown(
        """
        <style>
        :root { --granate: #681C32; --dorado: #8A6418; --tinta: #1F1B1C; --papel: #F7F3EA; --linea: #D9C9B6; }
        header[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
        #MainMenu, footer { display: none !important; }
        .stApp { background: var(--papel); color: var(--tinta); }
        .block-container { max-width: 1240px; padding-top: 1.25rem; padding-bottom: 3.5rem; }
        .institution-line { display: flex; align-items: center; justify-content: space-between;
            flex-wrap: wrap; gap: .5rem 1.5rem; background: var(--granate); color: #fff;
            padding: 1rem 1.45rem; border-bottom: 3px solid var(--dorado); }
        .institution-line strong { font-family: Georgia, 'Times New Roman', serif; font-size: 1.25rem; font-weight: 700; }
        .institution-line span { font-size: .9rem; color: #F5E9E6; }
        .stApp h1, .stApp h2, .stApp h3 { font-family: Georgia, 'Times New Roman', serif !important; color: #341E25; }
        .stApp h1 { letter-spacing: -.025em; font-size: 2.8rem; }
        .stApp h2 { font-size: 2rem; }
        .st-key-main_nav { border-bottom: 1px solid var(--linea); margin-bottom: 1.4rem; }
        .st-key-main_nav [role="radiogroup"] { flex-wrap: wrap; gap: .25rem .5rem; }
        .st-key-main_nav [data-testid="stRadioOption"] {
            padding: .7rem .8rem; border-bottom: 3px solid transparent; min-height: 44px;
        }
        .st-key-main_nav [data-testid="stRadioOption"] > div > div:first-child { display: none; }
        .st-key-main_nav [role="radiogroup"] > div:nth-child(-n+2) [data-testid="stRadioOption"] { font-weight: 700; }
        .st-key-main_nav [data-testid="stRadioOption"][data-selected="true"] {
            border-bottom-color: var(--granate); background: #EFE4DB; color: var(--granate);
        }
        .st-key-main_nav [data-testid="stRadioOption"]:has(input:focus-visible) {
            outline: 3px solid var(--dorado); outline-offset: -3px;
        }
        .stApp [data-testid="stForm"] { border: 1px solid var(--linea); background: #fff; border-radius: 6px; }
        .stApp [data-testid="stCaptionContainer"] { opacity: 1 !important; }
        .stApp [data-testid="stCaptionContainer"] p { color: #55494F !important; }
        [data-testid="stMetric"] { border-top: 2px solid var(--granate); padding-top: .5rem; }
        [data-testid="stMetricValue"] { color: var(--granate); font-variant-numeric: tabular-nums; }
        .stButton button[kind="primary"], .stFormSubmitButton button[kind="primary"] {
            background: var(--granate); border-color: var(--granate); color: #fff;
        }
        .stButton button:hover, .stDownloadButton button:hover, .stFormSubmitButton button:hover {
            border-color: var(--dorado); }
        .stButton button, .stDownloadButton button, .stFormSubmitButton button,
        .stRadio label, .stCheckbox label, .stSelectbox [role="combobox"] {
            min-height: 44px;
        }
        .stSelectbox button[aria-label="Open"], .stMultiSelect button[aria-label="Open"],
        [data-testid="stTooltipHoverTarget"] button { min-width: 44px; min-height: 44px; }
        button:focus-visible, input:focus-visible, [role="radio"]:focus-visible,
        [role="combobox"]:focus-visible, a:focus-visible {
            outline: 3px solid var(--dorado) !important; outline-offset: 3px;
        }
        @media (max-width: 640px) {
            .block-container { padding-left: .9rem; padding-right: .9rem; padding-top: .8rem; }
            .institution-line { padding: .9rem 1rem; }
            .stApp h1 { font-size: 1.85rem !important; }
            .stApp h2 { font-size: 1.55rem !important; }
            .st-key-main_nav [data-testid="stRadioOption"] { padding: .55rem .65rem; }
            .stMultiSelect button[aria-label^="Remove"],
            .stMultiSelect button[aria-label="Clear all"] { min-width: 44px; min-height: 44px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def file_version(path: Path) -> int:
    return path.stat().st_mtime_ns if path.exists() else 0


@st.cache_data(show_spinner=False)
def load_json(path: str, modified_ns: int) -> dict[str, Any]:
    del modified_ns
    return json.loads(Path(path).read_text(encoding="utf-8"))


@st.cache_resource(show_spinner=False)
def load_osm(path: str, metric: str, modified_ns: int):
    del modified_ns
    return load_osm_snapshot(path, metric=metric)


def benchmark_frame(results: dict[str, Any], profile: str) -> pd.DataFrame:
    data = results.get("profiles", {}).get(profile, {}).get("data", {})
    rows = []
    for queue in QUEUES:
        for item in data.get(queue, []):
            rows.append({
                "cola": queue,
                "estructura": QUEUES[queue],
                "vertices": item["nodes"],
                "aristas": item["edges"],
                "mediana_us": item["median_us"],
                "q1_us": item["q1_us"],
                "q3_us": item["q3_us"],
                "sample_count": item.get("sample_count", 0),
            })
    frame = pd.DataFrame(rows)
    if not frame.empty:
        reference = frame.loc[frame["cola"] == "binary_heap"].set_index("vertices")["mediana_us"]
        frame["ratio_vs_binary"] = frame["vertices"].map(reference) / frame["mediana_us"]
    return frame


def validate_benchmark_upload(content: bytes) -> dict[str, Any]:
    """Admite el esquema de resultados existente, sin modificar datos canónicos."""
    if len(content) > 5_000_000:
        raise ValueError("El archivo supera 5 MB.")
    try:
        payload = json.loads(content.decode("utf-8"))
        profiles = payload["profiles"]
        if not isinstance(profiles, dict) or not profiles:
            raise ValueError("No hay perfiles.")
        for profile, group in profiles.items():
            if not isinstance(profile, str) or not isinstance(group, dict):
                raise ValueError("Perfil inválido.")
            data = group["data"]
            if not isinstance(data, dict) or set(data) != set(QUEUES):
                raise ValueError("Cada perfil requiere las tres colas.")
            scales = None
            edges_per_scale = None
            for queue in QUEUES:
                items = data[queue]
                if not isinstance(items, list) or not 1 <= len(items) <= 100:
                    raise ValueError("Cada cola requiere entre 1 y 100 escalas.")
                seen = set()
                edges = {}
                for item in items:
                    n, e, count = item["nodes"], item["edges"], item["sample_count"]
                    if any(type(value) is not int for value in (n, e, count)) or n <= 0 or e < 0 or count <= 0:
                        raise ValueError("Tamaño o cantidad de muestras inválidos.")
                    q1, median, q3 = (float(item[field]) for field in ("q1_us", "median_us", "q3_us"))
                    if not all(map(math.isfinite, (q1, median, q3))) or not 0 < q1 <= median <= q3:
                        raise ValueError("Cuartiles inválidos.")
                    item["q1_us"], item["median_us"], item["q3_us"] = q1, median, q3
                    seen.add(n)
                    edges[n] = e
                if len(seen) != len(items) or (scales is not None and seen != scales):
                    raise ValueError("Las colas deben compartir escalas sin duplicados.")
                if edges_per_scale is not None and edges != edges_per_scale:
                    raise ValueError("Las colas deben declarar el mismo número de aristas por escala.")
                scales = seen
                edges_per_scale = edges
        return payload
    except (UnicodeError, json.JSONDecodeError, KeyError, TypeError, OverflowError) as exc:
        raise ValueError("JSON de benchmark inválido: consulte el esquema del archivo canónico.") from exc


def benchmark_figure(frame: pd.DataFrame, profile: str) -> go.Figure:
    figure = go.Figure()
    for queue, label in QUEUES.items():
        subset = frame[frame["cola"] == queue].sort_values("vertices")
        if subset.empty:
            continue
        figure.add_trace(go.Scatter(
            x=subset["vertices"], y=subset["mediana_us"], name=label.removeprefix("Heap ").capitalize(),
            mode="lines+markers", line={"color": QUEUE_COLORS[queue], "width": 2.5},
            marker={"size": 9, "symbol": {"binary_heap": "circle", "4ary_heap": "square",
                                             "fibonacci_heap": "diamond"}[queue]},
            error_y={"type": "data", "symmetric": False,
                     "array": subset["q3_us"] - subset["mediana_us"],
                     "arrayminus": subset["mediana_us"] - subset["q1_us"]},
            hovertemplate="Vértices: %{x}<br>Mediana: %{y:.1f} µs<extra>%{fullData.name}</extra>",
        ))
    figure.update_layout(
        template="plotly_white", paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
        xaxis_title="Vértices (escala log)", yaxis_title="Mediana e IQR (µs, escala log)",
        xaxis_type="log", yaxis_type="log", height=440,
        legend={"orientation": "h", "y": 1.15, "x": 0, "font": {"size": 11}},
        margin={"l": 52, "r": 12, "t": 65, "b": 55},
    )
    figure.update_xaxes(tickvals=sorted(frame["vertices"].unique()), showgrid=True, gridcolor="#E9DDD0")
    ticks = [10**power for power in range(math.floor(math.log10(frame["q1_us"].min())),
                                          math.ceil(math.log10(frame["q3_us"].max())) + 1)]
    figure.update_yaxes(tickvals=ticks, ticktext=[f"{tick:,.0f}" for tick in ticks],
                        showgrid=True, gridcolor="#E9DDD0")
    return figure


def route_figure(instance, path: list[Hashable], *, basemap: bool = False) -> go.Figure:
    """Dibuja la red local; solo el mapa base descarga teselas externas."""
    edge_lon, edge_lat = [], []
    for u in instance.nodes:
        if u not in instance.coords:
            continue
        for v, _ in instance.adj.get(u, []):
            if v in instance.coords:
                edge_lon.extend([instance.coords[u][0], instance.coords[v][0], None])
                edge_lat.extend([instance.coords[u][1], instance.coords[v][1], None])
    route_lon = [instance.coords[n][0] for n in path] if path else []
    route_lat = [instance.coords[n][1] for n in path] if path else []
    figure = go.Figure()
    if basemap:
        figure.add_trace(go.Scattermap(
            lat=edge_lat, lon=edge_lon, mode="lines", line={"color": "#837E7B", "width": 1.3},
            hoverinfo="skip", name="Red vial OSM",
        ))
        figure.add_trace(go.Scattermap(
            lat=route_lat, lon=route_lon, mode="lines+markers",
            line={"color": "#681C32", "width": 5}, marker={"color": "#681C32", "size": 9},
            text=[str(n) for n in path], hovertemplate="Nodo %{text}<extra>Ruta</extra>", name="Ruta mínima",
        ))
        figure.add_trace(go.Scattermap(
            lat=[route_lat[0], route_lat[-1]] if path else [],
            lon=[route_lon[0], route_lon[-1]] if path else [], mode="markers",
            marker={"color": "#8A6418", "size": 16},
            text=["Origen", "Destino"] if path else [], hoverinfo="text", name="Extremos", showlegend=False,
        ))
        center = instance.coords[path[len(path) // 2]] if path else (-71.9788, -13.5165)
        figure.update_layout(map={"style": "open-street-map", "center": {"lon": center[0], "lat": center[1]}, "zoom": 14})
    else:
        figure.add_trace(go.Scattergl(
            x=edge_lon, y=edge_lat, mode="lines", line={"color": "#CABEB0", "width": 1},
            hoverinfo="skip", name="Red vial OSM",
        ))
        figure.add_trace(go.Scattergl(
            x=route_lon, y=route_lat, mode="lines+markers", line={"color": "#681C32", "width": 4},
            marker={"color": "#681C32", "size": 8},
            text=[str(n) for n in path], hovertemplate="Nodo %{text}<extra>Ruta</extra>", name="Ruta mínima",
        ))
        figure.add_trace(go.Scattergl(
            x=[route_lon[0], route_lon[-1]] if path else [],
            y=[route_lat[0], route_lat[-1]] if path else [], mode="markers+text",
            marker={"color": "#8A6418", "size": 12}, text=["Origen", "Destino"] if path else [],
            textposition=["top left", "bottom right"] if path else None,
            hoverinfo="skip", name="Extremos", showlegend=False,
        ))
        figure.update_xaxes(title="Longitud", showgrid=False, zeroline=False)
        figure.update_yaxes(title="Latitud", showgrid=False, zeroline=False, scaleanchor="x", scaleratio=1)
    figure.update_layout(
        template="plotly_white", paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
        showlegend=True, legend={"orientation": "h", "y": 1.06, "font": {"size": 11}},
        height=500, margin={"l": 45 if not basemap else 0, "r": 12, "t": 40, "b": 25 if not basemap else 0},
    )
    return figure


def solve_route(instance, source: Hashable, target: Hashable, algorithm: str, queue: str) -> dict[str, Any]:
    if algorithm == "dijkstra":
        result = dijkstra_solver(instance.nodes, instance.adj, source, queue_type=queue, target=target)
        return {
            "algoritmo": "Dijkstra", "cola": QUEUES[queue], "costo": result["distances"][target],
            "ruta": result["paths"].get(target, []), "expandidos": result["stats"]["visited_count"],
            "relajaciones": result["stats"]["relax_attempts"],
            "decrementos": result["stats"].get("decrease_key_ops", 0),
        }
    if algorithm == "astar":
        result = a_star_solver(instance.nodes, instance.adj, source, target, instance.coords, queue_type=queue)
        return {
            "algoritmo": "A*", "cola": QUEUES[queue], "costo": result["target_distance"],
            "ruta": result["path"], "expandidos": result["stats"]["expanded_nodes"],
            "relajaciones": result["stats"]["relax_attempts"],
            "decrementos": result["stats"].get("decrease_key_ops", 0),
        }
    raise ValueError("Algoritmo no admitido.")


def compare_route(instance, source: Hashable, target: Hashable) -> list[dict[str, Any]]:
    rows = [solve_route(instance, source, target, "dijkstra", queue) for queue in QUEUES]
    costs = [row["costo"] for row in rows]
    if any(not math.isclose(costs[0], cost, rel_tol=1e-9, abs_tol=1e-6) for cost in costs[1:]):
        raise ValueError("Las colas no coinciden en el costo. No se presenta comparación.")
    return rows


def route_view() -> None:
    st.header("Ruta vial de Cusco")
    st.write("Resuelva una consulta sobre la red OSM guardada y contraste las estructuras con los mismos nodos y pesos.")
    if not OSM_PATH.exists():
        st.info("Sin red local: falta data/processed/cusco_osm_drive.json. No se descarga automáticamente.")
        return
    metric = st.radio("Costo de la ruta", ["time", "distance"], horizontal=True,
                      format_func=lambda m: "Tiempo nominal (s)" if m == "time" else "Distancia (m)")
    try:
        with st.spinner("Cargando red local..."):
            instance = load_osm(str(OSM_PATH), metric, file_version(OSM_PATH))
            applied = load_json(str(APPLIED_PATH), file_version(APPLIED_PATH)) if APPLIED_PATH.exists() else {}
    except (ValueError, OSError, KeyError, TypeError) as exc:
        st.error(f"No se pudo cargar la red: {exc}")
        return
    if not instance.nodes:
        st.info("La red no contiene nodos para consultar.")
        return
    st.caption(f"Red dirigida local · {len(instance.nodes):,} vértices · "
               f"{sum(len(edges) for edges in instance.adj.values()):,} aristas · sin descarga automática")

    presets = {
        "Centro a zona universitaria (puntos aproximados)": (
            nearest_node(instance, -71.9788, -13.5165), nearest_node(instance, -71.9590, -13.5220)),
        "San Pedro a Regocijo (puntos aproximados)": (
            nearest_node(instance, -71.9830, -13.5200), nearest_node(instance, -71.9800, -13.5170)),
    }
    canonical = applied.get("query", {})
    if canonical.get("source") in instance.adj and canonical.get("target") in instance.adj:
        presets = {"Consulta del informe": (canonical["source"], canonical["target"]), **presets}
    preset = st.selectbox("Recorrido", [*presets, "Seleccionar nodos"], key="route_preset")
    default_source, default_target = presets.get(preset, (None, None))
    if default_source not in instance.adj or default_target not in instance.adj:
        default_source, default_target = instance.nodes[0], instance.nodes[-1]

    with st.form("route_form"):
        if preset == "Seleccionar nodos":
            left, right = st.columns(2)
            def node_label(node: Hashable) -> str:
                lon, lat = instance.coords[node]
                return f"{node}  ·  {lat:.5f}, {lon:.5f}"

            source = left.selectbox("Origen (ID OSM)", instance.nodes, key="route_source", format_func=node_label)
            target = right.selectbox("Destino (ID OSM)", instance.nodes, index=len(instance.nodes) - 1,
                                     key="route_target", format_func=node_label)
        else:
            source, target = default_source, default_target
            st.caption(f"Origen {source} · Destino {target}. Los puntos aproximados se ajustan al nodo vial más próximo.")
        left, right = st.columns(2)
        algorithm = left.selectbox("Algoritmo", ["dijkstra", "astar"],
                                   format_func=lambda x: "Dijkstra" if x == "dijkstra" else "A* (heurística consistente)")
        queue = right.selectbox("Cola", list(QUEUES), format_func=QUEUES.get)
        compare = st.checkbox("Contrastar tres colas de Dijkstra y A* en esta consulta")

        weather_choice = "Sin clima"
        use_traffic = False
        hour = 13
        if metric == "time":
            with st.expander("Escenarios opcionales (factores uniformes, no tráfico medido)"):
                options = ["Sin clima"]
                if applied.get("weather_sensitivity", {}).get("observation"):
                    options.append("Observación histórica del informe")
                if WEATHER_PATH.exists():
                    options.append("Snapshot local posterior")
                if "weather_query" in st.session_state:
                    options.append("Consulta temporal de esta sesión")
                weather_choice = st.selectbox("Fuente del escenario meteorológico", options)
                use_traffic = st.checkbox("Aplicar supuesto de congestión por horario")
                hour = st.slider("Hora local simulada (Cusco)", 0, 23, 13,
                                 help="Solo se usa si marca congestión hipotética; no es un aforo.")
                st.caption("Clima histórico y snapshot local son fechas y fuentes distintas. "
                           "El factor se aplica a toda la red; no cambia la ruta óptima.")
        submitted = st.form_submit_button("Calcular ruta", type="primary")

    weather_version = file_version(WEATHER_PATH) if weather_choice == "Snapshot local posterior" else 0
    live_obs = st.session_state.get("weather_query") if weather_choice == "Consulta temporal de esta sesión" else None
    signature = (file_version(OSM_PATH), metric, preset, source, target, algorithm, queue,
                 compare, weather_choice, use_traffic, hour, weather_version, live_obs)
    preview = (not submitted and "route_result" not in st.session_state and preset == "Consulta del informe"
               and metric == "time" and weather_choice == "Sin clima" and not use_traffic)
    if submitted or preview:
        try:
            if source == target:
                raise ValueError("Seleccione nodos distintos para esta consulta.")
            weather_factor = 1.0
            provenance = "Pesos OSM nominales"
            if weather_choice == "Observación histórica del informe":
                obs = WeatherObservation.from_dict(applied["weather_sensitivity"]["observation"])
                weather_factor, provenance = weather_multiplier(obs), f"Open-Meteo histórico · {obs.observed_at}"
            elif weather_choice == "Snapshot local posterior":
                obs = load_weather_snapshot(WEATHER_PATH)
                weather_factor, provenance = weather_multiplier(obs), f"Snapshot {obs.source} · {obs.observed_at}"
            elif live_obs is not None:
                weather_factor, provenance = weather_multiplier(live_obs), f"Consulta temporal {live_obs.source} · {live_obs.observed_at}"
            traffic_factor = (calculate_traffic_multiplier(
                get_traffic_by_schedule(hour), street_type="avenida", weather_multiplier=weather_factor,
            ) if use_traffic else 1.0)
            factor = round(weather_factor * traffic_factor, 4)
            with st.spinner("Calculando camino mínimo..."):
                network = uniformly_scaled(instance, factor) if factor != 1.0 else instance
                route = solve_route(network, source, target, algorithm, queue)
                comparisons = compare_route(network, source, target) if compare else []
                if compare:
                    astar = solve_route(network, source, target, "astar", queue)
                    if not math.isclose(comparisons[0]["costo"], astar["costo"], rel_tol=1e-9, abs_tol=1e-6):
                        raise ValueError("Dijkstra y A* discrepan: revise la heurística y los pesos.")
                    comparisons.append(astar)
            st.session_state["route_result"] = (signature, route, comparisons, factor,
                                                   weather_factor, traffic_factor, provenance)
        except (ValueError, KeyError, OSError, WeatherServiceError) as exc:
            st.session_state.pop("route_result", None)
            st.error(f"No se pudo calcular la ruta: {exc}")

    saved = st.session_state.get("route_result")
    if not saved or saved[0] != signature:
        st.info("Pulse «Calcular ruta» para ver esta selección; los resultados anteriores no se reutilizan con otros parámetros.")
        return
    _, route, comparisons, factor, weather_factor, traffic_factor, provenance = saved
    if not route["ruta"] or not math.isfinite(route["costo"]):
        st.warning("No existe un camino dirigido entre los nodos elegidos.")
        return
    unit = "s" if metric == "time" else "m"
    st.subheader("Resultado de la consulta")
    c1, c2, c3 = st.columns(3)
    c1.metric("Costo mínimo estimado" if metric == "time" else "Distancia mínima",
              f"{route['costo']:,.2f} {unit}")
    c2.metric("Vértices de la ruta", len(route["ruta"]))
    c3.metric("Vértices expandidos", route["expandidos"])
    if factor != 1:
        st.warning(f"Escenario uniforme {factor:.4f}× (clima {weather_factor:.4f}×; "
                   f"tráfico supuesto {traffic_factor:.4f}×). No son tiempos de viaje medidos.")
        st.caption(f"Fuente del clima: {provenance}. El factor modifica el costo, no el orden óptimo de rutas.")
        if use_traffic:
            st.caption(f"Tráfico por horario supuesto: {hour}:00 (hora simulada de Cusco), "
                       "misma clase 'avenida' en toda la red. La consulta puntual TomTom no se aplica aquí.")
    else:
        st.caption("Peso OSM nominal: tiempo inferido por OSMnx y velocidades disponibles o supuestas; "
                   "distancia según la longitud del tramo. No incorpora tráfico real ni pendiente.")
    map_view = st.radio("Visualización de la ruta", ["Plano local (sin conexión)", "Mapa base (requiere Internet)"],
                        horizontal=True)
    st.plotly_chart(route_figure(instance, route["ruta"], basemap=map_view.startswith("Mapa base")), width="stretch")
    st.caption("Geometría © OpenStreetMap contributors (ODbL). El plano no descarga teselas; "
               "el mapa base sí necesita conexión. Ambos calculan desde el mismo JSON local.")
    if comparisons:
        st.subheader("Misma consulta, cuatro ejecuciones")
        st.dataframe(pd.DataFrame([{"Algoritmo": r["algoritmo"], "Cola": r["cola"], f"Costo ({unit})": round(r["costo"], 3),
                                     "Expandidos": r["expandidos"], "Relajaciones": r["relajaciones"],
                                     "Decrease-key": r["decrementos"]} for r in comparisons]),
                      hide_index=True, width="stretch")
        st.caption("Tres colas de Dijkstra y A* con la cola seleccionada: se contrasta costo, no velocidad. "
                   "Para tiempos medidos use «Comparación».")
    with st.expander("Secuencia de nodos y descarga CSV"):
        frame = pd.DataFrame([{"orden": index, "id_osm": node,
                              "latitud": instance.coords[node][1], "longitud": instance.coords[node][0]}
                             for index, node in enumerate(route["ruta"], 1)])
        st.dataframe(frame, hide_index=True, width="stretch")
        st.download_button("Descargar secuencia CSV", frame.to_csv(index=False).encode("utf-8"),
                           "ruta_cusco.csv", "text/csv")


def comparison_view() -> None:
    st.header("Comparación de colas")
    st.write("El benchmark canónico ejecutó Dijkstra sobre las mismas instancias en cada cola. "
             "Compare medianas y dispersión sin confundir la ruta interactiva con un ensayo de rendimiento.")
    with st.expander("Usar otro benchmark JSON (sin sobrescribir el original)"):
        uploaded = st.file_uploader("Archivo con el esquema de benchmark_results.json", type="json")
        st.caption("Se lee solo en esta sesión; no altera las mediciones del informe.")
    if not uploaded and not BENCHMARK_PATH.exists():
        st.info("Sin datos: falta data/processed/benchmark_results.json. Cargue un benchmark JSON para comparar.")
        return
    try:
        results = (validate_benchmark_upload(uploaded.getvalue()) if uploaded else
                   load_json(str(BENCHMARK_PATH), file_version(BENCHMARK_PATH)))
        profiles = list(results["profiles"])
    except (ValueError, KeyError, OSError, TypeError) as exc:
        st.error(f"No se puede usar el benchmark: {exc}")
        return
    if not profiles:
        st.info("El archivo no contiene perfiles para comparar.")
        return
    origin = uploaded.name if uploaded else "benchmark_results.json · mediciones canónicas"
    st.caption(f"Fuente: {origin}. Fecha de generación declarada: {results.get('generated_at_utc', 'no indicada')}.")
    if uploaded:
        st.warning("JSON temporal: se validan estructura, escalas, aristas y cuartiles, pero no se puede "
                   "acreditar aquí que sus tres colas usaran las mismas instancias ni su protocolo de medición.")
    profile = st.selectbox("Topología", profiles, format_func=lambda x: {
        "sparse": "Grafo disperso (sintético)", "dense": "Grafo denso (sintético)"}.get(x, x))
    try:
        frame = benchmark_frame(results, profile)
        sizes = sorted(frame["vertices"].unique().tolist())
        chosen = st.multiselect("Escalas (vértices)", sizes, default=sizes)
        frame = frame[frame["vertices"].isin(chosen)].copy()
    except (KeyError, TypeError, ValueError) as exc:
        st.error(f"No se pudo interpretar el perfil: {exc}")
        return
    if frame.empty:
        st.info("Seleccione al menos una escala para ver la comparación.")
        return
    sample_counts = frame["sample_count"].unique()
    st.caption("Las barras indican Q1 a Q3, no intervalos de confianza. Muestras por celda: "
               + ", ".join(str(n) for n in sorted(sample_counts)) + ".")
    winners = frame.loc[frame.groupby("vertices")["mediana_us"].idxmin()]
    counts = winners["estructura"].value_counts()
    st.write("**Menor mediana por escala seleccionada:** " + "; ".join(
        f"{name}: {count}" for name, count in counts.items()) + ". El solapamiento de cuartiles no prueba superioridad estadística.")
    st.subheader("¿Cómo cambia el tiempo al crecer el grafo?")
    st.plotly_chart(benchmark_figure(frame, profile), width="stretch")
    table = frame.rename(columns={"estructura": "Cola", "vertices": "Vértices", "aristas": "Aristas",
                                    "mediana_us": "Mediana (µs)", "q1_us": "Q1 (µs)", "q3_us": "Q3 (µs)",
                                    "sample_count": "Muestras", "ratio_vs_binary": "Relación vs binario"})
    table["Relación vs binario"] = table["Relación vs binario"].round(3)
    table = table[["Cola", "Vértices", "Aristas", "Mediana (µs)", "Q1 (µs)", "Q3 (µs)",
                   "Muestras", "Relación vs binario"]]
    st.dataframe(table, hide_index=True, width="stretch")
    st.caption("Relación = mediana binaria / mediana de la cola en la misma escala. "
               "Valores superiores a 1 favorecen a la cola comparada; no son pruebas de significación.")
    st.download_button("Descargar tabla filtrada CSV", table.to_csv(index=False).encode("utf-8"),
                       "comparacion_filtrada.csv", "text/csv")
    if not uploaded and APPLIED_PATH.exists():
        with st.expander("Caso OSM del informe (medición separada)"):
            try:
                applied = load_json(str(APPLIED_PATH), file_version(APPLIED_PATH))
                timings = applied["queues"]["timings"]
                st.dataframe(pd.DataFrame([{"Cola": QUEUES[q], "Mediana (µs)": v["median_us"],
                                            "Q1 (µs)": v["q1_us"], "Q3 (µs)": v["q3_us"],
                                            "Muestras": v["sample_count"]} for q, v in timings.items()]),
                             hide_index=True, width="stretch")
                st.caption("Fuente: applied_results.json. Una consulta OSM; no mezclar con los grafos sintéticos.")
            except (KeyError, OSError, ValueError, TypeError) as exc:
                st.error(f"No se pudo leer el caso OSM: {exc}")


def weather_panel() -> None:
    st.header("Clima y tráfico: datos frente a supuestos")
    st.write("Explore las dos observaciones sin mezclarlas. Ninguna API modifica por sí sola los costos por arista OSM.")
    if APPLIED_PATH.exists():
        try:
            applied = load_json(str(APPLIED_PATH), file_version(APPLIED_PATH))
            historic = applied["weather_sensitivity"]
            original = WeatherObservation.from_dict(historic["observation"])
            st.subheader("Observación utilizada en el informe")
            st.write(f"Open-Meteo (dato de modelo) · lectura {original.observed_at} (hora de Lima) · "
                     f"precipitación {original.precipitation_mm:.1f} mm · visibilidad {original.visibility_m:,.0f} m · "
                     f"ráfaga {original.wind_gusts_kmh:.1f} km/h")
            st.caption(f"Factor histórico {historic['multiplier']:.4f}× y tiempo de escenario "
                       f"{historic['adjusted_time_sec']:.2f} s. Humedad no registrada: 50 % es valor de reserva; "
                       "presión sin dato. No es un tiempo de viaje observado.")
        except (ValueError, OSError, KeyError, TypeError, WeatherServiceError) as exc:
            st.error(f"No se pudo leer el caso meteorológico del informe: {exc}")
    st.subheader("Archivo local posterior")
    if WEATHER_PATH.exists():
        try:
            payload = load_json(str(WEATHER_PATH), file_version(WEATHER_PATH))
            obs = load_weather_snapshot(WEATHER_PATH)
            raw = payload.get("raw_response", {})
            current = raw.get("current", {}) if "Open-Meteo" in obs.source else raw.get("main", {})
            humid_key = "relative_humidity_2m" if "Open-Meteo" in obs.source else "humidity"
            pressure_key = "surface_pressure" if "Open-Meteo" in obs.source else "grnd_level"
            st.caption(f"Archivo local guardado {payload.get('fetched_at_utc', 'fecha no disponible')} · "
                       f"{obs.source} · lectura {obs.observed_at}. No es una estación UNSAAC.")
            st.write(f"Temperatura {obs.temperature_c:.1f} °C · Precipitación {obs.precipitation_mm:.1f} mm · "
                     f"Visibilidad {obs.visibility_m:,.0f} m · Ráfagas {obs.wind_gusts_kmh:.1f} km/h")
            st.write("Humedad: " + (f"{obs.relative_humidity_pct:.0f} %" if humid_key in current else "sin dato en la respuesta")
                     + " · Presión de suelo: " + (f"{obs.surface_pressure_hpa:.0f} hPa" if pressure_key in current
                                                 and obs.surface_pressure_hpa is not None else "sin dato"))
            st.caption(f"Factor climático calculado: {weather_multiplier(obs):.4f}×, coeficientes hipotéticos; "
                       "no modifica la elección de ruta al aplicarse uniformemente.")
        except (KeyError, OSError, ValueError, WeatherServiceError, TypeError) as exc:
            st.error(f"El snapshot meteorológico no puede leerse: {exc}")
    else:
        st.info("No hay snapshot meteorológico. La ruta usa el peso nominal.")
    st.caption("Las consultas de red no sobrescriben los archivos de evaluación.")
    source = st.radio("Proveedor opcional", ["Open-Meteo", "OpenWeatherMap"], horizontal=True)
    supplied_key = st.text_input("Clave OpenWeatherMap (solo para esta consulta)", type="password",
                                  help="Introduzca una clave nueva tras rotar la anterior; no la guarde en Git.") if source == "OpenWeatherMap" else ""
    if st.button("Consultar condiciones ahora"):
        st.session_state.pop("weather_query", None)
        if source == "OpenWeatherMap" and not supplied_key.strip():
            st.error("Introduzca una clave nueva antes de consultar OpenWeatherMap.")
        else:
            try:
                with st.spinner("Consultando proveedor..."):
                    obs = (OpenMeteoClient().fetch_current() if source == "Open-Meteo" else
                           OpenWeatherMapClient(api_key=supplied_key).fetch_current())
                st.session_state["weather_query"] = obs
                st.session_state["weather_source"] = source
            except (WeatherServiceError, ValueError, OSError):
                st.error("No se pudo consultar el proveedor; el snapshot local no se modificó.")
    if "weather_query" in st.session_state and st.session_state.get("weather_source") == source:
        obs = st.session_state["weather_query"]
        st.success(f"Consulta temporal: {obs.source} · {obs.observed_at} · {obs.temperature_c:.1f} °C. "
                    "No se aplica a la ruta ni al informe.")
    st.subheader("Escenario horario de tráfico")
    st.caption("Los factores por horario y tipo de vía son supuestos, no aforos ni velocidades medidas en toda la red.")
    sample_hour = st.slider("Hora simulada para explorar el supuesto", 0, 23, 13, key="traffic_exploration")
    simulated = get_traffic_by_schedule(sample_hour)
    st.write(f"{sample_hour}:00 · {simulated.level.replace('_', ' ')} · "
             f"factor uniforme para 'avenida': {calculate_traffic_multiplier(simulated):.4f}×. "
             "Este control solo explica el escenario; la ruta tiene su propio formulario.")
    st.subheader("Consulta puntual TomTom (opcional)")
    traffic_key = st.text_input("Clave TomTom (opcional, solo lectura puntual)", type="password")
    if st.button("Consultar segmento TomTom"):
        if not traffic_key:
            st.warning("Introduzca una clave para consultar el segmento.")
        else:
            with st.spinner("Consultando un segmento..."):
                flow = TomTomTrafficClient(api_key=traffic_key).fetch_flow()
            if flow:
                st.write(f"Velocidad en segmento consultado: {flow['current_speed_kmh']:.1f} km/h; "
                         f"flujo libre: {flow['free_flow_speed_kmh']:.1f} km/h. "
                         "No se asigna a otras aristas OSM.")
            else:
                st.error("No se recibió una lectura TomTom; no se usó como dato de ruta.")


def manual_panel() -> None:
    st.header("Dijkstra, paso a paso")
    st.write("Instancia manual de seis nodos: siga las extracciones, distancias y predecesores de cada cola.")
    st.caption("Los nombres de lugares son reales; longitudes y pendientes son supuestos didácticos, no aristas OSM.")
    metric = st.selectbox("Métrica ilustrativa", ["distance", "time"],
                          format_func=lambda m: "Distancia (m)" if m == "distance" else "Tiempo (s)")
    instance = load_cusco_instance(metric)
    target = st.selectbox("Destino", instance.nodes[1:], format_func=instance.label)
    queue = st.selectbox("Cola para la traza", list(QUEUES), format_func=QUEUES.get)
    try:
        result = dijkstra_solver(instance.nodes, instance.adj, "A", queue_type=queue, record_trace=True)
        certificate = verify_shortest_paths(instance.nodes, instance.adj, "A", result)
        if not certificate["ok"]:
            st.error("El certificado de optimalidad falló para esta instancia.")
            return
        st.write(f"Ruta: {' → '.join(instance.label(n) for n in result['paths'][target])} · "
                  f"costo {result['distances'][target]:.2f} {'m' if metric == 'distance' else 's'}")
        st.caption("Certificado de caminos, cadenas al origen y desigualdades: válido.")
        history = result["history"]
        selected = st.slider("Paso de la traza", 1, len(history), 1)
        current = history[selected - 1]
        st.write(f"**Paso {selected} de {len(history)}:** se extrajo {instance.label(current['extracted'])} "
                 f"con costo definitivo {current['dist_extracted']:.2f}.")
        state = pd.DataFrame([{
            "Nodo": instance.label(n),
            "Distancia": f"{current['distances'][n]:.2f}" if math.isfinite(current["distances"][n]) else "∞",
            "Predecesor": (str(current["predecessors"].get(n))
                            if current["predecessors"].get(n) is not None else "Sin dato"),
            "Estado": ("Definitivo" if n in current["permanent_set"] else
                       "Tentativo" if math.isfinite(current["distances"][n]) else "Sin alcanzar"),
        } for n in instance.nodes])
        st.dataframe(state, hide_index=True, width="stretch")
        relaxations = current["relaxations"]
        if relaxations:
            st.write("**Aristas examinadas en este paso**")
            st.dataframe(pd.DataFrame([{
                "Hacia": instance.label(edge["to_node"]), "Peso": edge["edge_weight"],
                "Candidato": edge["new_dist"], "Mejora": "Sí" if edge["relaxed"] else "No",
            } for edge in relaxations]), hide_index=True, width="stretch")
        else:
            st.caption("Este paso no examinó aristas salientes útiles.")
        st.subheader("Todas las extracciones")
        rows = [{"Paso": step["k"], "Extraído": instance.label(step["extracted"]),
                  "Distancia": step["dist_extracted"],
                  "Mejoras": ", ".join(str(r["to_node"]) for r in step["relaxations"] if r["relaxed"]) or "Ninguna"}
                 for step in history]
        summary = pd.DataFrame(rows)
        st.dataframe(summary, hide_index=True, width="stretch")
        st.download_button("Descargar traza CSV", summary.to_csv(index=False).encode("utf-8"),
                           "traza_manual.csv", "text/csv")
    except (ValueError, KeyError, TypeError) as exc:
        st.error(f"No se pudo verificar la traza: {exc}")


def methods_panel() -> None:
    st.header("Datos y método")
    st.write("El experimento, la consulta vial y los escenarios opcionales usan fuentes distintas. "
             "Esta página permite comprobarlas sin cambiar archivos.")
    sources = pd.DataFrame([
        {"Uso": "Rutas", "Archivo": "cusco_osm_drive.json", "Naturaleza": "Red OSM congelada; pesos de tiempo OSMnx o longitudes"},
        {"Uso": "Rendimiento", "Archivo": "benchmark_results.json", "Naturaleza": "Mediciones de grafos sintéticos por escala"},
        {"Uso": "Caso aplicado", "Archivo": "applied_results.json", "Naturaleza": "Consulta OSM y clima histórico separados del benchmark"},
        {"Uso": "Escenario actualizable", "Archivo": "weather_cusco.json", "Naturaleza": "Lectura local posterior; no reemplaza el caso aplicado"},
    ])
    st.dataframe(sources, hide_index=True, width="stretch")
    if BENCHMARK_PATH.exists():
        try:
            benchmark = load_json(str(BENCHMARK_PATH), file_version(BENCHMARK_PATH))
            st.subheader("Protocolo experimental guardado")
            st.dataframe(pd.DataFrame([{"Campo": key, "Valor": str(value)}
                                      for key, value in benchmark["protocol"].items()]),
                         hide_index=True, width="stretch")
            st.caption(f"Generado: {benchmark.get('generated_at_utc', 'fecha no indicada')}. "
                       f"Entorno registrado: Python {benchmark.get('environment', {}).get('python', 'no indicado')}.")
        except (ValueError, OSError, KeyError, TypeError) as exc:
            st.error(f"No se pudo leer el protocolo: {exc}")
    else:
        st.info("Falta el benchmark canónico. Revise python/data/processed/benchmark_results.json.")
    st.subheader("Alcance de las conclusiones")
    st.write("La red OSM no incluye pendientes ni tráfico medido por arista. La lectura TomTom es puntual. "
             "Los cambios horarios y climáticos se aplican uniformemente: son sensibilidad, no congestión observada. "
             "AG-C06 también requiere planes, reflexiones, seguimiento y defensa individuales auténticos.")
    report_path = Path(__file__).resolve().parent.parent / "latex" / "main.pdf"
    if report_path.exists():
        st.download_button("Descargar informe técnico PDF", report_path.read_bytes(),
                           "informe_rutas_cusco.pdf", "application/pdf")
    else:
        st.caption("El informe PDF no está incluido en este entorno; compílelo con latex/compilar.ps1.")


def main() -> None:
    st.set_page_config(page_title="Rutas mínimas · UNSAAC", layout="wide", initial_sidebar_state="collapsed")
    apply_styles()
    st.markdown('<div class="institution-line"><strong>UNSAAC · Grupo 5</strong>'
                '<span>Algoritmos Avanzados · Rutas mínimas y colas de prioridad</span></div>',
                unsafe_allow_html=True)
    st.title("Rutas mínimas en Cusco")
    st.write("Ruta OSM, comparación experimental y evidencia del algoritmo en un mismo lugar.")
    with st.container(key="main_nav"):
        area = st.radio("Sección de la aplicación", ["Ruta", "Comparación", "Clima y tráfico",
                                                   "Traza manual", "Datos y método"], horizontal=True,
                        label_visibility="collapsed")
    {"Ruta": route_view, "Comparación": comparison_view, "Clima y tráfico": weather_panel,
     "Traza manual": manual_panel, "Datos y método": methods_panel}[area]()


if __name__ == "__main__":
    main()
