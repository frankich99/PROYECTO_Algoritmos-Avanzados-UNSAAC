"""
Montículo de Fibonacci (Fredman & Tarjan, 1987). Alternativa del Avance 5.

Insert O(1), Decrease-Key O(1) amortizado, Extract-Min O(log V) amortizado.

Representación: bosque de árboles min-heap cuyas raíces forman una lista
circular doblemente enlazada; cada nodo guarda grado, marca, padre y un hijo
cualquiera (los hermanos también forman lista circular). nodes_map permite
ubicar el nodo de un vértice en O(1) para decrease_key.

Corrección respecto al prototipo de la Unidad 1 (defecto latente): _consolidate
usaba un arreglo de tamaño fijo floor(log2(n+1)) + 7 y, si el grado de un árbol
lo superaba, ese árbol se descartaba en silencio. El grado máximo teórico es
floor(log_phi n) ~ 1.44 log2 n, así que el desborde solo era posible con
n > ~65 000 y árboles de forma extrema; no se observó en las pruebas, pero se
corrigió de forma preventiva: el arreglo se dimensiona con la cota log_phi y
además crece dinámicamente, por lo que ningún árbol puede perderse.
"""
import math
from typing import Any, Dict, Hashable, List, Optional, Tuple

from src.datastructures.base import PriorityQueue

_PHI = (1 + 5 ** 0.5) / 2


class FibNode:
    __slots__ = ("key", "value", "degree", "marked", "parent", "child", "left", "right")

    def __init__(self, key: float, value: Any):
        self.key: float = key
        self.value: Any = value
        self.degree: int = 0
        self.marked: bool = False
        self.parent: Optional["FibNode"] = None
        self.child: Optional["FibNode"] = None
        self.left: "FibNode" = self
        self.right: "FibNode" = self


class FibonacciHeap(PriorityQueue):
    name = "fibonacci_heap"

    def __init__(self) -> None:
        super().__init__()
        self.min_node: Optional[FibNode] = None
        self.total_nodes: int = 0
        self.nodes_map: Dict[Any, FibNode] = {}
        # Contadores estructurales (explican diferencias de costo frente a los heaps de arreglo)
        self.links: int = 0
        self.cuts: int = 0
        self.cascading_cuts: int = 0

    def __len__(self) -> int:
        return self.total_nodes

    def __contains__(self, item: Hashable) -> bool:
        return item in self.nodes_map

    def insert(self, node_id: Hashable, key: float) -> FibNode:
        key = self._check_key(key)
        if node_id in self.nodes_map:
            raise ValueError(f"El nodo {node_id!r} ya está en la cola; use decrease_key.")
        new_node = FibNode(key, node_id)
        self.nodes_map[node_id] = new_node
        if self.min_node is None:
            self.min_node = new_node
        else:
            self._insert_into_root_list(new_node)      # inserción perezosa
            self.comparisons += 1
            if new_node.key < self.min_node.key:
                self.min_node = new_node
        self.total_nodes += 1
        return new_node

    def find_min(self) -> Optional[Tuple[float, Any]]:
        if self.min_node is None:
            return None
        return self.min_node.key, self.min_node.value

    def extract_min(self) -> Tuple[float, Any]:
        z = self.min_node
        if z is None:
            raise IndexError("Extracción sobre montículo vacío.")

        # 1. Promover los hijos de z a la lista de raíces.
        if z.child is not None:
            children = []
            curr = z.child
            while True:
                children.append(curr)
                curr = curr.right
                if curr is z.child:
                    break
            for child in children:
                child.parent = None
                child.marked = False
                self._insert_into_root_list(child)
            z.child = None

        # 2. Retirar z de la lista de raíces.
        self._remove_from_root_list(z)
        del self.nodes_map[z.value]
        self.total_nodes -= 1

        if z.right is z:
            self.min_node = None
        else:
            self.min_node = z.right
            self._consolidate()

        z.left = z.right = z
        return z.key, z.value

    def decrease_key(self, node_id: Hashable, new_key: float) -> None:
        new_key = self._check_key(new_key)
        x = self.nodes_map.get(node_id)
        if x is None:
            return
        self.comparisons += 1
        if new_key >= x.key:
            return  # Solo disminución estricta (no-op en otro caso, igual que los heaps de arreglo)
        x.key = new_key
        y = x.parent
        if y is not None:
            self.comparisons += 1
            if x.key < y.key:
                self._cut(x, y)
                self._cascading_cut(y)
        self.comparisons += 1
        if x.key < self.min_node.key:
            self.min_node = x

    # -- rutinas internas ---------------------------------------------------------
    def _cut(self, x: FibNode, y: FibNode) -> None:
        """Separa x de su padre y y lo lleva a la lista de raíces."""
        self.cuts += 1
        if x.right is x:
            y.child = None
        else:
            x.left.right = x.right
            x.right.left = x.left
            if y.child is x:
                y.child = x.right
        y.degree -= 1
        x.parent = None
        x.marked = False
        self._insert_into_root_list(x)

    def _cascading_cut(self, y: FibNode) -> None:
        """Iterativo para evitar recursión profunda en cadenas largas de marcas."""
        while True:
            z = y.parent
            if z is None:
                return
            if not y.marked:
                y.marked = True
                return
            self.cascading_cuts += 1
            self._cut(y, z)
            y = z

    def _consolidate(self) -> None:
        # Cota teórica del grado máximo: floor(log_phi n) + 1; la lista crece si hiciera falta.
        bound = int(math.log(max(self.total_nodes, 1), _PHI)) + 2
        A: List[Optional[FibNode]] = [None] * bound

        root_list = []
        curr = self.min_node
        while True:
            root_list.append(curr)
            curr = curr.right
            if curr is self.min_node:
                break

        for w in root_list:
            x = w
            d = x.degree
            while True:
                if d >= len(A):
                    A.extend([None] * (d - len(A) + 1))
                y = A[d]
                if y is None:
                    break
                self.comparisons += 1
                if y.key < x.key:
                    x, y = y, x
                self._link(y, x)
                A[d] = None
                d += 1
            A[d] = x

        self.min_node = None
        for node in A:
            if node is None:
                continue
            if self.min_node is None:
                self.min_node = node
                node.left = node.right = node
            else:
                self._insert_into_root_list(node)
                self.comparisons += 1
                if node.key < self.min_node.key:
                    self.min_node = node

    def _link(self, y: FibNode, x: FibNode) -> None:
        """Hace de y un hijo de x (ambos raíces del mismo grado)."""
        self.links += 1
        self._remove_from_root_list(y)
        y.parent = x
        if x.child is None:
            x.child = y
            y.left = y.right = y
        else:
            y.left = x.child
            y.right = x.child.right
            x.child.right.left = y
            x.child.right = y
        x.degree += 1
        y.marked = False

    def _insert_into_root_list(self, node: FibNode) -> None:
        if self.min_node is None:
            self.min_node = node
            node.left = node.right = node
        else:
            node.left = self.min_node
            node.right = self.min_node.right
            self.min_node.right.left = node
            self.min_node.right = node

    @staticmethod
    def _remove_from_root_list(node: FibNode) -> None:
        if node.right is not node:
            node.left.right = node.right
            node.right.left = node.left

    # -- verificación e instrumentación ----------------------------------------------
    def check_invariants(self) -> bool:
        """Orden de heap en cada árbol, grados correctos y conteo total coherente."""
        if self.min_node is None:
            return self.total_nodes == 0 and not self.nodes_map
        seen = 0

        def walk(start: FibNode, parent: Optional[FibNode]) -> bool:
            nonlocal seen
            cur = start
            while True:
                seen += 1
                if cur.parent is not parent:
                    return False
                if parent is not None and cur.key < parent.key:
                    return False
                if parent is None and cur.key < self.min_node.key:
                    return False
                count = 0
                if cur.child is not None:
                    c = cur.child
                    while True:
                        count += 1
                        c = c.right
                        if c is cur.child:
                            break
                    if not walk(cur.child, cur):
                        return False
                if count != cur.degree:
                    return False
                cur = cur.right
                if cur is start:
                    return True

        return walk(self.min_node, None) and seen == self.total_nodes == len(self.nodes_map)

    def op_stats(self) -> Dict[str, Any]:
        return {"comparisons": self.comparisons, "links": self.links,
                "cuts": self.cuts, "cascading_cuts": self.cascading_cuts}

    def get_state(self) -> List[Tuple[Any, float]]:
        return sorted([(node_id, node.key) for node_id, node in self.nodes_map.items()],
                      key=lambda x: str(x[0]))
