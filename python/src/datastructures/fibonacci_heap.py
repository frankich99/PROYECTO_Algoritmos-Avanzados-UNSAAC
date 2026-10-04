"""
Montículo de Fibonacci. Insert/Decrease-Key O(1) amortizado, Extract-Min O(log V).
"""
import math
from typing import Optional, Any, Dict, List, Tuple

class FibNode:
    def __init__(self, key: float, value: Any):
        self.key: float = key
        self.value: Any = value
        self.degree: int = 0
        self.marked: bool = False
        self.parent: Optional['FibNode'] = None
        self.child: Optional['FibNode'] = None
        self.left: 'FibNode' = self
        self.right: 'FibNode' = self

class FibonacciHeap:
    def __init__(self):
        self.min_node: Optional[FibNode] = None
        self.total_nodes: int = 0
        self.nodes_map: Dict[Any, FibNode] = {}
        self.comparisons: int = 0

    def is_empty(self) -> bool:
        return self.min_node is None

    def __len__(self) -> int:
        return self.total_nodes

    def insert(self, node_id: Any, key: float) -> FibNode:
        new_node = FibNode(key, node_id)
        self.nodes_map[node_id] = new_node
        if self.min_node is None:
            self.min_node = new_node
        else:
            self._insert_into_root_list(new_node)
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
        
        # Agregar todos los hijos de z a la lista de raíces
        if z.child is not None:
            children = []
            curr = z.child
            while True:
                children.append(curr)
                curr = curr.right
                if curr == z.child:
                    break
            for child in children:
                child.parent = None
                self._insert_into_root_list(child)
        
        # Remover z de la lista de raíces
        self._remove_from_root_list(z)
        del self.nodes_map[z.value]
        self.total_nodes -= 1

        if z == z.right:
            self.min_node = None
        else:
            self.min_node = z.right
            self._consolidate()

        return z.key, z.value

    def decrease_key(self, node_id: Any, new_key: float) -> None:
        if node_id not in self.nodes_map:
            return
        x = self.nodes_map[node_id]
        self.comparisons += 1
        if new_key > x.key:
            return  # Solo disminución permitida
        x.key = new_key
        y = x.parent
        if y is not None:
            self.comparisons += 1
            if x.key < y.key:
                self._cut(x, y)
                self._cascading_cut(y)
        self.comparisons += 1
        if self.min_node is not None and x.key < self.min_node.key:
            self.min_node = x

    def _cut(self, x: FibNode, y: FibNode) -> None:
        # Remover x de la lista de hijos de y
        if x.right == x:
            y.child = None
        else:
            x.left.right = x.right
            x.right.left = x.left
            if y.child == x:
                y.child = x.right
        y.degree -= 1
        x.parent = None
        x.marked = False
        self._insert_into_root_list(x)

    def _cascading_cut(self, y: FibNode) -> None:
        z = y.parent
        if z is not None:
            if not y.marked:
                y.marked = True
            else:
                self._cut(y, z)
                self._cascading_cut(z)

    def _consolidate(self) -> None:
        max_deg = int(math.log2(self.total_nodes + 1)) + 2
        A: List[Optional[FibNode]] = [None] * (max_deg + 5)

        root_list = []
        curr = self.min_node
        if curr is not None:
            while True:
                root_list.append(curr)
                curr = curr.right
                if curr == self.min_node:
                    break

        for w in root_list:
            x = w
            d = x.degree
            while d < len(A) and A[d] is not None:
                y = A[d]
                self.comparisons += 1
                if x.key > y.key:
                    x, y = y, x
                self._link(y, x)
                A[d] = None
                d += 1
            if d < len(A):
                A[d] = x

        self.min_node = None
        for i in range(len(A)):
            if A[i] is not None:
                node = A[i]
                if self.min_node is None:
                    self.min_node = node
                    node.left = node
                    node.right = node
                else:
                    self._insert_into_root_list(node)
                    self.comparisons += 1
                    if node.key < self.min_node.key:
                        self.min_node = node

    def _link(self, y: FibNode, x: FibNode) -> None:
        self._remove_from_root_list(y)
        y.parent = x
        if x.child is None:
            x.child = y
            y.left = y
            y.right = y
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
            node.left = node
            node.right = node
        else:
            node.left = self.min_node
            node.right = self.min_node.right
            self.min_node.right.left = node
            self.min_node.right = node

    def _remove_from_root_list(self, node: FibNode) -> None:
        if node.right == node:
            pass
        else:
            node.left.right = node.right
            node.right.left = node.left

    def get_state(self) -> List[Tuple[Any, float]]:
        return sorted([(node_id, node.key) for node_id, node in self.nodes_map.items()], key=lambda x: str(x[0]))
