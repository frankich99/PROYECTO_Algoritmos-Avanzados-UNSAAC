"""
Contrato común de las colas de prioridad usadas por Dijkstra.

Todas las estructuras (IndexedMinHeap, DAryHeap, FibonacciHeap) heredan de
PriorityQueue, de modo que el solver de Dijkstra no conoce la estructura
concreta: solo invoca insert / extract_min / decrease_key / is_empty.

Convenciones del contrato (iguales para las tres implementaciones):
- insert(item, key): el item no debe existir; key no puede ser NaN.
- extract_min() -> (key, item): lanza IndexError si la cola está vacía.
- decrease_key(item, new_key): si new_key >= key actual o el item no está
  en la cola, la operación es un no-op (no lanza error). Esto permite que
  Dijkstra la invoque sin consultas previas.
- comparisons: contador de comparaciones de claves (instrumentación).
"""
from abc import ABC, abstractmethod
import math
from typing import Any, Dict, Hashable, Tuple


class PriorityQueue(ABC):
    """Interfaz abstracta de cola de prioridad mínima con Decrease-Key."""

    #: Nombre corto usado en tablas y en la CLI.
    name: str = "abstract"

    def __init__(self) -> None:
        self.comparisons: int = 0

    # -- operaciones del contrato -------------------------------------------------
    @abstractmethod
    def insert(self, item: Hashable, key: float) -> None:
        ...

    @abstractmethod
    def extract_min(self) -> Tuple[float, Hashable]:
        ...

    @abstractmethod
    def decrease_key(self, item: Hashable, new_key: float) -> None:
        ...

    @abstractmethod
    def __len__(self) -> int:
        ...

    @abstractmethod
    def __contains__(self, item: Hashable) -> bool:
        ...

    def is_empty(self) -> bool:
        return len(self) == 0

    def contains(self, item: Hashable) -> bool:
        return item in self

    # -- utilidades compartidas -----------------------------------------------------
    @staticmethod
    def _check_key(key: float) -> float:
        """Rechaza claves no numéricas o NaN (comparaciones indefinidas)."""
        if isinstance(key, bool) or not isinstance(key, (int, float)):
            raise TypeError(f"La clave debe ser numérica, se recibió {type(key).__name__}.")
        if math.isnan(key):
            raise ValueError("La clave no puede ser NaN.")
        return float(key)

    def op_stats(self) -> Dict[str, Any]:
        """Contadores internos propios de cada estructura (para comparar costos)."""
        return {"comparisons": self.comparisons}
