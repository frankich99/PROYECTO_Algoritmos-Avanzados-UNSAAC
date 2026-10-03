"""
Min-Heap Binario con tabla de posiciones para Decrease-Key en O(log V).
"""
from typing import List, Tuple, Dict, Any, Optional

class IndexedMinHeap:
    """Cola de prioridad Min-Heap con indexación directa de nodos."""
    def __init__(self):
        # heap almacena tuplas (clave_distancia, id_nodo)
        self.heap: List[Tuple[float, Any]] = []
        # pos mapea id_nodo -> indice en self.heap
        self.pos: Dict[Any, int] = {}
        # Contadores de operaciones elementales para análisis empírico
        self.comparisons: int = 0
        self.swaps: int = 0

    def is_empty(self) -> bool:
        return len(self.heap) == 0

    def __len__(self) -> int:
        return len(self.heap)

    def contains(self, node: Any) -> bool:
        return node in self.pos

    def insert(self, node: Any, dist: float) -> None:
        idx = len(self.heap)
        self.heap.append((dist, node))
        self.pos[node] = idx
        self._sift_up(idx)

    def extract_min(self) -> Tuple[float, Any]:
        if not self.heap:
            raise IndexError("Extracción sobre montículo vacío.")
        min_dist, min_node = self.heap[0]
        last_dist, last_node = self.heap.pop()
        del self.pos[min_node]
        if self.heap:
            self.heap[0] = (last_dist, last_node)
            self.pos[last_node] = 0
            self._sift_down(0)
        return min_dist, min_node

    def decrease_key(self, node: Any, new_dist: float) -> None:
        if node not in self.pos:
            return
        idx = self.pos[node]
        current_dist, _ = self.heap[idx]
        self.comparisons += 1
        if new_dist < current_dist:
            self.heap[idx] = (new_dist, node)
            self._sift_up(idx)

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
        self.swaps += 1
        node_i = self.heap[i][1]
        node_j = self.heap[j][1]
        self.heap[i], self.heap[j] = self.heap[j], self.heap[i]
        self.pos[node_i] = j
        self.pos[node_j] = i

    def get_state(self) -> List[Tuple[Any, float]]:
        """Retorna el estado de la cola ordenado alfabéticamente por id de nodo."""
        return sorted([(node, dist) for dist, node in self.heap], key=lambda x: str(x[0]))
