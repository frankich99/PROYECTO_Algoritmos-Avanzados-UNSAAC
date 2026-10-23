"""
Min-Heap Binario con tabla de posiciones para Decrease-Key en O(log V).

Estructura principal del Avance 4.

Representación:
- heap: arreglo contiguo de pares (clave, item); hijo izq. 2i+1, der. 2i+2.
- pos:  diccionario item -> índice en heap. Se actualiza en cada intercambio
        (método _swap), lo que permite ubicar un vértice en O(1) dentro de
        decrease_key sin búsqueda lineal.

Complejidad: insert, extract_min y decrease_key en O(log V); espacio O(V).
"""
from typing import Any, Dict, Hashable, List, Tuple

from src.datastructures.base import PriorityQueue


class IndexedMinHeap(PriorityQueue):
    """Cola de prioridad Min-Heap binaria con indexación directa de nodos."""

    name = "binary_heap"

    def __init__(self) -> None:
        super().__init__()
        self.heap: List[Tuple[float, Any]] = []   # (clave_distancia, id_nodo)
        self.pos: Dict[Any, int] = {}             # id_nodo -> índice en heap
        self.swaps: int = 0

    def __len__(self) -> int:
        return len(self.heap)

    def __contains__(self, node: Hashable) -> bool:
        return node in self.pos

    def insert(self, node: Hashable, dist: float) -> None:
        dist = self._check_key(dist)
        if node in self.pos:
            raise ValueError(f"El nodo {node!r} ya está en la cola; use decrease_key.")
        idx = len(self.heap)
        self.heap.append((dist, node))
        self.pos[node] = idx
        self._sift_up(idx)

    def peek_min(self) -> Tuple[float, Any]:
        if not self.heap:
            raise IndexError("Consulta sobre montículo vacío.")
        return self.heap[0]

    def extract_min(self) -> Tuple[float, Any]:
        if not self.heap:
            raise IndexError("Extracción sobre montículo vacío.")
        min_dist, min_node = self.heap[0]
        last_dist, last_node = self.heap.pop()
        del self.pos[min_node]
        if self.heap:
            # El último elemento ocupa la raíz y se hunde hasta restaurar el orden.
            self.heap[0] = (last_dist, last_node)
            self.pos[last_node] = 0
            self._sift_down(0)
        return min_dist, min_node

    def decrease_key(self, node: Hashable, new_dist: float) -> None:
        new_dist = self._check_key(new_dist)
        if node not in self.pos:
            return
        idx = self.pos[node]                      # O(1) gracias a la tabla pos
        current_dist, _ = self.heap[idx]
        self.comparisons += 1
        if new_dist < current_dist:
            self.heap[idx] = (new_dist, node)
            self._sift_up(idx)                    # a lo sumo floor(log2 V) niveles

    # -- rutinas internas ---------------------------------------------------------
    def _sift_up(self, idx: int) -> None:
        while idx > 0:
            parent = (idx - 1) // 2
            self.comparisons += 1
            if self.heap[idx][0] < self.heap[parent][0]:
                self._swap(idx, parent)
                idx = parent
            else:
                break

    def _sift_down(self, idx: int) -> None:
        n = len(self.heap)
        while True:
            left = 2 * idx + 1
            right = 2 * idx + 2
            smallest = idx

            if left < n:
                self.comparisons += 1
                if self.heap[left][0] < self.heap[smallest][0]:
                    smallest = left

            if right < n:
                self.comparisons += 1
                if self.heap[right][0] < self.heap[smallest][0]:
                    smallest = right

            if smallest != idx:
                self._swap(idx, smallest)
                idx = smallest
            else:
                break

    def _swap(self, i: int, j: int) -> None:
        """Intercambio atómico: arreglo y tabla de posiciones se actualizan juntos."""
        self.swaps += 1
        node_i = self.heap[i][1]
        node_j = self.heap[j][1]
        self.heap[i], self.heap[j] = self.heap[j], self.heap[i]
        self.pos[node_i] = j
        self.pos[node_j] = i

    # -- verificación e instrumentación ----------------------------------------------
    def check_invariants(self) -> bool:
        """Propiedad de heap + coherencia de pos. Usado por las pruebas."""
        for i in range(1, len(self.heap)):
            if self.heap[i][0] < self.heap[(i - 1) // 2][0]:
                return False
        return all(self.heap[i][1] in self.pos and self.pos[self.heap[i][1]] == i
                   for i in range(len(self.heap))) and len(self.pos) == len(self.heap)

    def op_stats(self) -> Dict[str, Any]:
        return {"comparisons": self.comparisons, "swaps": self.swaps}

    def get_state(self) -> List[Tuple[Any, float]]:
        """Retorna el estado de la cola ordenado alfabéticamente por id de nodo."""
        return sorted([(node, dist) for dist, node in self.heap], key=lambda x: str(x[0]))
