"""
Registro de colas de prioridad: punto único para seleccionarlas por nombre.

Lo usan el solver de Dijkstra, la CLI, el benchmark y las pruebas, de modo que
agregar una nueva estructura solo requiere registrarla aquí.
"""
from typing import Callable, Dict, List

from src.datastructures.base import PriorityQueue
from src.datastructures.d_ary_heap import DAryHeap
from src.datastructures.fibonacci_heap import FibonacciHeap
from src.datastructures.indexed_min_heap import IndexedMinHeap

QUEUE_FACTORIES: Dict[str, Callable[[], PriorityQueue]] = {
    "binary_heap": IndexedMinHeap,
    "4ary_heap": lambda: DAryHeap(d=4),
    "fibonacci_heap": FibonacciHeap,
}

QUEUE_LABELS: Dict[str, str] = {
    "binary_heap": "Binary Min-Heap indexado (Avance 4)",
    "4ary_heap": "4-ary Heap indexado (Avance 5)",
    "fibonacci_heap": "Fibonacci Heap (Avance 5)",
}

QUEUE_ALIASES: Dict[str, str] = {
    "binary": "binary_heap", "bin": "binary_heap", "binario": "binary_heap",
    "4ary": "4ary_heap", "dary": "4ary_heap", "d_ary": "4ary_heap", "4-ary": "4ary_heap",
    "fibonacci": "fibonacci_heap", "fib": "fibonacci_heap",
}


def available_queues() -> List[str]:
    return list(QUEUE_FACTORIES)


def normalize_queue_name(name: str) -> str:
    key = str(name).strip().lower()
    key = QUEUE_ALIASES.get(key, key)
    if key not in QUEUE_FACTORIES:
        raise ValueError(
            f"Tipo de cola no soportado: {name!r}. Opciones: {', '.join(available_queues())}."
        )
    return key


def create_queue(name: str) -> PriorityQueue:
    return QUEUE_FACTORIES[normalize_queue_name(name)]()
