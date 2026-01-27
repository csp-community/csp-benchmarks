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
1. (Optional) Add an SSH key to Hetzner and set `HETZNER_SSH_PRIVATE_KEY` secret

### Running on Hetzner

```bash
# Set your Hetzner token
export HCLOUD_TOKEN="your-token-here"

# Run benchmarks on Hetzner
python -m csp_benchmarks.hetzner.cli run --push

# Clean up any leftover servers
python -m csp_benchmarks.hetzner.cli cleanup
```

### GitHub Actions

Benchmarks run automatically:

- **Weekly**: Full benchmarks on Hetzner Cloud (Sunday 2 AM UTC)
- **On push to main**: Benchmarks for the new commit
- **Manual trigger**: Via workflow_dispatch with custom options

## Configuration

The ASV configuration is in `asv.conf.json`. Key settings:

```json
{
    "project": "csp",
    "repo": "https://github.com/Point72/csp.git",
    "branches": ["main"],
    "pythons": ["3.11"],
    "benchmark_dir": "benchmarks",
    "results_dir": "results"
}
```

## Results

Benchmark results are stored in the `results/` directory and published to GitHub Pages.

View the latest results at: <https://csp-community.github.io/csp-benchmarks/benchmarks/>

## Contributing

1. Add new benchmarks to the `benchmarks/` directory
1. Follow ASV naming conventions (`bench_*.py`, class names ending in `Suite`)
1. Use parameterized benchmarks for testing across different configurations
1. Run `make benchmark-local` to test your benchmarks before submitting
