# Benchmarks

csp-benchmarks uses [airspeed velocity (ASV)](https://asv.readthedocs.io/) for performance benchmarking.

## Benchmark Suites

### Core Benchmarks (bench_core.py)

Tests fundamental csp graph execution performance:

- **GraphExecutionSuite**: Measures graph execution with different topologies
  - `time_linear_graph`: Linear chain of nodes
  - `time_fan_out_graph`: Single source to many nodes
  - `time_fan_in_graph`: Many sources merging
- **NodeOverheadSuite**: Measures node invocation overhead
  - `time_empty_node`: Passthrough node
  - `time_compute_node`: Simple computation
  - `time_stateful_node`: Node with state

### Stats Benchmarks (bench_stats.py)

Tests the `csp.stats` module:

- **StatsBenchmarkSuite**: Statistical functions
  - Tests median, quantile, rank with different intervals
- **StatsScalingSuite**: Scaling behavior
  - Tests mean and stddev with varying array sizes

### Baselib Benchmarks (bench_baselib.py)

Tests built-in csp operations:

- **BaselibSuite**: Core operations
  - `time_filter`: Filter operation
  - `time_sample`: Sample operation
  - `time_delay`: Delay operation
  - `time_merge`: Merge operation
  - `time_flatten`: Flatten operation
- **CurveSuite**: Historical data loading
  - `time_curve_load`: Raw curve loading
  - `time_curve_with_processing`: Curve with processing

### Math Benchmarks (bench_math.py)

Tests `csp.math` operations:

- **MathSuite**: Arithmetic and comparisons
  - `time_abs`: Absolute value
  - `time_arithmetic_chain`: Chained operations
  - `time_comparisons`: Comparison operators
- **AccumulatorSuite**: Accumulating operations
  - `time_accum`: Accumulator
  - `time_count`: Counter
  - `time_diff`: Differencer

## Running Benchmarks

### Quick Start

```bash
# Install dependencies
pip install -e ".[develop]"

# Run quick benchmarks
make benchmark-quick

# Run full benchmarks
make benchmark

# View results
make benchmark-view
```

### Using ASV Directly

```bash
# Initialize machine
python -m asv machine --config csp_benchmarks/asv.conf.json --yes

# Run specific benchmark
python -m asv run --config csp_benchmarks/asv.conf.json --bench "GraphExecutionSuite" HEAD^!

# Compare commits
python -m asv compare --config csp_benchmarks/asv.conf.json HEAD~5 HEAD

# Continuous benchmarking
python -m asv continuous --config csp_benchmarks/asv.conf.json main HEAD
```

## Adding New Benchmarks

1. Create a new file in `csp_benchmarks/benchmarks/` named `bench_*.py`
1. Define classes ending in `Suite`
1. Add `setup` method for initialization
1. Add `time_*` methods for timing benchmarks

Example:

```python
class MyFeatureSuite:
    params = [[10, 100, 1000]]
    param_names = ["size"]

    def setup(self, size):
        self.size = size
        # Setup code here

    def time_my_operation(self, size):
        # Code to benchmark
        pass
```

## Interpreting Results

ASV provides several ways to view results:

- **Terminal output**: Shows timing for each benchmark
- **HTML report**: Interactive web interface (`make benchmark-view`)
- **Comparison**: Shows performance changes between commits

### Performance Regression Detection

ASV can detect regressions automatically:

```bash
# Check for regressions
python -m asv continuous --config csp_benchmarks/asv.conf.json main HEAD

# This will fail if performance degrades significantly
```
