"""
Algoritmo A* (A-Star) para ruteo de emergencia punto a punto.
Extensión heurística del algoritmo de Dijkstra orientada a objetivos (Goal-Directed Search).
Grupo 5 - Algoritmos Avanzados (UNSAAC)
"""
import math
import time
from typing import Any, Callable, Dict, Hashable, List, Optional, Tuple

from src.datastructures.registry import create_queue
from src.io.graph_io import validate_graph

# Velocidad máxima en avenidas de Cusco (35 km/h convertidos a m/s)
V_MAX_MS = 35.0 / 3.6  # ~9.72 m/s

# Coordenadas relativas métricas aproximadas de los nodos del Centro Histórico (origen Plaza Mayor = (0,0))
DEFAULT_CUSCO_COORDS: Dict[str, Tuple[float, float]] = {
    "A": (0.0, 0.0),       # Plaza Mayor
    "B": (-120.0, -10.0),  # Plaza Regocijo
    "C": (180.0, -250.0),  # Qorikancha
    "D": (-310.0, -80.0),  # Plaza San Francisco
    "E": (-480.0, -320.0), # Mercado Central San Pedro
    "F": (350.0, -420.0)   # Plazoleta Limacpampa
}


def euclidean_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Calcula la distancia euclidiana física en línea recta entre dos puntos (x, y)."""
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def make_admissible_heuristic(
    coords: Dict[Hashable, Tuple[float, float]],
    target: Hashable,
    metric: str = "time",
    v_max: float = V_MAX_MS
) -> Callable[[Hashable], float]:
    """
    Construye una función heurística h(u) estrictamente admisible y consistente:
    - Para 'distance': h(u) = distancia_en_linea_recta(u, target) <= distancia_real_en_red
    - Para 'time': h(u) = distancia_en_linea_recta(u, target) / v_max <= tiempo_real_en_red
    
    Al no sobreestimar jamás el costo real (h(u) <= h*(u)), garantiza la optimalidad de A*.
    """
    if target not in coords:
        return lambda _u: 0.0

    target_pt = coords[target]

    def heuristic(node: Hashable) -> float:
        if node not in coords:
            return 0.0
        dist = euclidean_distance(coords[node], target_pt)
        if metric == "time":
            return dist / v_max
        return dist

    return heuristic


def a_star_solver(
    nodes: List[Hashable],
    adj: Dict[Hashable, List[Tuple[Hashable, float]]],
    source: Hashable,
    target: Hashable,
    coords: Optional[Dict[Hashable, Tuple[float, float]]] = None,
    queue_type: str = "binary_heap",
    metric: str = "time",
    custom_heuristic: Optional[Callable[[Hashable], float]] = None,
    validate: bool = True
) -> Dict[str, Any]:
    """
    Ejecuta el Algoritmo A* desde 'source' hasta 'target' con inyección de colas de prioridad.
    """
    if validate:
        validate_graph(nodes, adj, source)
        if target not in nodes:
            raise ValueError(f"El nodo objetivo target '{target}' no existe en el grafo.")

    t0 = time.perf_counter()

    # Heurística admisible
    if custom_heuristic is not None:
        h = custom_heuristic
    elif coords is not None:
        h = make_admissible_heuristic(coords, target, metric=metric)
    elif all(n in DEFAULT_CUSCO_COORDS for n in (source, target)):
        h = make_admissible_heuristic(DEFAULT_CUSCO_COORDS, target, metric=metric)
    else:
        h = lambda _u: 0.0

    g_score: Dict[Hashable, float] = {v: float("inf") for v in nodes}
    f_score: Dict[Hashable, float] = {v: float("inf") for v in nodes}
    prev: Dict[Hashable, Optional[Hashable]] = {v: None for v in nodes}

    g_score[source] = 0.0
    f_score[source] = h(source)

    heap = create_queue(queue_type)
    heap.insert(source, f_score[source])

    visited = set()
    stats = {
        "insert_ops": 1,
        "extract_min_ops": 0,
        "decrease_key_ops": 0,
        "relax_attempts": 0,
        "expanded_nodes": 0
    }

    target_found = False

    while not heap.is_empty():
        f_u, u = heap.extract_min()
        stats["extract_min_ops"] += 1

        if g_score[u] == float("inf"):
            break

        visited.add(u)
        stats["expanded_nodes"] += 1

        if u == target:
            target_found = True
            break

        for v, weight in adj.get(u, []):
            stats["relax_attempts"] += 1
            if v in visited:
                continue

            tentative_g = g_score[u] + weight
            if tentative_g < g_score[v]:
                prev[v] = u
                g_score[v] = tentative_g
                new_f = tentative_g + h(v)
                f_score[v] = new_f

                if v in heap:
                    heap.decrease_key(v, new_f)
                    stats["decrease_key_ops"] += 1
                else:
                    heap.insert(v, new_f)
                    stats["insert_ops"] += 1

    t1 = time.perf_counter()

    # Reconstrucción de la ruta óptima
    path: List[Hashable] = []
    if target_found or g_score[target] < float("inf"):
        curr: Optional[Hashable] = target
        while curr is not None:
            path.append(curr)
            curr = prev[curr]
        path.reverse()

    return {
        "algorithm": "a_star",
        "queue": queue_type,
        "source": source,
        "target": target,
        "target_distance": g_score[target],
        "path": path,
        "g_scores": g_score,
        "f_scores": f_score,
        "predecessors": prev,
        "visited_nodes": list(visited),
        "stats": stats,
        "elapsed_ms": (t1 - t0) * 1000.0
    }
