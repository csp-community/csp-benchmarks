"""Benchmarks for built-in CSP operations."""

from datetime import datetime, timedelta, timezone

import csp
import pytest

UTC = timezone(timedelta(0))


@pytest.fixture
def run_times(num_ticks):
    start_time = datetime(2020, 1, 1, tzinfo=UTC)
    return start_time, start_time + timedelta(seconds=num_ticks)


@pytest.mark.benchmark(group="baselib")
@pytest.mark.parametrize("num_ticks", [1000, 10000, 100000])
@pytest.mark.parametrize("operation", ["filter", "sample", "delay", "merge", "flatten"])
def test_baselib_operation(benchmark, run_times, operation):
    """Benchmark one built-in CSP operation."""

    @csp.graph
    def graph():
        timer = csp.timer(timedelta(seconds=1), 1.0)
        if operation == "filter":
            counter = csp.count(timer)
            is_even = csp.apply(counter, lambda value: value % 2 == 0, bool)
            result = csp.filter(is_even, timer)
        elif operation == "sample":
            result = csp.sample(csp.timer(timedelta(seconds=10), True), timer)
        elif operation == "delay":
            result = csp.delay(timer, timedelta(seconds=5))
        elif operation == "merge":
            result = csp.merge(timer, csp.timer(timedelta(seconds=2), 2.0), csp.timer(timedelta(seconds=3), 3.0))
        else:
            result = csp.flatten([timer, csp.timer(timedelta(seconds=2), 2.0), csp.timer(timedelta(seconds=3), 3.0)])
        csp.add_graph_output("output", result)

    start_time, end_time = run_times
    benchmark(csp.run, graph, starttime=start_time, endtime=end_time, realtime=False)


@pytest.fixture
def curve_case(num_points):
    start_time = datetime(2020, 1, 1, tzinfo=UTC)
    end_time = start_time + timedelta(seconds=num_points)
    data = [(start_time + timedelta(seconds=index), float(index)) for index in range(num_points)]
    return start_time, end_time, data


@pytest.mark.benchmark(group="baselib")
@pytest.mark.parametrize("num_points", [100, 1000, 10000])
@pytest.mark.parametrize("processing", [False, True], ids=["load", "processing"])
def test_curve(benchmark, curve_case, processing):
    """Benchmark loading curve data, optionally with downstream processing."""
    start_time, end_time, data = curve_case

    @csp.node
    def process(x: csp.ts[float]) -> csp.ts[float]:
        if csp.ticked(x):
            return x * 2.0

    @csp.graph
    def graph():
        result = csp.curve(float, data)
        if processing:
            result = process(result)
        csp.add_graph_output("output", result)

    benchmark(csp.run, graph, starttime=start_time, endtime=end_time, realtime=False)
