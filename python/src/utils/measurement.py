"""Medición reproducible con reloj monotónico y estadísticas robustas."""
import gc
import statistics
import time
from typing import Any, Callable, Dict, Iterable, List


def summarize_samples(samples_us: Iterable[float]) -> Dict[str, float]:
    samples = [float(value) for value in samples_us]
    if not samples:
        raise ValueError("Se requiere al menos una muestra.")
    median = statistics.median(samples)
    if len(samples) > 1:
        q1, _q2, q3 = statistics.quantiles(samples, n=4, method="inclusive")
    else:
        q1 = q3 = samples[0]
    deviations = [abs(value - median) for value in samples]
    mean = statistics.fmean(samples)
    std = statistics.pstdev(samples) if len(samples) > 1 else 0.0
    return {
        "mean_us": round(mean, 3),
        "median_us": round(median, 3),
        "std_us": round(std, 3),
        "q1_us": round(q1, 3),
        "q3_us": round(q3, 3),
        "iqr_us": round(q3 - q1, 3),
        "mad_us": round(statistics.median(deviations), 3),
        "min_us": round(min(samples), 3),
        "max_us": round(max(samples), 3),
        "cv_pct": round(100.0 * std / mean, 3) if mean else 0.0,
        "sample_count": len(samples),
    }


def measure(
    fn: Callable[[], Any],
    runs: int = 5,
    warmup: int = 1,
    disable_gc: bool = True,
    keep_samples: bool = False,
) -> Dict[str, Any]:
    """Mide ``fn`` con ``perf_counter_ns``; GC queda fuera de cada muestra."""
    if runs < 1:
        raise ValueError("runs debe ser >= 1")
    for _ in range(max(0, warmup)):
        fn()
    samples: List[float] = []
    for _ in range(runs):
        was_enabled = gc.isenabled()
        if disable_gc:
            gc.collect()
            gc.disable()
        try:
            started_ns = time.perf_counter_ns()
            fn()
            elapsed_ns = time.perf_counter_ns() - started_ns
        finally:
            if disable_gc and was_enabled:
                gc.enable()
        samples.append(elapsed_ns / 1_000.0)
    result: Dict[str, Any] = {**summarize_samples(samples), "runs": runs, "warmup": max(0, warmup)}
    if keep_samples:
        result["samples_us"] = [round(value, 3) for value in samples]
    return result
