#!/usr/bin/env python3
"""
Transform ASV result files to use real CSP tag commit hashes and remove csp from params.

This makes ASV display CSP versions on the x-axis as a connected line (same series, different commits)
rather than separate series with vertical dots.
"""

import json
import re
from pathlib import Path

# Real commit hashes from CSP repo tags (git rev-parse v0.X.Y^{commit})
CSP_VERSION_TO_COMMIT = {
    "0.12.0": "277a3200c601c4c2982b871cfea8ba9085e8640b",
    "0.13.0": "0d92361fcbb127f64a9fda2ed9f490c2d5c2dfd9",
    "0.13.1": "b20dff2379f7731218dff32cdcc02a1d3e0c3190",
    "0.13.2": "bb04478d344396e4dc3fee664bfb1537aa3b0e20",
    "0.14.0": "952de074ddda926bf4a881b5f13423d2a8373aad",
}


def extract_csp_version(filename: str) -> str | None:
    """Extract CSP version from filename like '01ce9cfc-virtualenv-py3.12-csp0.13.0.json'."""
    match = re.search(r"-csp(\d+\.\d+\.\d+)\.json$", filename)
    return match.group(1) if match else None


def transform_result_file(src_path: Path, results_dir: Path) -> Path | None:
    """
    Transform a single result file:
    1. Use real CSP commit hash in filename
    2. Remove csp from env_name (so same machine/python = same series)
    3. Remove csp from params
    4. Keep requirements for install but ASV won't use it for series grouping

    Returns the new path, or None if transformation was skipped.
    """
    filename = src_path.name

    # Skip non-result files
    if filename == "machine.json" or not filename.endswith(".json"):
        return None

    # Extract CSP version
    csp_version = extract_csp_version(filename)
    if not csp_version:
        print(f"  Skipping {filename}: no CSP version found")
        return None

    # Get real commit hash
    real_commit = CSP_VERSION_TO_COMMIT.get(csp_version)
    if not real_commit:
        print(f"  Skipping {filename}: unknown CSP version {csp_version}")
        return None

    real_commit_short = real_commit[:8]

    # Build new filename - remove csp from env name
    # Old: 01ce9cfc-virtualenv-py3.12-csp0.13.0.json
    # New: 0d92361f-virtualenv-py3.12.json
    new_filename = re.sub(r"^[a-f0-9]{8}", real_commit_short, filename)
    new_filename = re.sub(r"-csp\d+\.\d+\.\d+\.json$", ".json", new_filename)

    new_path = src_path.parent / new_filename

    # Read and update JSON content
    with open(src_path) as f:
        data = json.load(f)

    # Update commit_hash
    data["commit_hash"] = real_commit

    # Update env_name - remove csp part
    old_env = data.get("env_name", "")
    data["env_name"] = re.sub(r"-csp\d+\.\d+\.\d+$", "", old_env)

    # Remove csp from params (so ASV doesn't create separate series)
    if "params" in data and "csp" in data["params"]:
        del data["params"]["csp"]

    # Write to new file
    with open(new_path, "w") as f:
        json.dump(data, f, indent=2)

    # Remove old file if different
    if src_path != new_path:
        src_path.unlink()

    print(f"  Transformed: {filename} -> {new_filename}")
    return new_path


def transform_all_results(results_dir: Path) -> int:
    """Transform all result files in the results directory."""
    transformed_count = 0

    for machine_dir in results_dir.iterdir():
        if not machine_dir.is_dir():
            continue

        print(f"Processing machine: {machine_dir.name}")

        for result_file in list(machine_dir.glob("*.json")):
            if result_file.name == "machine.json":
                continue

            new_path = transform_result_file(result_file, results_dir)
            if new_path and new_path != result_file:
                transformed_count += 1

    return transformed_count


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Transform ASV results to use real CSP commit hashes")
    parser.add_argument("--results-dir", type=Path, default=Path("csp_benchmarks/results"), help="Path to results directory")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually modify files")

    args = parser.parse_args()

    if not args.results_dir.exists():
        print(f"Results directory not found: {args.results_dir}")
        return 1

    print(f"Transforming results in: {args.results_dir}")
    print(f"CSP versions mapped: {list(CSP_VERSION_TO_COMMIT.keys())}")
    print()

    if args.dry_run:
        print("DRY RUN - no files will be modified")
        print()

    count = transform_all_results(args.results_dir)
    print(f"\nTransformed {count} files")
    return 0


if __name__ == "__main__":
    exit(main())
