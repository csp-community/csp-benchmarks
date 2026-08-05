"""Tests for native pytest benchmark collection."""

from pathlib import Path

from benched.config import load_config
from benched.runner import collect_benchmarks

PROJECT_ROOT = Path(__file__).parents[2]


def test_collects_all_parameterized_benchmarks():
    config = load_config(PROJECT_ROOT / "pyproject.toml", environ={})

    exit_code, nodeids = collect_benchmarks(config)

    assert exit_code == 0
    assert len(nodeids) == 95
    assert any("bench_core.py::test_linear_graph" in nodeid for nodeid in nodeids)
    assert any("bench_baselib.py::test_curve" in nodeid for nodeid in nodeids)
    assert any("bench_math.py::test_math_operation" in nodeid for nodeid in nodeids)
    assert any("bench_stats.py::test_stats_scaling" in nodeid for nodeid in nodeids)


def test_collection_keeps_csp_subject_separate_from_suite():
    config = load_config(PROJECT_ROOT / "pyproject.toml", environ={})

    assert config.suite.name == "csp-benchmarks"
    assert config.subject.name == "csp"
    assert config.subject.distribution == "csp"
    assert config.benchmark_paths == (PROJECT_ROOT / "csp_benchmarks" / "benchmarks",)
