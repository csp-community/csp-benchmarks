"""Import the legacy ASV history using current pytest benchmark identities."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any
from urllib.parse import quote

from benched.asv import import_asv_results, infer_asv_identities
from benched.model import Measurement, Run
from benched.storage import read_runs, save_run

PROJECT_ROOT = Path(__file__).parents[1]


@dataclass(frozen=True)
class BenchmarkTarget:
    module: str
    function: str
    group: str
    parameter_order: tuple[str, ...]
    fixed_parameters: tuple[tuple[str, Any], ...] = ()
    fixed_parameter_ids: tuple[tuple[str, str], ...] = ()


def _target(
    module: str,
    function: str,
    group: str,
    *parameter_order: str,
    fixed_parameters: dict[str, Any] | None = None,
    fixed_parameter_ids: dict[str, str] | None = None,
) -> BenchmarkTarget:
    return BenchmarkTarget(
        module,
        function,
        group,
        parameter_order,
        tuple((fixed_parameters or {}).items()),
        tuple((fixed_parameter_ids or {}).items()),
    )


BENCHMARK_TARGETS = {
    "bench_baselib.BaselibSuite.time_filter": _target(
        "bench_baselib.py", "test_baselib_operation", "baselib", "operation", "num_ticks", fixed_parameters={"operation": "filter"}
    ),
    "bench_baselib.BaselibSuite.time_sample": _target(
        "bench_baselib.py", "test_baselib_operation", "baselib", "operation", "num_ticks", fixed_parameters={"operation": "sample"}
    ),
    "bench_baselib.BaselibSuite.time_delay": _target(
        "bench_baselib.py", "test_baselib_operation", "baselib", "operation", "num_ticks", fixed_parameters={"operation": "delay"}
    ),
    "bench_baselib.BaselibSuite.time_merge": _target(
        "bench_baselib.py", "test_baselib_operation", "baselib", "operation", "num_ticks", fixed_parameters={"operation": "merge"}
    ),
    "bench_baselib.BaselibSuite.time_flatten": _target(
        "bench_baselib.py", "test_baselib_operation", "baselib", "operation", "num_ticks", fixed_parameters={"operation": "flatten"}
    ),
    "bench_baselib.CurveSuite.time_curve_load": _target(
        "bench_baselib.py",
        "test_curve",
        "baselib",
        "processing",
        "num_points",
        fixed_parameters={"processing": False},
        fixed_parameter_ids={"processing": "load"},
    ),
    "bench_baselib.CurveSuite.time_curve_with_processing": _target(
        "bench_baselib.py",
        "test_curve",
        "baselib",
        "processing",
        "num_points",
        fixed_parameters={"processing": True},
        fixed_parameter_ids={"processing": "processing"},
    ),
    "bench_core.GraphExecutionSuite.time_linear_graph": _target("bench_core.py", "test_linear_graph", "core", "num_ticks", "num_nodes"),
    "bench_core.GraphExecutionSuite.time_fan_out_graph": _target("bench_core.py", "test_fan_out_graph", "core", "num_ticks", "num_nodes"),
    "bench_core.GraphExecutionSuite.time_fan_in_graph": _target("bench_core.py", "test_fan_in_graph", "core", "num_ticks", "num_nodes"),
    "bench_core.NodeOverheadSuite.time_empty_node": _target("bench_core.py", "test_empty_node", "core", "num_ticks"),
    "bench_core.NodeOverheadSuite.time_compute_node": _target("bench_core.py", "test_compute_node", "core", "num_ticks"),
    "bench_core.NodeOverheadSuite.time_stateful_node": _target("bench_core.py", "test_stateful_node", "core", "num_ticks"),
    "bench_math.MathSuite.time_abs": _target(
        "bench_math.py", "test_math_operation", "math", "operation", "num_ticks", fixed_parameters={"operation": "abs"}
    ),
    "bench_math.MathSuite.time_arithmetic_chain": _target(
        "bench_math.py", "test_math_operation", "math", "operation", "num_ticks", fixed_parameters={"operation": "arithmetic"}
    ),
    "bench_math.MathSuite.time_comparisons": _target(
        "bench_math.py", "test_math_operation", "math", "operation", "num_ticks", fixed_parameters={"operation": "comparisons"}
    ),
    "bench_math.AccumulatorSuite.time_accum": _target(
        "bench_math.py", "test_accumulator_operation", "math", "operation", "num_ticks", fixed_parameters={"operation": "accum"}
    ),
    "bench_math.AccumulatorSuite.time_count": _target(
        "bench_math.py", "test_accumulator_operation", "math", "operation", "num_ticks", fixed_parameters={"operation": "count"}
    ),
    "bench_math.AccumulatorSuite.time_diff": _target(
        "bench_math.py", "test_accumulator_operation", "math", "operation", "num_ticks", fixed_parameters={"operation": "diff"}
    ),
    "bench_stats.StatsBenchmarkSuite.time_stats": _target(
        "bench_stats.py", "test_stats", "stats", "interval", "function", "array_size", fixed_parameters={"array_size": 100}
    ),
    "bench_stats.StatsScalingSuite.time_mean_scaling": _target(
        "bench_stats.py", "test_stats_scaling", "stats", "function", "array_size", fixed_parameters={"function": "mean"}
    ),
    "bench_stats.StatsScalingSuite.time_stddev_scaling": _target(
        "bench_stats.py", "test_stats_scaling", "stats", "function", "array_size", fixed_parameters={"function": "stddev"}
    ),
}


def _benchmark_id(nodeid: str, parameters: dict[str, Any]) -> str:
    encoded = "&".join(
        f"{quote(name, safe='')}={quote(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True), safe='')}"
        for name, value in sorted(parameters.items())
    )
    return f"{nodeid}|{encoded}"


def map_measurement(measurement: Measurement) -> Measurement:
    target = BENCHMARK_TARGETS.get(measurement.nodeid)
    if target is None:
        raise ValueError(f"legacy benchmark has no pytest identity mapping: {measurement.nodeid}")
    parameters = {**measurement.parameters, **dict(target.fixed_parameters)}
    parameter_ids = dict(target.fixed_parameter_ids)
    parameter_id = "-".join(parameter_ids.get(name, str(parameters[name])) for name in target.parameter_order)
    name = f"{target.function}[{parameter_id}]"
    base_nodeid = f"csp_benchmarks/benchmarks/{target.module}::{target.function}"
    return replace(
        measurement,
        benchmark_id=_benchmark_id(base_nodeid, parameters),
        nodeid=f"{base_nodeid}[{parameter_id}]",
        name=name,
        group=target.group,
        parameter_id=parameter_id,
        parameters=parameters,
    )


def map_run(run: Run) -> Run:
    environment = run.environment
    if environment.python_version.endswith("/.venv/bin/python"):
        environment = replace(environment, python_version="3.11")
    suite = replace(run.suite, repository="https://github.com/csp-community/csp-benchmarks", revision=None)
    subject = replace(run.subject, repository="https://github.com/Point72/csp", revision=run.suite.revision)
    provenance = run.provenance
    if provenance.source_file:
        source_file = Path(provenance.source_file)
        try:
            source_file = source_file.relative_to(PROJECT_ROOT)
        except ValueError:
            source_file = Path(source_file.name)
        provenance = replace(provenance, source_file=source_file.as_posix())
    return replace(
        run,
        suite=suite,
        subject=subject,
        environment=environment,
        measurements=tuple(map_measurement(item) for item in run.measurements),
        provenance=provenance,
    )


def import_history(source: Path, destination: Path, asv_config: Path) -> tuple[int, int]:
    identities = infer_asv_identities(
        source,
        asv_config=asv_config,
        suite_name="csp-benchmarks",
        subject_name="csp",
        subject_version_param="csp",
    )
    summary = import_asv_results(source, str(destination), identities, dry_run=True)
    existing = {stored.run.run_id for stored in read_runs(str(destination))}
    imported = 0
    for run in summary.runs:
        mapped = map_run(run)
        if mapped.run_id in existing:
            continue
        save_run(str(destination), mapped)
        existing.add(mapped.run_id)
        imported += 1
    return imported, len(summary.runs) - imported


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("csp_benchmarks/results"))
    parser.add_argument("--results-dir", type=Path, default=Path("csp_benchmarks/benched-results"))
    parser.add_argument("--asv-config", type=Path, default=Path("csp_benchmarks/asv.conf.json"))
    args = parser.parse_args()
    imported, skipped = import_history(args.source, args.results_dir, args.asv_config)
    print(f"Imported {imported} historical runs; skipped {skipped} existing runs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
