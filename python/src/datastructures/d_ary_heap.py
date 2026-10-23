"""
Montículo d-ario indexado (por defecto d = 4). Alternativa del Avance 5.

Para el índice i (base cero):
    padre(i)  = (i - 1) // d
    hijo_k(i) = d*i + k,   1 <= k <= d

Altura ceil(log_d V): con d = 4 el árbol tiene la mitad de niveles que el
binario, así que decrease_key (sift_up, 1 comparación por nivel) es más
barato; a cambio, extract_min (sift_down) compara hasta d hijos por nivel.
Los d hijos de un nodo son contiguos en el arreglo (mejor localidad de caché).

Igual que IndexedMinHeap, mantiene la tabla pos: item -> índice.
"""
from typing import Any, Dict, Hashable, List, Tuple

from src.datastructures.base import PriorityQueue


class DAryHeap(PriorityQueue):
    """Min-Heap d-ario con Decrease-Key O(log_d V) y Extract-Min O(d log_d V)."""

    def __init__(self, d: int = 4) -> None:
        super().__init__()
        if isinstance(d, bool) or not isinstance(d, int) or d < 2:
            raise ValueError(f"La aridad d debe ser un entero >= 2 (se recibió {d!r}).")
        self.d = d
        self.name = "4ary_heap" if d == 4 else f"{d}ary_heap"
        self.heap: List[Tuple[float, Any]] = []
        self.pos: Dict[Any, int] = {}
        self.swaps: int = 0

    def __len__(self) -> int:
        return len(self.heap)

    def __contains__(self, item: Hashable) -> bool:
        return item in self.pos

    def insert(self, item: Hashable, key: float) -> None:
        key = self._check_key(key)
        if item in self.pos:
            raise ValueError(f"El nodo {item!r} ya está en la cola; use decrease_key.")
        self.heap.append((key, item))
        self.pos[item] = len(self.heap) - 1
        self._sift_up(len(self.heap) - 1)

    def peek_min(self) -> Tuple[float, Any]:
        if not self.heap:
            raise IndexError("Consulta sobre montículo vacío.")
        return self.heap[0]

    def extract_min(self) -> Tuple[float, Any]:
        if not self.heap:
            raise IndexError("Extracción sobre montículo vacío.")
        top = self.heap[0]
        last = self.heap.pop()
        del self.pos[top[1]]
        if self.heap:
            self.heap[0] = last
            self.pos[last[1]] = 0
            self._sift_down(0)
        return top

    def decrease_key(self, item: Hashable, new_key: float) -> None:
        new_key = self._check_key(new_key)
        idx = self.pos.get(item)
        if idx is None:
            return
        self.comparisons += 1
        if new_key < self.heap[idx][0]:
            self.heap[idx] = (new_key, item)
            self._sift_up(idx)

    # -- rutinas internas ---------------------------------------------------------
    def _sift_up(self, idx: int) -> None:
        d = self.d
        while idx > 0:
            parent = (idx - 1) // d
            self.comparisons += 1
            if self.heap[idx][0] < self.heap[parent][0]:
                self._swap(idx, parent)
                idx = parent
            else:
                break

    def _sift_down(self, idx: int) -> None:
        d = self.d
        n = len(self.heap)
        while True:
            first = d * idx + 1
            if first >= n:
                break
            # Hijo mínimo entre los (a lo sumo) d hijos contiguos.
            smallest = first
            for c in range(first + 1, min(first + d, n)):
                self.comparisons += 1
                if self.heap[c][0] < self.heap[smallest][0]:
                    smallest = c
            self.comparisons += 1
            if self.heap[smallest][0] < self.heap[idx][0]:
                self._swap(idx, smallest)
                idx = smallest
            else:
                break

    def _swap(self, i: int, j: int) -> None:
        self.swaps += 1
        a, b = self.heap[i], self.heap[j]
        self.heap[i], self.heap[j] = b, a
        self.pos[b[1]] = i
        self.pos[a[1]] = j

    # -- verificación e instrumentación ----------------------------------------------
    def check_invariants(self) -> bool:
        d = self.d
        for i in range(1, len(self.heap)):
            if self.heap[i][0] < self.heap[(i - 1) // d][0]:
                return False
        return all(self.pos.get(self.heap[i][1]) == i for i in range(len(self.heap))) \
            and len(self.pos) == len(self.heap)

    def op_stats(self) -> Dict[str, Any]:
        return {"comparisons": self.comparisons, "swaps": self.swaps}

    def get_state(self) -> List[Tuple[Any, float]]:
        return sorted([(item, key) for key, item in self.heap], key=lambda x: str(x[0]))
