"""
Interfaz común para seleccionar y ejecutar cualquier alternativa por nombre.

    solve(instance, source, method)  ->  resultado con formato común

Métodos disponibles:
    binary_heap     Dijkstra + IndexedMinHeap   (Avance 4, alternativa 1)
    4ary_heap       Dijkstra + DAryHeap(d=4)    (Avance 5, alternativa 2)
    fibonacci_heap  Dijkstra + FibonacciHeap    (Avance 5, alternativa 2b)
    bellman_ford    Referencia independiente    (validación)
"""
from typing import Any, Dict, Hashable, List

from src.algorithms.dijkstra import dijkstra_solver
from src.algorithms.reference import bellman_ford
from src.datastructures.registry import QUEUE_ALIASES, QUEUE_LABELS, available_queues
from src.io.graph_io import GraphInstance, validate_graph

REFERENCE_METHOD = "bellman_ford"

METHOD_LABELS: Dict[str, str] = {**QUEUE_LABELS, REFERENCE_METHOD: "Bellman-Ford (referencia)"}


def available_methods(include_reference: bool = True) -> List[str]:
    methods = available_queues()
    return methods + [REFERENCE_METHOD] if include_reference else methods


def normalize_method(name: str) -> str:
    key = str(name).strip().lower()
    if key in ("bellman_ford", "bellman-ford", "bf", "referencia", "reference"):
        return REFERENCE_METHOD
    key = QUEUE_ALIASES.get(key, key)
    if key not in METHOD_LABELS:
        raise ValueError(f"Método no soportado: {name!r}. Opciones: {', '.join(available_methods())}, all.")
    return key


def expand_methods(spec: str) -> List[str]:
    """'all' -> todas las colas; 'binary,fib' -> lista normalizada sin duplicados."""
    if spec.strip().lower() == "all":
        return available_methods(include_reference=False)
    out: List[str] = []
    for part in spec.split(","):
        if part.strip():
            m = normalize_method(part)
            if m not in out:
                out.append(m)
    if not out:
        raise ValueError("No se indicó ningún método.")
    return out


def solve(instance: GraphInstance, source: Hashable, method: str = "binary_heap",
          record_trace: bool = False) -> Dict[str, Any]:
    method = normalize_method(method)
    if method == REFERENCE_METHOD:
        validate_graph(instance.nodes, instance.adj, source, allow_negative=True)
        return bellman_ford(instance.nodes, instance.adj, source, validate=False)
    validate_graph(instance.nodes, instance.adj, source)
    return dijkstra_solver(instance.nodes, instance.adj, source, queue_type=method,
                           record_trace=record_trace, validate=False)
