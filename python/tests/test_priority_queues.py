"""
Pruebas del contrato común de las tres colas de prioridad (patrón AAA).

Cada prueba se ejecuta sobre las tres estructuras (parametrize), lo que
garantiza que todas cumplen la misma interfaz que usa Dijkstra.
"""
import heapq
import random

import pytest

from src.datastructures.d_ary_heap import DAryHeap
from src.datastructures.fibonacci_heap import FibonacciHeap
from src.datastructures.indexed_min_heap import IndexedMinHeap
from src.datastructures.registry import create_queue, normalize_queue_name
from tests.conftest import QUEUES


# ---------------------------------------------------------------- básicos
@pytest.mark.parametrize("q", QUEUES)
def test_extracts_in_ascending_order(q):
    heap = create_queue(q)
    for item, key in [("D", 4.0), ("A", 1.0), ("C", 3.0), ("B", 2.0), ("E", 5.0)]:
        heap.insert(item, key)
    out = [heap.extract_min() for _ in range(5)]
    assert out == [(1.0, "A"), (2.0, "B"), (3.0, "C"), (4.0, "D"), (5.0, "E")]
    assert heap.is_empty()


@pytest.mark.parametrize("q", QUEUES)
def test_decrease_key_moves_item_to_front(q):
    heap = create_queue(q)
    for item, key in [("B", 180.0), ("C", 450.0), ("D", 400.0)]:
        heap.insert(item, key)
    heap.decrease_key("C", 150.0)
    assert heap.extract_min() == (150.0, "C")
    assert len(heap) == 2


@pytest.mark.parametrize("q", QUEUES)
def test_decrease_from_infinity(q):
    heap = create_queue(q)
    for item in "ABCD":
        heap.insert(item, float("inf"))
    heap.decrease_key("C", 7.0)
    heap.decrease_key("A", 9.0)
    assert heap.extract_min() == (7.0, "C")
    assert heap.extract_min() == (9.0, "A")


# ---------------------------------------------------------------- límite
@pytest.mark.parametrize("q", QUEUES)
def test_empty_extraction_raises(q):
    heap = create_queue(q)
    assert heap.is_empty()
    with pytest.raises(IndexError):
        heap.extract_min()


@pytest.mark.parametrize("q", QUEUES)
def test_single_element(q):
    heap = create_queue(q)
    heap.insert("X", 0.0)
    assert "X" in heap and len(heap) == 1
    assert heap.extract_min() == (0.0, "X")
    assert "X" not in heap and heap.is_empty()


@pytest.mark.parametrize("q", QUEUES)
def test_increase_attempt_is_noop(q):
    heap = create_queue(q)
    heap.insert("A", 50.0)
    heap.decrease_key("A", 100.0)
    assert heap.extract_min() == (50.0, "A")


@pytest.mark.parametrize("q", QUEUES)
def test_decrease_key_of_absent_item_is_noop(q):
    heap = create_queue(q)
    heap.insert("A", 1.0)
    heap.extract_min()
    heap.decrease_key("A", 0.0)       # ya extraído: Dijkstra nunca lo reinserta
    heap.decrease_key("ZZZ", 0.0)     # nunca existió
    assert heap.is_empty()


@pytest.mark.parametrize("q", QUEUES)
def test_equal_keys_all_extracted(q):
    heap = create_queue(q)
    for i in range(20):
        heap.insert(i, 1.0)
    got = sorted(heap.extract_min()[1] for _ in range(20))
    assert got == list(range(20))


# ---------------------------------------------------------------- adversos
@pytest.mark.parametrize("q", QUEUES)
def test_duplicate_insert_rejected(q):
    heap = create_queue(q)
    heap.insert("A", 1.0)
    with pytest.raises(ValueError):
        heap.insert("A", 2.0)


@pytest.mark.parametrize("q", QUEUES)
@pytest.mark.parametrize("bad", [float("nan"), "10", None, True])
def test_invalid_keys_rejected(q, bad):
    heap = create_queue(q)
    with pytest.raises((ValueError, TypeError)):
        heap.insert("A", bad)


def test_dary_rejects_invalid_arity():
    for d in (0, 1, -3, 2.5, True):
        with pytest.raises(ValueError):
            DAryHeap(d=d)


def test_unknown_queue_name():
    with pytest.raises(ValueError):
        create_queue("pairing_heap")
    assert normalize_queue_name("FIB") == "fibonacci_heap"
    assert normalize_queue_name("4ary") == "4ary_heap"


# ---------------------------------------------------------------- estrés vs referencia
def _random_ops(heap_factory, seed: int, n_ops: int = 3000):
    """Secuencia aleatoria de insert/decrease/extract comparada contra un modelo con heapq."""
    rng = random.Random(seed)
    heap = heap_factory()
    model = {}               # item -> clave actual
    ref = []                 # heapq con entradas perezosas
    next_id = 0
    for _ in range(n_ops):
        op = rng.random()
        if op < 0.40 or not model:
            key = float(rng.randint(0, 1000))
            heap.insert(next_id, key)
            model[next_id] = key
            heapq.heappush(ref, (key, next_id))
            next_id += 1
        elif op < 0.75:
            item = rng.choice(list(model))
            new_key = model[item] - rng.randint(0, 300)
            heap.decrease_key(item, new_key)
            if new_key < model[item]:
                model[item] = new_key
                heapq.heappush(ref, (new_key, item))
        else:
            k, item = heap.extract_min()
            while True:          # mínimo vigente del modelo
                rk, ritem = ref[0]
                if ritem in model and model[ritem] == rk:
                    break
                heapq.heappop(ref)
            assert k == rk, f"clave extraída {k} != mínimo esperado {rk}"
            assert model[item] == k
            del model[item]
        assert len(heap) == len(model)
        if hasattr(heap, "check_invariants") and rng.random() < 0.05:
            assert heap.check_invariants()
    while model:
        k, item = heap.extract_min()
        assert model.pop(item) == k
        assert all(k <= v for v in model.values())
    assert heap.is_empty()


@pytest.mark.parametrize("factory", [IndexedMinHeap, lambda: DAryHeap(2), lambda: DAryHeap(3),
                                     lambda: DAryHeap(4), lambda: DAryHeap(8), FibonacciHeap],
                         ids=["binary", "dary2", "dary3", "dary4", "dary8", "fibonacci"])
@pytest.mark.parametrize("seed", [1, 2, 3])
def test_random_operations_match_reference(factory, seed):
    _random_ops(factory, seed)


def test_fibonacci_exercises_cascading_cuts():
    # Forzar árboles profundos (muchas extracciones) y luego muchos decrease-key.
    heap = FibonacciHeap()
    n = 512
    for i in range(n):
        heap.insert(i, float(i + n))
    heap.insert(-1, 0.0)
    heap.extract_min()                     # consolida en árboles binomiales grandes
    for i in range(n - 1, 0, -1):
        heap.decrease_key(i, float(i) - n)  # cortes y cortes en cascada
    assert heap.cuts > 0 and heap.cascading_cuts > 0
    assert heap.check_invariants()
    keys = [heap.extract_min()[0] for _ in range(n)]
    assert keys == sorted(keys)


def test_fibonacci_large_consolidation_loses_nothing():
    # Consolidación masiva: ningún elemento se pierde ni se desordena. (El defecto latente de la
    # Unidad 1, arreglo de grados de tamaño fijo, solo se manifestaría con n > ~65 000 y árboles
    # de forma extrema; se corrigió por diseño y esta prueba cubre el caso típico a gran escala.)
    heap = FibonacciHeap()
    n = 20000
    for i in range(n):
        heap.insert(i, float(i))
    extracted = [heap.extract_min()[1] for _ in range(n)]
    assert extracted == list(range(n))
