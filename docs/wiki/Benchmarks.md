# Run and publish CSP benchmarks

Install the suite and its development dependencies into the Python environment that
contains the CSP version you want to measure:

```bash
pip install -e ".[develop]"
```

List all parameterized cases without executing them:

```bash
csp-benchmarks list
```

Run the complete suite or select a subset with normal pytest arguments:

```bash
csp-benchmarks run
csp-benchmarks run --quick
csp-benchmarks run -k linear_graph
csp-benchmarks run csp_benchmarks/benchmarks/bench_stats.py
```

If CSP came from a source checkout, record its revision separately from the benchmark
suite revision:

```bash
csp-benchmarks run --subject-revision "$CSP_COMMIT" --machine my-machine
```

Compare two compatible saved runs:

```bash
csp-benchmarks history
csp-benchmarks compare previous latest
csp-benchmarks compare previous latest --fail-if median:10%
```

Generate and preview the static report:

```bash
make benchmark-publish
make benchmark-view
```

To add a benchmark, create a top-level `test_*` function in a `bench_*.py` file. Use
pytest fixtures for setup, `pytest.mark.parametrize` for collection axes, and pass
only the operation being measured to pytest-benchmark's `benchmark` fixture.

```python
import pytest


@pytest.fixture
def values(size):
    return make_values(size)


@pytest.mark.benchmark(group="example")
@pytest.mark.parametrize("size", [10, 100, 1_000])
def test_operation(benchmark, values):
    benchmark(operation, values)
```

Use `benchmark.pedantic` only when setup or teardown must happen around every timed
round.
