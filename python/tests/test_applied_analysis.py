import pytest

from src.benchmarks.applied_analysis import nearest_node, uniformly_scaled
from src.io.graph_io import GraphInstance


@pytest.fixture
def geo_instance():
    return GraphInstance(
        nodes=[1, 2, 3],
        adj={1: [(2, 5.0)], 2: [(3, 2.0)], 3: []},
        coords={1: (-72.0, -13.5), 2: (-71.9, -13.4), 3: (-71.8, -13.3)},
        default_source=1,
        metric="time",
    )


def test_nearest_node_uses_coordinates(geo_instance):
    assert nearest_node(geo_instance, -71.91, -13.41) == 2


def test_uniform_scaling_preserves_topology_and_scales_weights(geo_instance):
    adjusted = uniformly_scaled(geo_instance, 1.2)
    assert adjusted.nodes == geo_instance.nodes
    assert adjusted.adj[1][0] == (2, pytest.approx(6.0))
    assert adjusted.metadata["weather_multiplier"] == 1.2


def test_uniform_scaling_rejects_speedup(geo_instance):
    with pytest.raises(ValueError):
        uniformly_scaled(geo_instance, 0.9)
