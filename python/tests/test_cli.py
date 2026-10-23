"""
Pruebas de integración de la interfaz común (comandos de main.py).
"""
import json

import pytest

from src.cli import cmd_menu, main as cli


def test_list(capsys):
    assert cli(["list"]) == 0
    out = capsys.readouterr().out
    for name in ("binary_heap", "4ary_heap", "fibonacci_heap", "bellman_ford"):
        assert name in out


def test_run_default_cusco(capsys):
    assert cli(["run"]) == 0
    out = capsys.readouterr().out
    assert "A -> B -> D -> E" in out and "Verificación: OK" in out


@pytest.mark.parametrize("q", ["binary", "4ary", "fib", "bellman_ford", "all", "binary,fib"])
def test_run_each_method(q, instances_dir, capsys):
    assert cli(["run", "-i", str(instances_dir / "clrs_24_6.txt"), "-q", q]) == 0
    assert "Verificación: OK" in capsys.readouterr().out


def test_run_target_and_trace(capsys):
    assert cli(["run", "--metric", "distance", "-t", "F", "--trace"]) == 0
    out = capsys.readouterr().out
    assert "Ruta A -> F: A -> C -> F" in out and "k= 1 extrae A" in out


def test_inline_instance_proposed_in_session(capsys):
    assert cli(["run", "--inline", "P Q 2; Q R 2; P R 5", "-s", "P", "-q", "all"]) == 0
    out = capsys.readouterr().out
    assert "P -> Q -> R" in out and "EQUIVALENTES" in out


def test_compare_with_ties(instances_dir, capsys):
    assert cli(["compare", "-i", str(instances_dir / "empates_grid_3x3.json")]) == 0
    out = capsys.readouterr().out
    assert "EQUIVALENTES" in out and "mismo costo" in out


@pytest.mark.parametrize("argv", [
    ["run", "-i", "no_existe.json"],
    ["run", "-s", "ZZ"],
    ["run", "-q", "pairing"],
    ["run", "--inline", "A B -1"],
    ["run", "--inline", "A B"],
    ["run", "-t", "QQ"],
])
def test_invalid_inputs_exit_code_2(argv, capsys):
    assert cli(argv) == 2
    assert "[ERROR]" in capsys.readouterr().err


def test_negative_cycle_exit_code(instances_dir, capsys):
    assert cli(["run", "-i", str(instances_dir / "invalidas" / "ciclo_negativo.txt"), "-q", "bf"]) == 2


def test_generate_run_and_verify_roundtrip(tmp_path, capsys):
    inst = tmp_path / "gen.json"
    res = tmp_path / "res.json"
    assert cli(["generate", "--type", "random", "--nodes", "40", "--seed", "3", "-o", str(inst)]) == 0
    assert cli(["run", "-i", str(inst), "-q", "fibonacci", "-o", str(res)]) == 0
    assert cli(["verify", "-i", str(inst), "-r", str(res)]) == 0
    # Manipular el resultado: el verificador debe rechazarlo
    data = json.loads(res.read_text())
    key = next(k for k, v in data["distances"].items() if v)
    data["distances"][key] = data["distances"][key] * 0.5
    res.write_text(json.dumps(data))
    assert cli(["verify", "-i", str(inst), "-r", str(res)]) == 1


def test_generate_grid_types(tmp_path):
    assert cli(["generate", "--type", "grid", "--rows", "2", "--cols", "3", "-o", str(tmp_path / "g.json")]) == 0
    assert cli(["generate", "--type", "road-grid", "-o", str(tmp_path / "r.json")]) == 0
    assert cli(["generate", "--type", "grid", "--rows", "0", "-o", str(tmp_path / "x.json")]) == 2


def test_compare_output_report(tmp_path, capsys):
    out = tmp_path / "rep.json"
    assert cli(["compare", "--metric", "distance", "-o", str(out)]) == 0
    rep = json.loads(out.read_text())
    assert rep["comparison"]["distances_equal"] and set(rep["results"]) >= {"binary_heap", "bellman_ford"}


def test_benchmark_small(tmp_path, capsys):
    assert cli(["benchmark", "--scales", "10", "20", "--runs", "1", "--output-dir", str(tmp_path)]) == 0
    assert (tmp_path / "benchmark_results.json").exists()
    assert (tmp_path / "tabla_benchmark_escalabilidad.tex").exists()


def test_menu_scripted(capsys):
    answers = iter(["4", "A B 1; B C 1; A C 5", "6", "A", "all", "n", "7", "", "4", "A B x", "9", "0"])
    assert cmd_menu(None, input_fn=lambda _p: next(answers)) == 0
    out = capsys.readouterr().out
    assert "A -> B -> C" in out and "[ERROR] Entrada inválida" in out and "Opción no válida" in out

def test_graphviz_export(tmp_path, capsys):
    dot_file = tmp_path / "test_graph.dot"
    assert cli(["graphviz", "-o", str(dot_file), "-t", "E"]) == 0
    assert dot_file.exists()
    content = dot_file.read_text(encoding="utf-8")
    assert "digraph CuscoRoadNetwork" in content
    assert "A -> B" in content

def test_astar_cli(capsys):
    assert cli(["astar", "-t", "E"]) == 0
    out = capsys.readouterr().out
    assert "A* Heurístico" in out
    assert "Optimalidad: GARANTIZADA" in out
