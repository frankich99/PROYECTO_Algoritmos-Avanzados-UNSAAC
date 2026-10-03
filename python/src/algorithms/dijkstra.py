"""
Algoritmo de Dijkstra con colas de prioridad intercambiables.
Genera trazas paso a paso y estadísticas de operaciones.
"""
from typing import Dict, List, Tuple, Any, Optional
import heapq

# Intento de importación de colas especializadas (se integrarán en commits 2 y 3)
try:
    from src.datastructures.indexed_min_heap import IndexedMinHeap
except ImportError:
    IndexedMinHeap = None

try:
    from src.datastructures.d_ary_heap import DAryHeap
except ImportError:
    DAryHeap = None

try:
    from src.datastructures.fibonacci_heap import FibonacciHeap
except ImportError:
    FibonacciHeap = None


class _FallbackBinaryHeap:
    """Implementación base de cola de prioridad binaria para el prototipo inicial."""
    def __init__(self):
        self._heap = []
        self._entry_map = {}
        self._counter = 0

    def is_empty(self) -> bool:
        return len(self._entry_map) == 0

    def insert(self, node: str, dist: float) -> None:
        self.decrease_key(node, dist)

    def decrease_key(self, node: str, dist: float) -> None:
        self._counter += 1
        entry = [dist, self._counter, node]
        self._entry_map[node] = entry
        heapq.heappush(self._heap, entry)

    def extract_min(self) -> Tuple[float, str]:
        while self._heap:
            dist, count, node = heapq.heappop(self._heap)
            if node in self._entry_map and self._entry_map[node][1] == count:
                del self._entry_map[node]
                return dist, node
        raise IndexError("Extracción sobre montículo vacío.")


def dijkstra_solver(
    nodes: List[str],
    adj: Dict[str, List[Tuple[str, float]]],
    source: str,
    queue_type: str = "binary_heap"
) -> Dict[str, Any]:
    """Ejecuta Dijkstra con la cola de prioridad indicada. Retorna distancias, caminos, traza y estadísticas."""
    dist: Dict[str, float] = {v: float('inf') for v in nodes}
    prev: Dict[str, Optional[str]] = {v: None for v in nodes}
    dist[source] = 0.0

    # Selección de estructura de cola de prioridad
    if queue_type == "binary_heap":
        if IndexedMinHeap is not None:
            heap = IndexedMinHeap()
        else:
            heap = _FallbackBinaryHeap()
    elif queue_type == "4ary_heap":
        if DAryHeap is None:
            raise NotImplementedError("DAryHeap no disponible en esta fase. Pendiente de integración por Yeni Porroa.")
        heap = DAryHeap(d=4)
    elif queue_type == "fibonacci_heap":
        if FibonacciHeap is None:
            raise NotImplementedError("FibonacciHeap no disponible en esta fase. Pendiente de integración por Romario Quispe.")
        heap = FibonacciHeap()
    else:
        raise ValueError(f"Tipo de cola no soportado: {queue_type}")

    # Carga inicial de nodos
    for v in nodes:
        heap.insert(v, dist[v])

    visited = set()
    history = []
    iteration = 0
    extract_count = 0
    decrease_count = 0
    relax_attempts = 0

    while not heap.is_empty():
        d_u, u = heap.extract_min()

        extract_count += 1

        if d_u == float('inf'):
            break

        visited.add(u)
        iteration += 1
        step_relaxations = []

        for v, weight in adj.get(u, []):
            if v not in visited:
                relax_attempts += 1
                old_d = dist[v]
                candidate_d = d_u + weight
                if candidate_d < old_d:
                    dist[v] = candidate_d
                    prev[v] = u
                    heap.decrease_key(v, candidate_d)
                    decrease_count += 1
                    step_relaxations.append({
                        "to_node": v,
                        "old_dist": old_d,
                        "new_dist": candidate_d,
                        "edge_weight": weight
                    })

        history.append({
            "k": iteration,
            "extracted": u,
            "dist_extracted": d_u,
            "queue_state": {k: dist[k] for k in nodes if k not in visited},
            "permanent_set": sorted(list(visited)),
            "relaxations": step_relaxations
        })

    # Reconstrucción de caminos
    paths: Dict[str, List[str]] = {}
    for dest in nodes:
        if dist[dest] == float('inf'):
            paths[dest] = []
            continue
        p = []
        curr: Optional[str] = dest
        while curr is not None:
            p.append(curr)
            curr = prev.get(curr)
        paths[dest] = p[::-1]

    return {
        "distances": dist,
        "predecessors": prev,
        "paths": paths,
        "history": history,
        "stats": {
            "extract_count": extract_count,
            "decrease_count": decrease_count,
            "relax_attempts": relax_attempts,
            "visited_count": len(visited)
        }
    }
