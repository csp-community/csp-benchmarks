"""Tests for importing CSP's legacy ASV history."""

from dataclasses import replace
from pathlib import Path

from benched.asv import import_asv_results, infer_asv_identities
from benched.config import load_config
from benched.runner import collect_benchmarks
from benched.storage import read_runs

from csp_benchmarks.import_asv_history import import_history, map_measurement, map_run

PROJECT_ROOT = Path(__file__).parents[2]
ASV_RESULTS = PROJECT_ROOT / "csp_benchmarks" / "results"
ASV_CONFIG = PROJECT_ROOT / "csp_benchmarks" / "asv.conf.json"


def _legacy_runs(tmp_path):
    identities = infer_asv_identities(
        ASV_RESULTS,
        asv_config=ASV_CONFIG,
        suite_name="csp-benchmarks",
        subject_name="csp",
        subject_version_param="csp",
    )
    return import_asv_results(ASV_RESULTS, str(tmp_path), identities, dry_run=True).runs


def test_maps_legacy_measurement_to_current_pytest_identity(tmp_path):
    measurement = next(
        item
        for run in _legacy_runs(tmp_path)
        for item in run.measurements
        if item.nodeid == "bench_baselib.BaselibSuite.time_delay" and item.parameters == {"num_ticks": 1000}
    )

    mapped = map_measurement(measurement)

    assert mapped.benchmark_id == ("csp_benchmarks/benchmarks/bench_baselib.py::test_baselib_operation|num_ticks=1000&operation=%22delay%22")
    assert mapped.nodeid == "csp_benchmarks/benchmarks/bench_baselib.py::test_baselib_operation[delay-1000]"
    assert mapped.name == "test_baselib_operation[delay-1000]"
    assert mapped.group == "baselib"
    assert mapped.parameters == {"num_ticks": 1000, "operation": "delay"}


def test_maps_every_legacy_case_to_95_current_identities(tmp_path):
    mapped = [map_measurement(item) for run in _legacy_runs(tmp_path) for item in run.measurements]
    config = load_config(PROJECT_ROOT / "pyproject.toml", environ={})
    exit_code, current_nodeids = collect_benchmarks(config)

    assert exit_code == 0
    assert len({item.benchmark_id for item in mapped}) == 95
    assert {item.nodeid for item in mapped} == set(current_nodeids)


def test_normalizes_python_executable_recorded_by_asv(tmp_path):
    run = next(run for run in _legacy_runs(tmp_path) if run.environment.python_version.endswith("/.venv/bin/python"))

    mapped = map_run(run)

    assert mapped.environment.python_version == "3.11"
    assert mapped.provenance.source_file.startswith("csp_benchmarks/results/")
    assert mapped.suite.revision is None
    assert mapped.subject.revision == run.suite.revision


def test_rejects_unmapped_legacy_benchmark(tmp_path):
    measurement = _legacy_runs(tmp_path)[0].measurements[0]

    try:
        map_measurement(replace(measurement, nodeid="unknown.time_case"))
    except ValueError as error:
        assert str(error) == "legacy benchmark has no pytest identity mapping: unknown.time_case"
    else:
        raise AssertionError("missing mapping was accepted")


def test_imports_history_once(tmp_path):
    destination = tmp_path / "results"

    first = import_history(ASV_RESULTS, destination, ASV_CONFIG)
    second = import_history(ASV_RESULTS, destination, ASV_CONFIG)
    runs = read_runs(str(destination))

    assert first == (42, 0)
    assert second == (0, 42)
    assert len(runs) == 42
    assert len({measurement.benchmark_id for stored in runs for measurement in stored.run.measurements}) == 95
