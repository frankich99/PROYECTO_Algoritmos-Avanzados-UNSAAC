"""Medición de tiempos reutilizable (benchmark y CLI)."""
import statistics
import time
from typing import Any, Callable, Dict


def measure(fn: Callable[[], Any], runs: int = 5, warmup: int = 1) -> Dict[str, float]:
    """Ejecuta fn warmup + runs veces y devuelve estadísticas en microsegundos."""
    if runs < 1:
        raise ValueError("runs debe ser >= 1")
    for _ in range(max(0, warmup)):
        fn()
    samples = []
    for _ in range(runs):
        t0 = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - t0) * 1e6)
    return {
        "mean_us": round(statistics.fmean(samples), 2),
        "std_us": round(statistics.pstdev(samples), 2) if len(samples) > 1 else 0.0,
        "min_us": round(min(samples), 2),
        "max_us": round(max(samples), 2),
        "runs": runs,
    }
