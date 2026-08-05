"""Benchmarks for CSP math operations."""

from datetime import datetime, timedelta, timezone

import csp
import pytest

UTC = timezone(timedelta(0))


@pytest.fixture
def run_times(num_ticks):
    start_time = datetime(2020, 1, 1, tzinfo=UTC)
    return start_time, start_time + timedelta(seconds=num_ticks)


@pytest.mark.benchmark(group="math")
@pytest.mark.parametrize("num_ticks", [1000, 10000, 100000])
@pytest.mark.parametrize("operation", ["abs", "arithmetic", "comparisons"])
def test_math_operation(benchmark, run_times, operation):
    """Benchmark one CSP math operation."""

    @csp.graph
    def graph():
        first = csp.timer(timedelta(seconds=1), -1.5 if operation == "abs" else 1.0)
        if operation == "abs":
            csp.add_graph_output("output", abs(first))
            return
        second = csp.timer(timedelta(seconds=1), 2.0)
        if operation == "arithmetic":
            csp.add_graph_output("output", (first + second) * first - second / (first + 1))
            return
        csp.add_graph_output("gt", first > second)
        csp.add_graph_output("lt", first < second)
        csp.add_graph_output("eq", first == second)

    start_time, end_time = run_times
    benchmark(csp.run, graph, starttime=start_time, endtime=end_time, realtime=False)


@pytest.mark.benchmark(group="math")
@pytest.mark.parametrize("num_ticks", [1000, 10000, 100000])
@pytest.mark.parametrize("operation", ["accum", "count", "diff"])
def test_accumulator_operation(benchmark, run_times, operation):
    """Benchmark one CSP accumulating operation."""

    @csp.graph
    def graph():
        timer = csp.timer(timedelta(seconds=1), 1.0)
        if operation == "accum":
            result = csp.accum(timer)
        elif operation == "count":
            result = csp.count(timer)
        else:
            result = csp.diff(csp.accum(timer), 1)
        csp.add_graph_output("output", result)

    start_time, end_time = run_times
    benchmark(csp.run, graph, starttime=start_time, endtime=end_time, realtime=False)
