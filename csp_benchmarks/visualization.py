"""
Transform CSP benchmark results for better ASV visualization.

ASV's default visualization shows git commits on the x-axis. Since we benchmark
different csp library versions (not commits), this module transforms the results
so that ASV treats each csp version as a separate "commit" for visualization.

Usage:
    python -m csp_benchmarks.visualization transform <results_dir>
    python -m csp_benchmarks.visualization report <results_dir>
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# Map csp versions to synthetic commit hashes and dates
# Dates are set to order versions chronologically for proper x-axis ordering
CSP_VERSION_MAP = {
    "0.12.0": {"date": datetime(2024, 1, 1), "order": 1},
    "0.13.0": {"date": datetime(2024, 4, 1), "order": 2},
    "0.13.1": {"date": datetime(2024, 5, 1), "order": 3},
    "0.13.2": {"date": datetime(2024, 6, 1), "order": 4},
    "0.14.0": {"date": datetime(2024, 9, 1), "order": 5},
}


def version_to_commit_hash(version: str) -> str:
    """Generate a deterministic 'commit hash' for a csp version."""
    # Use a hash of the version string to create a fake commit hash
    return hashlib.sha1(f"csp-{version}".encode()).hexdigest()[:8]


def version_to_date(version: str) -> int:
    """Get a synthetic date (ms timestamp) for a csp version."""
    if version in CSP_VERSION_MAP:
        dt = CSP_VERSION_MAP[version]["date"]
    else:
        # For unknown versions, parse version and create date
        parts = re.findall(r"\d+", version)
        if len(parts) >= 2:
            major, minor = int(parts[0]), int(parts[1])
            patch = int(parts[2]) if len(parts) > 2 else 0
            # Create date based on version numbers
            year = 2024 + major - 1
            month = min(12, minor + 1)
            day = min(28, patch + 1)
            dt = datetime(year, month, day)
        else:
            dt = datetime(2024, 1, 1)
    return int(dt.timestamp() * 1000)


def transform_results_for_asv(results_dir: Path | str, output_dir: Path | str | None = None) -> None:
    """
    Transform benchmark results so csp versions appear on x-axis.

    This creates a new results directory where each csp version is treated
    as a separate "commit" rather than a matrix parameter.

    Args:
        results_dir: Source results directory
        output_dir: Output directory (defaults to results_dir + "_transformed")
    """
    results_dir = Path(results_dir)
    output_dir = Path(output_dir) if output_dir else results_dir.parent / (results_dir.name + "_transformed")

    # Clean and create output directory
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    # Copy benchmarks.json
    benchmarks_file = results_dir / "benchmarks.json"
    if benchmarks_file.exists():
        shutil.copy(benchmarks_file, output_dir / "benchmarks.json")

    # Copy README if exists
    readme_file = results_dir / "README.md"
    if readme_file.exists():
        shutil.copy(readme_file, output_dir / "README.md")

    # Process each machine directory
    for machine_dir in results_dir.iterdir():
        if not machine_dir.is_dir():
            continue

        machine_name = machine_dir.name
        out_machine_dir = output_dir / machine_name
        out_machine_dir.mkdir(parents=True, exist_ok=True)

        # Copy machine.json
        machine_file = machine_dir / "machine.json"
        if machine_file.exists():
            shutil.copy(machine_file, out_machine_dir / "machine.json")

        # Process result files
        for result_file in machine_dir.glob("*.json"):
            if result_file.name == "machine.json":
                continue

            result_data = json.loads(result_file.read_text())

            # Extract csp version
            requirements = result_data.get("requirements", {})
            csp_version = requirements.get("csp")

            if csp_version is None or csp_version == "":
                # Already transformed (no csp in requirements) - copy as-is
                shutil.copy(result_file, out_machine_dir / result_file.name)
                continue

            # Create new commit hash based on csp version
            new_commit_hash = version_to_commit_hash(csp_version)

            # Create new date based on csp version (for x-axis ordering)
            new_date = version_to_date(csp_version)

            # Update the result data
            result_data["commit_hash"] = new_commit_hash

            # Set date to order versions properly on x-axis
            result_data["date"] = new_date

            # Remove csp from env_name to avoid duplication
            env_name = result_data.get("env_name", "")
            # Transform "virtualenv-py3.11-csp0.14.0" -> "virtualenv-py3.11"
            new_env_name = re.sub(r"-csp[\d.]+", "", env_name)
            result_data["env_name"] = new_env_name

            # Remove csp from params since it's now the "commit"
            if "params" in result_data and "csp" in result_data["params"]:
                del result_data["params"]["csp"]

            # Clear requirements (csp is now implicit in the commit)
            result_data["requirements"] = {}

            # New filename: {commit_hash}-{env_name}.json
            new_filename = f"{new_commit_hash}-{new_env_name}.json"

            # Write transformed result
            (out_machine_dir / new_filename).write_text(json.dumps(result_data, separators=(",", ":")))

    print(f"Transformed results written to: {output_dir}")


def transform_in_place(results_dir: Path | str) -> None:
    """
    Transform results in place (backup created first).

    Args:
        results_dir: Results directory to transform
    """
    results_dir = Path(results_dir)
    backup_dir = results_dir.parent / (results_dir.name + "_backup")

    # Create backup
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    shutil.copytree(results_dir, backup_dir)
    print(f"Backup created at: {backup_dir}")

    # Transform to temp directory
    temp_dir = results_dir.parent / (results_dir.name + "_temp")
    transform_results_for_asv(results_dir, temp_dir)

    # Replace original with transformed
    shutil.rmtree(results_dir)
    shutil.move(temp_dir, results_dir)
    print(f"Results transformed in place: {results_dir}")


def generate_markdown_report(results_dir: Path | str) -> str:
    """Generate a markdown report comparing csp versions."""
    results_dir = Path(results_dir)

    # Collect results by benchmark and version
    data: dict[str, dict[str, dict[str, list]]] = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    for machine_dir in results_dir.iterdir():
        if not machine_dir.is_dir():
            continue

        machine_name = machine_dir.name

        for result_file in machine_dir.glob("*.json"):
            if result_file.name == "machine.json":
                continue

            result_data = json.loads(result_file.read_text())
            requirements = result_data.get("requirements", {})
            csp_version = requirements.get("csp", "unknown")
            python_version = result_data.get("python", "")

            results = result_data.get("results", {})
            for benchmark_name, benchmark_result in results.items():
                if benchmark_result is None or not isinstance(benchmark_result, list):
                    continue
                if len(benchmark_result) < 1:
                    continue

                values = benchmark_result[0]
                if values is None:
                    continue

                # For simplicity, take mean of parameterized results
                if isinstance(values, list):
                    avg = sum(v for v in values if v is not None) / len([v for v in values if v is not None])
                else:
                    avg = values

                key = f"{machine_name} (py{python_version})"
                data[benchmark_name][key][csp_version].append(avg)

    # Generate markdown
    lines = [
        "# CSP Benchmark Results",
        "",
        "Performance comparison across CSP library versions.",
        "",
    ]

    # Get all versions
    all_versions = set()
    for bench_data in data.values():
        for series_data in bench_data.values():
            all_versions.update(series_data.keys())

    versions = sorted(all_versions, key=lambda v: tuple(int(x) for x in re.findall(r"\d+", v)))

    for benchmark, series_data in sorted(data.items()):
        lines.append(f"## {benchmark}")
        lines.append("")

        # Header
        header = "| Machine | " + " | ".join(f"v{v}" for v in versions) + " |"
        separator = "|" + "|".join(["---"] * (len(versions) + 1)) + "|"
        lines.append(header)
        lines.append(separator)

        # Rows
        for series_name, version_values in sorted(series_data.items()):
            row_values = []
            for v in versions:
                vals = version_values.get(v, [])
                if vals:
                    avg = sum(vals) / len(vals)
                    if avg < 0.001:
                        row_values.append(f"{avg * 1e6:.1f}μs")
                    elif avg < 1:
                        row_values.append(f"{avg * 1000:.2f}ms")
                    else:
                        row_values.append(f"{avg:.3f}s")
                else:
                    row_values.append("-")
            lines.append(f"| {series_name} | " + " | ".join(row_values) + " |")

        lines.append("")

    return "\n".join(lines)


def main():
    import sys

    if len(sys.argv) < 3:
        print("Usage:")
        print("  python -m csp_benchmarks.visualization transform <results_dir> [output_dir]")
        print("  python -m csp_benchmarks.visualization transform-inplace <results_dir>")
        print("  python -m csp_benchmarks.visualization report <results_dir>")
        sys.exit(1)

    command = sys.argv[1]
    results_dir = sys.argv[2]

    if command == "transform":
        output_dir = sys.argv[3] if len(sys.argv) > 3 else None
        transform_results_for_asv(results_dir, output_dir)
    elif command == "transform-inplace":
        transform_in_place(results_dir)
    elif command == "report":
        print(generate_markdown_report(results_dir))
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
