# csp-benchmarks

Performance benchmarks for [csp](https://github.com/Point72/csp) using [airspeed velocity (ASV)](https://asv.readthedocs.io/).

[![Build Status](https://github.com/csp-community/csp-benchmarks/actions/workflows/build.yaml/badge.svg?branch=main&event=push)](https://github.com/csp-community/csp-benchmarks/actions/workflows/build.yaml)
[![Benchmarks](https://github.com/csp-community/csp-benchmarks/actions/workflows/benchmarks.yaml/badge.svg)](https://github.com/csp-community/csp-benchmarks/actions/workflows/benchmarks.yaml)
[![License](https://img.shields.io/github/license/csp-community/csp-benchmarks)](https://github.com/csp-community/csp-benchmarks)

## Overview

This repository contains performance benchmarks for the csp library, designed to:

- Track performance over time across commits
- Detect performance regressions
- Compare different implementations and configurations
- Run on dedicated Hetzner Cloud machines for consistent results

## Benchmark Suites

### Core Benchmarks (bench_core.py)

- **GraphExecutionSuite**: Tests graph execution with varying node counts and tick rates
- **NodeOverheadSuite**: Measures node invocation overhead

### Stats Benchmarks (bench_stats.py)

- **StatsBenchmarkSuite**: Tests statistical functions (median, quantile, rank)
- **StatsScalingSuite**: Tests how stats scale with data size

### Baselib Benchmarks (bench_baselib.py)

- **BaselibSuite**: Tests built-in operations (filter, sample, delay, merge, flatten)
- **CurveSuite**: Tests historical data loading

### Math Benchmarks (bench_math.py)

- **MathSuite**: Tests arithmetic and comparison operations
- **AccumulatorSuite**: Tests accumulating operations (accum, count, diff)

## Quick Start

### Installation

```bash
# Install with development dependencies
pip install -e ".[develop]"

# For Hetzner Cloud integration
pip install -e ".[develop,hetzner]"
```

### Running Benchmarks with the CLI

After installing `csp-benchmarks`, you can run benchmarks locally against your installed csp version:

```bash
# List all available benchmark suites
csp-benchmarks list

# Run all benchmarks
csp-benchmarks run

# Run specific suite (core, baselib, math, stats)
csp-benchmarks run --suite core

# Run specific benchmark method
csp-benchmarks run --method linear_graph

# Quick mode (fewer parameter combinations)
csp-benchmarks run --quick

# Verbose output with min/max timing
csp-benchmarks run --suite baselib --verbose

# Custom number of runs per benchmark
csp-benchmarks run --runs 5
```

CLI Options:

- `--suite, -s`: Filter to specific suite (e.g., 'core', 'baselib')
- `--method, -m`: Filter to specific method name pattern
- `--quick, -q`: Quick mode with fewer parameter combinations
- `--runs, -r`: Number of runs per benchmark (default: 3)
- `--verbose, -v`: Show detailed timing info (min/max)

### Running Benchmarks with Make

```bash
# Run quick benchmarks for the current commit
make benchmark-quick

# Run full benchmarks
make benchmark

# Run using local Python environment (no virtualenv)
make benchmark-local

# View results
make benchmark-view
```

### Using ASV Directly

```bash
# Initialize machine configuration
python -m asv machine --yes

# Run benchmarks for current commit
python -m asv run HEAD^!

# Compare with previous commit
python -m asv compare HEAD~1 HEAD

# Generate and serve HTML report
python -m asv publish
python -m asv preview
```

## Hetzner Cloud Integration

For consistent benchmark results, this repository supports running benchmarks on dedicated Hetzner Cloud servers.

### Setup

1. Create a Hetzner Cloud API token at <https://console.hetzner.cloud/>
1. Set the token as a repository secret: `HCLOUD_TOKEN`
1. Generate an SSH key pair: `ssh-keygen -t ed25519 -f hetzner_key -N ""`
1. Add the **public key** to Hetzner Cloud Console with name `benchmarks`
1. Add the **private key** content as repository secret: `HETZNER_SSH_PRIVATE_KEY`

### Running on Hetzner

```bash
# Set your Hetzner token
export HCLOUD_TOKEN="your-token-here"

# Run benchmarks on Hetzner (SSH key must already exist in Hetzner as 'benchmarks')
python -m csp_benchmarks.hetzner.cli run --ssh-key ~/.ssh/hetzner_key --ssh-key-name benchmarks --push

# Clean up any leftover servers
python -m csp_benchmarks.hetzner.cli cleanup
```

### GitHub Actions

Benchmarks run automatically:

- **On push to main**: Benchmarks for the new commit
- **Manual trigger**: Via workflow_dispatch with custom options

## Results

Benchmark results are stored in the `results/` directory and published to GitHub Pages.

View the latest results at: <https://csp-community.github.io/csp-benchmarks/>

## Contributing

### Adding New Benchmarks

1. Add new benchmarks to the `benchmarks/` directory
1. Follow ASV naming conventions (`bench_*.py`, class names ending in `Suite`)
1. Use parameterized benchmarks for testing across different configurations
1. Run `make benchmark-local` to test your benchmarks before submitting

### Contributing Machine Results

You can contribute benchmark results from your own machine to help the community understand csp performance across different hardware configurations.

#### Step 1: Register Your Machine

Add your machine to `csp_benchmarks/asv-machine.json`. Use a unique, descriptive name:

```json
{
    "timkpaine-framework-13": {
        "arch": "x86_64",
        "cpu": "AMD Ryzen AI 9 HX 370 (24 cores)",
        "machine": "timkpaine-framework-13",
        "num_cpu": "24",
        "os": "Ubuntu 24.04",
        "ram": "64GB"
    }
}
```

Machine naming convention: `username-device-model` (e.g., `timkpaine-framework-13`, `johndoe-mbp-m3`)

#### Step 2: Run Benchmarks

```bash
# Install dependencies
pip install -e ".[develop]"

# Copy machine config to ASV location
cp csp_benchmarks/asv-machine.json ~/.asv-machine.json

# Run benchmarks with your machine name
python -m asv run --config csp_benchmarks/asv.conf.json --machine your-machine-name

# Or use make (runs with local Python)
make benchmark-local
```

#### Step 3: Verify Results

```bash
# Check that results were created
ls csp_benchmarks/results/your-machine-name/

# Preview the results locally
make benchmark-view
```

#### Step 4: Submit a Pull Request

1. Fork the repository
1. Create a branch: `git checkout -b add-machine-results`
1. Commit your changes:
   - `csp_benchmarks/asv-machine.json` (your machine entry)
   - `csp_benchmarks/results/your-machine-name/` (your result files)
1. Open a PR with a description of your hardware

#### Tips for Consistent Results

- Close other applications during benchmarking
- Run on AC power (not battery) for laptops
- Ensure stable CPU frequency (disable turbo boost for more consistent results)
- Run multiple times and verify results are stable
- Include your OS version and Python version in the PR description
