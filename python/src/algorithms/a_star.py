"""A* como extensión punto a punto del núcleo comparativo de Dijkstra.

La heurística se escala con los pesos de la propia instancia. Esto evita
suponer que unas coordenadas o una velocidad máxima son válidas para cualquier
grafo. Si faltan coordenadas, A* usa h=0 y conserva la corrección de Dijkstra.
"""
import math
import time
from typing import Any, Callable, Dict, Hashable, List, Optional, Tuple

from src.datastructures.registry import create_queue, normalize_queue_name
from src.io.graph_io import InvalidInstanceError, validate_graph

Coords = Dict[Hashable, Tuple[float, float]]
Adjacency = Dict[Hashable, List[Tuple[Hashable, float]]]


def euclidean_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def admissible_scale(nodes: List[Hashable], adj: Adjacency, coords: Coords) -> float:
    """Calcula lambda=min(w(u,v)/||x_u-x_v||) para todas las aristas útiles.

    Entonces h(v)=lambda*||x_v-x_t|| es consistente por desigualdad
    triangular. Cualquier falta de coordenadas desactiva la heurística.
    """
    if any(node not in coords for node in nodes):
        return 0.0
    ratios: List[float] = []
    for u in nodes:
        for v, weight in adj.get(u, []):
            geometric = euclidean_distance(coords[u], coords[v])
            if geometric > 0:
                ratios.append(float(weight) / geometric)
    return min(ratios, default=0.0)


def make_consistent_heuristic(
    nodes: List[Hashable],
    adj: Adjacency,
    coords: Coords,
    target: Hashable,
) -> Tuple[Callable[[Hashable], float], float]:
    if target not in coords:
        return (lambda _node: 0.0), 0.0
    scale = admissible_scale(nodes, adj, coords)
    target_point = coords[target]

    def heuristic(node: Hashable) -> float:
        if scale == 0.0 or node not in coords:
            return 0.0
        return scale * euclidean_distance(coords[node], target_point)

    return heuristic, scale


def validate_heuristic_consistency(
    nodes: List[Hashable],
    adj: Adjacency,
    target: Hashable,
    heuristic: Callable[[Hashable], float],
    eps: float = 1e-9,
) -> None:
    """Rechaza heurísticas negativas, no finitas o inconsistentes."""
    values: Dict[Hashable, float] = {}
    for node in nodes:
        value = float(heuristic(node))
        if not math.isfinite(value) or value < -eps:
            raise InvalidInstanceError(f"Heurística inválida en {node!r}: {value!r}.")
        values[node] = max(0.0, value)
    if abs(values[target]) > eps:
        raise InvalidInstanceError("Una heurística consistente debe cumplir h(target)=0.")
    for u in nodes:
        for v, weight in adj.get(u, []):
            if values[u] > float(weight) + values[v] + eps:
                raise InvalidInstanceError(
                    f"Heurística inconsistente en {u!r}->{v!r}: "
                    f"h(u)={values[u]:.6g} > w+h(v)={float(weight) + values[v]:.6g}."
                )


def a_star_solver(
    nodes: List[Hashable],
    adj: Adjacency,
    source: Hashable,
    target: Hashable,
    coords: Optional[Coords] = None,
    queue_type: str = "binary_heap",
    custom_heuristic: Optional[Callable[[Hashable], float]] = None,
    validate: bool = True,
) -> Dict[str, Any]:
    """Resuelve una consulta origen-destino con una heurística verificada."""
    queue_type = normalize_queue_name(queue_type)
    if validate:
        validate_graph(nodes, adj, source)
    if target not in set(nodes):
        raise InvalidInstanceError(f"El nodo objetivo {target!r} no existe en el grafo.")

    heuristic_scale = 0.0
    if custom_heuristic is not None:
        heuristic = custom_heuristic
        heuristic_kind = "custom_consistent"
    elif coords:
        heuristic, heuristic_scale = make_consistent_heuristic(nodes, adj, coords, target)
        heuristic_kind = "scaled_euclidean" if heuristic_scale > 0 else "zero"
    else:
        heuristic = lambda _node: 0.0
        heuristic_kind = "zero"
    validate_heuristic_consistency(nodes, adj, target, heuristic)

    started_ns = time.perf_counter_ns()
    infinity = float("inf")
    g_score: Dict[Hashable, float] = {node: infinity for node in nodes}
    f_score: Dict[Hashable, float] = {node: infinity for node in nodes}
    predecessors: Dict[Hashable, Optional[Hashable]] = {node: None for node in nodes}
    g_score[source] = 0.0
    f_score[source] = heuristic(source)

    queue = create_queue(queue_type)
    queue.insert(source, f_score[source])
    closed = set()
    stats = {
        "insert_ops": 1,
        "extract_min_ops": 0,
        "decrease_key_ops": 0,
        "relax_attempts": 0,
        "expanded_nodes": 0,
    }

    while not queue.is_empty():
        _f_u, u = queue.extract_min()
        stats["extract_min_ops"] += 1
        closed.add(u)
        stats["expanded_nodes"] += 1
        if u == target:
            break

        for v, weight in adj.get(u, []):
            stats["relax_attempts"] += 1
            if v in closed:
                continue
            candidate = g_score[u] + weight
            if candidate < g_score[v]:
                predecessors[v] = u
                g_score[v] = candidate
                f_score[v] = candidate + heuristic(v)
                if v in queue:
                    queue.decrease_key(v, f_score[v])
                    stats["decrease_key_ops"] += 1
                else:
                    queue.insert(v, f_score[v])
                    stats["insert_ops"] += 1

    path: List[Hashable] = []
    if math.isfinite(g_score[target]):
        current: Optional[Hashable] = target
        while current is not None:
            path.append(current)
            current = predecessors[current]
        path.reverse()

    stats.update(queue.op_stats())
    return {
        "algorithm": "a_star",
        "queue": queue_type,
        "source": source,
        "target": target,
        "target_distance": g_score[target],
        "path": path,
        "g_scores": g_score,
        "f_scores": f_score,
        "predecessors": predecessors,
        "visited_nodes": list(closed),
        "stats": stats,
        "heuristic": heuristic_kind,
        "heuristic_scale": heuristic_scale,
        "elapsed_ms": (time.perf_counter_ns() - started_ns) / 1_000_000.0,
    }
