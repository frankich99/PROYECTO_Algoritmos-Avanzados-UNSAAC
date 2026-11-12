"""Comprobaciones de coherencia para el despliegue unificado (Docker / Render)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_runtime_deploy_files_are_present_and_consistent():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    dockerignore = (ROOT / ".dockerignore").read_text(encoding="utf-8")
    requirements = (ROOT / "python" / "requirements-runtime.txt").read_text(encoding="utf-8")
    render_raw = (ROOT / "render.yaml").read_text(encoding="utf-8")

    assert "npm run build" in dockerfile
    assert "uvicorn web_api:app --app-dir python" in dockerfile
    assert "requirements-runtime.txt" in dockerfile
    assert "USER appuser" in dockerfile
    assert ".env" in dockerignore
    assert "web/node_modules" in dockerignore

    for pkg in ("fastapi", "uvicorn", "requests", "networkx"):
        assert pkg in requirements

    assert "runtime: docker" in render_raw
    assert "healthCheckPath: /api/v1/health" in render_raw
    assert "autoDeployTrigger: commit" in render_raw
