"""Configuración global de pytest y fixtures."""
import sys
from pathlib import Path

import pytest

PY_DIR = Path(__file__).resolve().parent.parent
if str(PY_DIR) not in sys.path:
    sys.path.insert(0, str(PY_DIR))

INSTANCES = PY_DIR / "data" / "instances"
QUEUES = ["binary_heap", "4ary_heap", "fibonacci_heap"]


@pytest.fixture
def instances_dir() -> Path:
    return INSTANCES


@pytest.fixture
def sample_graph():
    return {
        'A': [('B', 1.0), ('C', 4.0)],
        'B': [('A', 1.0), ('C', 2.0), ('D', 5.0)],
        'C': [('A', 4.0), ('B', 2.0), ('D', 1.0)],
        'D': [('B', 5.0), ('C', 1.0)]
    }
