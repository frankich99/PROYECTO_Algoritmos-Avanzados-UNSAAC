"""
Implementaciones de referencia para validar los resultados de Dijkstra.

- bellman_ford: algoritmo independiente (programación dinámica sobre aristas,
  O(V·E)). No usa colas de prioridad, por lo que un error en cualquier heap no
  puede "contagiarse" a la referencia. Admite pesos negativos y detecta ciclos
  negativos.
- dijkstra_array: Dijkstra con arreglo no ordenado, O(V^2). Es la versión
  "de libro" más simple (fila 1 de la tabla comparativa del informe).

Ambas devuelven el mismo formato de salida que dijkstra_solver.
"""
from typing import Any, Dict, Hashable, List, Optional, Tuple
import time

from src.algorithms.dijkstra import INF, reconstruct_path
from src.io.graph_io import InvalidInstanceError, validate_graph


class NegativeCycleError(InvalidInstanceError):
    """El grafo tiene un ciclo de peso negativo alcanzable desde el origen."""


def bellman_ford(
    nodes: List[Hashable],
    adj: Dict[Hashable, List[Tuple[Hashable, float]]],
    source: Hashable,
    validate: bool = True,
) -> Dict[str, Any]:
    if validate:
        validate_graph(nodes, adj, source, allow_negative=True)
    t0 = time.perf_counter()
    dist: Dict[Hashable, float] = {v: INF for v in nodes}
    prev: Dict[Hashable, Optional[Hashable]] = {v: None for v in nodes}
    dist[source] = 0.0
    edges = [(u, v, float(w)) for u in nodes for v, w in adj.get(u, [])]
    relax_attempts = 0
    rounds = 0
    for _ in range(len(nodes) - 1):
        rounds += 1
        changed = False
        for u, v, w in edges:
            if dist[u] == INF:
                continue
            relax_attempts += 1
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                prev[v] = u
                changed = True
        if not changed:
            break
    for u, v, w in edges:
        if dist[u] != INF and dist[u] + w < dist[v]:
            raise NegativeCycleError(f"Ciclo de peso negativo alcanzable desde {source!r} (arista {u!r}->{v!r}).")
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    return {
        "algorithm": "bellman_ford",
        "queue": None,
        "source": source,
        "distances": dist,
        "predecessors": prev,
        "paths": {d: reconstruct_path(prev, dist, d) for d in nodes},
        "history": [],
        "stats": {"rounds": rounds, "relax_attempts": relax_attempts,
                  "visited_count": sum(1 for v in nodes if dist[v] != INF)},
        "elapsed_ms": elapsed_ms,
    }


def dijkstra_array(
    nodes: List[Hashable],
    adj: Dict[Hashable, List[Tuple[Hashable, float]]],
    source: Hashable,
) -> Dict[str, Any]:
    validate_graph(nodes, adj, source)
    t0 = time.perf_counter()
    dist = {v: INF for v in nodes}
    prev: Dict[Hashable, Optional[Hashable]] = {v: None for v in nodes}
    dist[source] = 0.0
    pending = set(nodes)
    while pending:
        u = min(pending, key=lambda x: dist[x])   # búsqueda lineal O(V)
        if dist[u] == INF:
            break
        pending.remove(u)
        for v, w in adj.get(u, []):
            if v in pending and dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                prev[v] = u
    return {
        "algorithm": "dijkstra_array",
        "queue": "unsorted_array",
        "source": source,
        "distances": dist,
        "predecessors": prev,
        "paths": {d: reconstruct_path(prev, dist, d) for d in nodes},
        "history": [],
        "stats": {},
        "elapsed_ms": (time.perf_counter() - t0) * 1000.0,
    }
