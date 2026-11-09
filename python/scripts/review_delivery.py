"""Genera evidencia actual de pruebas, piloto y Git sin reescribir el banco histórico."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import hashlib
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "python"))

from src.benchmarks.scalability_benchmark import run_canonical_benchmark
from src.generators.instance_generator import benchmark_network

REPO = "https://github.com/frankich99/PROYECTO_Algoritmos-Avanzados-UNSAAC"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, encoding="utf-8").strip()


def python_summary(path):
    modules = {}
    root = ET.parse(path).getroot()
    cases = root.findall(".//testcase")
    if not cases:
        raise ValueError("El XML no contiene pruebas ejecutadas.")
    for case in cases:
        name = case.get("classname", "sin_modulo")
        entry = modules.setdefault(name, {"name": name, "passed": 0, "failed": 0, "skipped": 0})
        status = "failed" if case.find("failure") is not None or case.find("error") is not None else "skipped" if case.find("skipped") is not None else "passed"
        entry[status] += 1
    return {**{key: sum(row[key] for row in modules.values()) for key in ("passed", "failed", "skipped")},
            "seconds": round(sum(float(suite.get("time", "0")) for suite in root.findall(".//testsuite")), 3),
            "modules": sorted(modules.values(), key=lambda row: row["name"])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python-report", type=Path, default=ROOT / "python/test-results/junit.xml")
    parser.add_argument("--web-report", type=Path, default=ROOT / "web/test-results/results.json")
    parser.add_argument("--github-check", action="store_true", help="Comprueba la rama remota vía GitHub, sin credenciales.")
    args = parser.parse_args()
    python_tests = python_summary(args.python_report)
    web_results = json.loads(args.web_report.read_text(encoding="utf-8"))
    web_tests = {"passed": web_results["numPassedTests"], "failed": web_results["numFailedTests"], "total": web_results["numTotalTests"]}
    if python_tests["failed"] or web_tests["failed"] or not web_tests["total"] or not web_results.get("success"):
        raise ValueError("No se publica una evidencia exitosa cuando la ejecución tiene fallos o no tiene pruebas.")
    pilot = run_canonical_benchmark(sparse_scales=[30, 100], dense_scales=[30, 60], runs=5, instances_per_size=2, seed=12345, verbose=False)
    pilot["kind"] = "second_delivery_review_pilot"
    pilot["protocol"]["timing_scope"] = "Solo núcleo, sin validación, I/O, trazas ni reconstrucción de caminos"
    rows = []
    for profile, result in pilot["profiles"].items():
        for queue, measurements in result["data"].items():
            for row in measurements:
                if len(row["samples_us"]) != 10 or not row["q1_us"] <= row["median_us"] <= row["q3_us"]:
                    raise ValueError("Muestras o cuartiles inconsistentes.")
                for seed in row["instance_seeds"]:
                    if benchmark_network(row["nodes"], profile, seed).adj != benchmark_network(row["nodes"], profile, seed).adj:
                        raise ValueError("La semilla no reproduce el grafo.")
                rows.append({"profile": profile, "queue": queue, **{key: row[key] for key in
                    ("nodes", "edges", "median_us", "q1_us", "q3_us", "sample_count", "instance_seeds")}})
    commits = []
    branch_map = {
        "Grupo 5 - Algoritmos Avanzados": "ramaFRANKI",
        "Noe Choquenaira": "ramaFRANKI",
        "ramaFRANKI": "ramaFRANKI",
        "Aldo Yaranga": "ramaAldo",
        "ramaAldo": "ramaAldo",
        "Yeni Porroa": "ramaYeni",
        "ramaYeni": "ramaYeni",
        "Romario Quispe": "RamaRomario",
        "RamaRomario": "RamaRomario",
    }
    for line in git("log", "--format=%H%x1f%aI%x1f%an%x1f%s", "HEAD").splitlines():
        sha, date, author, subject = line.split("\x1f", 3)
        author = branch_map.get(author, author)
        commits.append({"hash": sha, "date": date, "author": author, "subject": subject})
    branch = git("branch", "--show-current")
    remote_head = remote_date = None
    if args.github_check:
        import requests
        from urllib.parse import quote
        response = requests.get(f"https://api.github.com/repos/frankich99/PROYECTO_Algoritmos-Avanzados-UNSAAC/commits/{quote(branch, safe='')}", timeout=20)
        response.raise_for_status()
        remote_head = response.json()["sha"]
        remote_date = datetime.now(timezone.utc).isoformat()
    report = {
        "schema_version": 1, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "git": {"head": git("rev-parse", "HEAD"), "branch": branch, "dirty": bool(git("status", "--porcelain")),
                "github_head": remote_head, "github_checked_at": remote_date},
        "tests": {"python": python_tests, "web": web_tests},
        "pilot": {"generated_at_utc": pilot["generated_at_utc"], "protocol": pilot["protocol"], "environment": pilot["environment"],
                  "rows": sorted(rows, key=lambda row: (row["profile"], row["nodes"], row["queue"]))},
        "contributors": [{"name": name, "count": count} for name, count in Counter(commit["author"] for commit in commits).most_common()],
        "commits": commits,
        "source_sha256": {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                          for folder in ("python/src", "python/tests", "web/src", "web/tests")
                          for path in sorted((ROOT / folder).rglob("*")) if path.suffix in (".py", ".ts", ".tsx", ".css")},
    }
    bitacora = ["# Bitácora de aportes verificables en GitHub", "", f"Generada: {report['generated_at_utc']}.",
                f"Rama `{branch}`; base `{report['git']['head']}`. Incluye solo commits alcanzables desde esa base.",
                f"HEAD remoto consultado: `{remote_head or 'no consultado'}`.", "",
                "La autoría de un commit no prueba dedicación, aprendizaje individual ni asistencia a reuniones. Los cambios se agrupan por rama de trabajo correspondiente. Las fechas son las declaradas en Git, no actas ni fechas de recepción.", "",
                "## Ramas registradas", "", "| Rama | Commits |", "| --- | ---: |"]
    bitacora += [f"| {row['name']} | {row['count']} |" for row in report["contributors"]]
    bitacora += ["", "## Cronología", "", "| Fecha del autor | Rama | Cambio | Evidencia |", "| --- | --- | --- | --- |"]
    bitacora += [f"| {c['date']} | {c['author']} | {c['subject'].replace('|', '/')} | [{c['hash'][:7]}]({REPO}/commit/{c['hash']}) |" for c in commits]
    bitacora += ["", "## Correcciones de esta revisión (aún sin commit)", "", "- Se retiran afirmaciones de cobertura al 100 %, superioridad universal y reducción fija de A*.",
                 "- Se rechazan valores no finitos en el modelo; la calibración de A* deja de almacenar O(E) cocientes.",
                 "- Se añaden referencia exhaustiva, flujo HTTP con semillas y pruebas de componentes web.",
                 "- Se separan pruebas, piloto de revisión, banco histórico y contribuciones de Git.",
                 "- Pendientes: actas y reflexiones individuales auténticas, instalación limpia, PDF recompilado y defensa."]
    bitacora_text = "\n".join(bitacora) + "\n"
    (ROOT / "docs/BITACORA_GITHUB.md").write_text(bitacora_text, encoding="utf-8")
    for folder in (ROOT / "python/data/processed", ROOT / "web/public/data", ROOT / "data"):
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "delivery_evidence.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        (folder / "delivery_pilot.json").write_text(json.dumps(pilot, ensure_ascii=False, indent=2), encoding="utf-8")
    for folder in (ROOT / "web/public/data", ROOT / "data"):
        (folder / "bitacora_github.md").write_text(bitacora_text, encoding="utf-8")
        (folder / "segunda_entrega.md").write_text((ROOT / "docs/SEGUNDA_ENTREGA.md").read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Evidencia guardada: {python_tests['passed']} Python, {web_tests['passed']} web; {sum(row['sample_count'] for row in rows)} tiempos piloto; {len(commits)} commits.")


if __name__ == "__main__":
    main()
