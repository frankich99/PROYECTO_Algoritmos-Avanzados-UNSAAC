import pytest

from src.benchmarks.scalability_benchmark import run_canonical_benchmark
from src.generators.instance_generator import benchmark_network
from src.utils.measurement import measure, summarize_samples


def test_measure_reports_robust_statistics_and_samples():
    result = measure(lambda: sum(range(20)), runs=4, warmup=1, keep_samples=True)
    assert result["sample_count"] == 4
    assert len(result["samples_us"]) == 4
    assert result["q1_us"] <= result["median_us"] <= result["q3_us"]


def test_summarize_samples_known_values():
    result = summarize_samples([1, 2, 3, 100])
    assert result["median_us"] == pytest.approx(2.5)
    assert result["min_us"] == 1
    assert result["max_us"] == 100


def test_profiles_have_expected_edge_regimes():
    sparse = benchmark_network(30, "sparse", seed=1)
    dense = benchmark_network(30, "dense", seed=1)
    assert sparse.num_edges == 120
    assert dense.num_edges == round(0.08 * 30 * 29)


def test_small_canonical_benchmark_schema_and_correctness():
    result = run_canonical_benchmark(
        sparse_scales=[8],
        dense_scales=[8],
        runs=1,
        instances_per_size=1,
        seed=7,
        verbose=False,
    )
    assert result["schema_version"] == 2
    assert set(result["profiles"]) == {"sparse", "dense"}
    for profile in result["profiles"].values():
        assert set(profile["data"]) == {"binary_heap", "4ary_heap", "fibonacci_heap"}
        assert sum(profile["winner_counts"].values()) == 1
