"""
Heap d-ario (d=4 por defecto) con indexación inversa. Altura log_d(V).
"""
from typing import List, Tuple, Dict, Any, Optional

class DAryHeap:
    """Cola de prioridad d-aria indexada (por defecto d=4)."""
    def __init__(self, d: int = 4):
        if d < 2:
            raise ValueError("El grado d debe ser al menos 2.")
        self.d: int = d
        self.heap: List[Tuple[float, Any]] = []
        self.pos: Dict[Any, int] = {}
        self.comparisons: int = 0
        self.swaps: int = 0

    def is_empty(self) -> bool:
        return len(self.heap) == 0

    def __len__(self) -> int:
        return len(self.heap)

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
            parent = (idx - 1) // self.d
            self.comparisons += 1
            if self.heap[idx][0] < self.heap[parent][0]:
                self._swap(idx, parent)
                idx = parent
            else:
                break

    def _sift_down(self, idx: int) -> None:
        n = len(self.heap)
        while True:
            first_child = self.d * idx + 1
            if first_child >= n:
                break
            
            # Buscar el hijo menor entre los d hijos contiguos
            smallest = first_child
            last_child = min(first_child + self.d, n)
            for child in range(first_child + 1, last_child):
                self.comparisons += 1
                if self.heap[child][0] < self.heap[smallest][0]:
                    smallest = child

            self.comparisons += 1
            if self.heap[smallest][0] < self.heap[idx][0]:
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
        return sorted([(node, dist) for dist, node in self.heap], key=lambda x: str(x[0]))
