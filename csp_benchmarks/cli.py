#!/usr/bin/env python3
"""
CLI for running CSP benchmarks locally.

This allows users who have pip-installed csp-benchmarks to run benchmarks
against their locally installed csp without needing the source repository.

Usage:
    csp-benchmarks list                    # List available benchmarks
    csp-benchmarks run                     # Run all benchmarks
    csp-benchmarks run --suite core        # Run specific suite
    csp-benchmarks run --quick             # Quick mode (fewer params)
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import sys
import time
from typing import Any

# Benchmark modules to discover
BENCHMARK_MODULES = [
    "csp_benchmarks.benchmarks.bench_core",
    "csp_benchmarks.benchmarks.bench_baselib",
    "csp_benchmarks.benchmarks.bench_math",
    "csp_benchmarks.benchmarks.bench_stats",
]


def discover_benchmarks() -> dict[str, dict[str, Any]]:
    """
    Discover all benchmark classes and their time_* methods.

    Returns:
        Dictionary mapping suite names to their benchmark info.
    """
    benchmarks = {}

    for module_name in BENCHMARK_MODULES:
        try:
            module = importlib.import_module(module_name)
        except ImportError as e:
            print(f"Warning: Could not import {module_name}: {e}", file=sys.stderr)
            continue

        # Find all benchmark classes (those with time_* methods)
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if not name.endswith("Suite"):
                continue

            # Get all time_* methods
            time_methods = [m for m in dir(obj) if m.startswith("time_") and callable(getattr(obj, m))]

            if time_methods:
                # Extract suite name from module
                suite_name = module_name.split(".")[-1].replace("bench_", "")
                full_name = f"{suite_name}.{name}"

                benchmarks[full_name] = {
                    "class": obj,
                    "module": module_name,
                    "methods": time_methods,
                    "params": getattr(obj, "params", None),
                    "param_names": getattr(obj, "param_names", None),
                }

    return benchmarks


def list_benchmarks() -> int:
    """List all available benchmarks."""
    benchmarks = discover_benchmarks()

    if not benchmarks:
        print("No benchmarks found.")
        return 1

    print("Available benchmark suites:\n")

    for suite_name, info in sorted(benchmarks.items()):
        print(f"  {suite_name}")
        if info["params"]:
            param_desc = ", ".join(f"{name}={vals}" for name, vals in zip(info["param_names"] or [], _normalize_params(info["params"])))
            print(f"    Parameters: {param_desc}")
        for method in info["methods"]:
            print(f"    - {method}")
        print()

    return 0


def _normalize_params(params: Any) -> list[list]:
    """Normalize params to list of lists."""
    if not params:
        return []
    if isinstance(params[0], (list, tuple)):
        return [list(p) for p in params]
    return [params]


def _get_param_combinations(params: Any, param_names: list[str] | None, quick: bool = False) -> list[dict]:
    """Get all parameter combinations to run."""
    if not params:
        return [{}]

    normalized = _normalize_params(params)
    names = param_names or [f"param{i}" for i in range(len(normalized))]

    # In quick mode, only use first and last value of each param
    if quick:
        normalized = [[p[0], p[-1]] if len(p) > 1 else p for p in normalized]

    # Generate all combinations
    from itertools import product

    combinations = []
    for combo in product(*normalized):
        combinations.append(dict(zip(names, combo)))

    return combinations


def run_benchmark_method(instance: Any, method_name: str, params: dict, num_runs: int = 3) -> dict:
    """
    Run a single benchmark method and return timing results.

    Returns:
        Dictionary with timing statistics.
    """
    method = getattr(instance, method_name)
    param_values = tuple(params.values()) if params else ()

    # Warmup run
    try:
        method(*param_values)
    except Exception as e:
        return {"error": str(e)}

    # Timed runs
    times = []
    for _ in range(num_runs):
        start = time.perf_counter()
        try:
            method(*param_values)
        except Exception as e:
            return {"error": str(e)}
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    return {
        "min": min(times),
        "max": max(times),
        "mean": sum(times) / len(times),
        "runs": num_runs,
    }


def format_time(seconds: float) -> str:
    """Format time in human-readable units."""
    if seconds < 1e-6:
        return f"{seconds * 1e9:.2f} ns"
    elif seconds < 1e-3:
        return f"{seconds * 1e6:.2f} µs"
    elif seconds < 1:
        return f"{seconds * 1e3:.2f} ms"
    else:
        return f"{seconds:.3f} s"


def run_benchmarks(
    suite_filter: str | None = None,
    method_filter: str | None = None,
    quick: bool = False,
    num_runs: int = 3,
    verbose: bool = False,
) -> int:
    """Run benchmarks and print results."""
    benchmarks = discover_benchmarks()

    if not benchmarks:
        print("No benchmarks found.")
        return 1

    # Filter suites
    if suite_filter:
        benchmarks = {k: v for k, v in benchmarks.items() if suite_filter.lower() in k.lower()}
        if not benchmarks:
            print(f"No benchmarks matching '{suite_filter}' found.")
            return 1

    print(f"Running CSP benchmarks (quick={quick}, runs={num_runs})")
    print("=" * 70)

    try:
        import csp

        print(f"CSP version: {getattr(csp, '__version__', 'unknown')}")
    except ImportError:
        print("ERROR: csp is not installed. Install it with: pip install csp")
        return 1

    print()

    total_passed = 0
    total_failed = 0

    for suite_name, info in sorted(benchmarks.items()):
        print(f"\n{suite_name}")
        print("-" * len(suite_name))

        # Get parameter combinations
        param_combos = _get_param_combinations(info["params"], info["param_names"], quick)

        for params in param_combos:
            # Create instance and run setup
            instance = info["class"]()

            if hasattr(instance, "setup"):
                try:
                    param_values = tuple(params.values()) if params else ()
                    instance.setup(*param_values)
                except Exception as e:
                    print(f"  Setup failed for params {params}: {e}")
                    total_failed += 1
                    continue

            param_str = ", ".join(f"{k}={v}" for k, v in params.items()) if params else ""

            # Filter methods if requested
            methods = info["methods"]
            if method_filter:
                methods = [m for m in methods if method_filter.lower() in m.lower()]

            for method_name in methods:
                result = run_benchmark_method(instance, method_name, params, num_runs)

                display_name = method_name.replace("time_", "")
                if param_str:
                    display_name = f"{display_name}({param_str})"

                if "error" in result:
                    print(f"  ✗ {display_name}: ERROR - {result['error']}")
                    total_failed += 1
                else:
                    time_str = format_time(result["mean"])
                    if verbose:
                        print(f"  ✓ {display_name}: {time_str} (min={format_time(result['min'])}, max={format_time(result['max'])})")
                    else:
                        print(f"  ✓ {display_name}: {time_str}")
                    total_passed += 1

    print()
    print("=" * 70)
    print(f"Results: {total_passed} passed, {total_failed} failed")

    return 0 if total_failed == 0 else 1


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run CSP benchmarks locally",
        prog="csp-benchmarks",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # List command
    subparsers.add_parser("list", help="List available benchmarks")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run benchmarks")
    run_parser.add_argument(
        "--suite",
        "-s",
        help="Filter to specific suite (e.g., 'core', 'baselib')",
    )
    run_parser.add_argument(
        "--method",
        "-m",
        help="Filter to specific method name pattern",
    )
    run_parser.add_argument(
        "--quick",
        "-q",
        action="store_true",
        help="Quick mode: run with fewer parameter combinations",
    )
    run_parser.add_argument(
        "--runs",
        "-r",
        type=int,
        default=3,
        help="Number of runs per benchmark (default: 3)",
    )
    run_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed timing info (min/max)",
    )

    args = parser.parse_args()

    if args.command == "list":
        return list_benchmarks()
    elif args.command == "run":
        return run_benchmarks(
            suite_filter=args.suite,
            method_filter=args.method,
            quick=args.quick,
            num_runs=args.runs,
            verbose=args.verbose,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
