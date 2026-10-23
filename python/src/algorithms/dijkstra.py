"""
Algoritmo de Dijkstra con colas de prioridad intercambiables (inyección por nombre).

Correspondencia con el Algoritmo 1 del informe (Sección 5, "Dijkstra con cola
de prioridad parametrizada"); los números de línea del pseudocódigo se indican
como [Lk] en los comentarios.

La estructura concreta se obtiene del registro (src/datastructures/registry.py),
así que las tres alternativas comparten exactamente el mismo código algorítmico:
cualquier diferencia de resultados solo puede deberse a la cola.
"""
from typing import Any, Dict, Hashable, List, Optional, Tuple
import time

from src.datastructures.registry import create_queue, normalize_queue_name
from src.io.graph_io import validate_graph

INF = float("inf")


def reconstruct_path(prev: Dict[Hashable, Optional[Hashable]], dist: Dict[Hashable, float],
                     dest: Hashable) -> List[Hashable]:
    """Sigue los predecesores desde dest hasta el origen. [] si dest es inalcanzable."""
    if dist[dest] == INF:
        return []
    path = []
    curr: Optional[Hashable] = dest
    guard = len(prev) + 1
    while curr is not None:
        path.append(curr)
        curr = prev.get(curr)
        guard -= 1
        if guard < 0:  # sólo ocurriría con predecesores corruptos (ciclo)
            raise RuntimeError("Ciclo detectado en la tabla de predecesores.")
    return path[::-1]


def dijkstra_solver(
    nodes: List[Hashable],
    adj: Dict[Hashable, List[Tuple[Hashable, float]]],
    source: Hashable,
    queue_type: str = "binary_heap",
    record_trace: bool = False,
    validate: bool = True,
    build_paths: bool = True,
) -> Dict[str, Any]:
    """
    Ejecuta Dijkstra desde source usando la cola indicada.

    Retorna un diccionario con el formato de salida común a todas las
    alternativas: distances, predecessors, paths, history (si record_trace),
    stats (contadores de operaciones) y elapsed_ms.
    build_paths=False omite la reconstrucción de rutas (el benchmark mide solo el núcleo).
    """
    queue_type = normalize_queue_name(queue_type)
    if validate:
        validate_graph(nodes, adj, source)

    t0 = time.perf_counter()

    # [L1-L6] Inicialización: d[v]=inf, pi[v]=NIL, d[s]=0
    dist: Dict[Hashable, float] = {v: INF for v in nodes}
    prev: Dict[Hashable, Optional[Hashable]] = {v: None for v in nodes}
    dist[source] = 0.0

    # [L7] Q.BUILD(V, d): inserción iterativa de cada vértice con su clave
    heap = create_queue(queue_type)
    for v in nodes:
        heap.insert(v, dist[v])

    visited = set()          # [L8] S <- conjunto de vértices permanentes
    history: List[Dict[str, Any]] = []
    extract_count = decrease_count = relax_attempts = 0

    # [L9] mientras Q no esté vacía
    while not heap.is_empty():
        d_u, u = heap.extract_min()          # [L10]
        extract_count += 1

        if d_u == INF:                       # [L11-L13] el resto es inalcanzable
            break

        visited.add(u)                       # [L14]
        step_relaxations = []

        for v, weight in adj.get(u, []):     # [L15]
            if v in visited:                 # [L16]
                continue
            relax_attempts += 1
            old_d = dist[v]
            candidate_d = d_u + weight       # [L17]
            relaxed = candidate_d < old_d    # [L18]
            if relaxed:
                dist[v] = candidate_d        # [L19]
                prev[v] = u                  # [L20]
                heap.decrease_key(v, candidate_d)   # [L21]
                decrease_count += 1
            if record_trace:
                step_relaxations.append({
                    "to_node": v, "old_dist": old_d, "new_dist": candidate_d,
                    "edge_weight": weight, "relaxed": relaxed,
                })

        if record_trace:
            history.append({
                "k": len(visited),
                "extracted": u,
                "dist_extracted": d_u,
                "permanent_set": sorted(visited, key=str),
                "queue_state": {k: dist[k] for k in nodes if k not in visited},
                "distances": dict(dist),
                "predecessors": dict(prev),
                "relaxations": step_relaxations,
            })

    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    # Extensión al pseudocódigo: reconstrucción de caminos a partir de pi ([L26] retorna d y pi)
    paths = {dest: reconstruct_path(prev, dist, dest) for dest in nodes} if build_paths else {}

    stats = {
        "insert_ops": len(nodes),
        "extract_min_ops": extract_count,
        "decrease_key_ops": decrease_count,
        "relax_attempts": relax_attempts,
        "visited_count": len(visited),
        **heap.op_stats(),
    }
    # Alias de la versión de la Unidad 1 (compatibilidad con scripts anteriores)
    stats["extract_count"] = extract_count
    stats["decrease_count"] = decrease_count

    return {
        "algorithm": "dijkstra",
        "queue": queue_type,
        "source": source,
        "distances": dist,
        "predecessors": prev,
        "paths": paths,
        "history": history,
        "stats": stats,
        "elapsed_ms": elapsed_ms,
    }
