"""Configuración global de pytest y fixtures."""
import pytest

@pytest.fixture
def sample_graph():
    return {
        'A': [('B', 1.0), ('C', 4.0)],
        'B': [('A', 1.0), ('C', 2.0), ('D', 5.0)],
        'C': [('A', 4.0), ('B', 2.0), ('D', 1.0)],
        'D': [('B', 5.0), ('C', 1.0)]
    }
