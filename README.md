# csp-benchmarks

Performance benchmarks for [CSP](https://github.com/Point72/csp), measured with
pytest-benchmark and tracked with [Benched](https://github.com/1kbgz/benched).

[![Build Status](https://github.com/csp-community/csp-benchmarks/actions/workflows/build.yaml/badge.svg?branch=main&event=push)](https://github.com/csp-community/csp-benchmarks/actions/workflows/build.yaml)
[![Benchmarks](https://github.com/csp-community/csp-benchmarks/actions/workflows/benchmarks.yaml/badge.svg)](https://github.com/csp-community/csp-benchmarks/actions/workflows/benchmarks.yaml)
[![License](https://img.shields.io/github/license/csp-community/csp-benchmarks)](https://github.com/csp-community/csp-benchmarks)

The benchmark suite and installed CSP package have separate identities. Benched
records the suite Git revision, installed CSP version, optional CSP revision, machine,
Python runtime, parameters, and pytest-benchmark statistics in each run.

## Install

```bash
pip install -e ".[develop]"
```

Install the `hetzner` extra to use the cloud runner:

```bash
pip install -e ".[develop,hetzner]"
```

## Run and inspect benchmarks

The `csp-benchmarks` command forwards to Benched using this repository's
`pyproject.toml` configuration:

```bash
csp-benchmarks list
csp-benchmarks run --quick
csp-benchmarks run -k linear_graph
csp-benchmarks history
csp-benchmarks compare previous latest --fail-if median:10%
```

To associate a source checkout with the installed CSP subject, provide its revision:

```bash
csp-benchmarks run --subject-revision "$CSP_COMMIT" --machine github-actions
```

Equivalent Make targets are available:

```bash
make benchmark-list
make benchmark-quick
make benchmark MACHINE=my-machine
```

Pytest-benchmark calibrates iterations and executes multiple rounds by default.
`--quick` reduces benchmark duration; it does not remove parameter cases. Use pytest
selection such as `-k`, a file path, or a full node ID to select cases.

## Generate the static report

```bash
make benchmark-publish
make benchmark-view
```

`benchmark-publish` writes a static report to `build/benchmarks`.
`benchmark-view` serves it at <http://127.0.0.1:8000> and opens a browser.

## Benchmark groups

- `core`: graph topology and node overhead
- `baselib`: built-in operations and historical curves
- `math`: arithmetic, comparisons, and accumulators
- `stats`: statistical functions and array-size scaling

Cases use ordinary pytest parameterization and fixtures. Add benchmarks as top-level
`test_*` functions in `csp_benchmarks/benchmarks/bench_*.py`, then pass the operation
under test to the `benchmark` fixture.

## Run on Hetzner

Set `HCLOUD_TOKEN`, register an SSH public key named `benchmarks`, then run:

```bash
python -m csp_benchmarks.hetzner.cli run \
  --ssh-key ~/.ssh/hetzner_key \
  --ssh-key-name benchmarks \
  --server-type cx23 \
  --push
```

The runner creates a machine, prepares the selected Python environment, invokes the
same Make target, downloads results, and optionally commits them. It does not ask
Benched to create environments or install CSP versions.

## Import historical ASV results

The ASV configuration and result documents remain only for this repository's
one-time migration. Importing them through the CSP mapping keeps historical samples
on the same 95 benchmark identities used by the pytest suite:

```bash
make benchmark-import-asv
make benchmark-publish
```

The import is idempotent. New benchmark execution never invokes ASV.

## Results

Canonical Benched run documents are stored beneath `csp_benchmarks/benched-results`.
Legacy ASV documents remain in `csp_benchmarks/results` for one-time import. The
published report is available at <https://csp-community.github.io/csp-benchmarks/>.
