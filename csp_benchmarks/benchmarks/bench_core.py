"""Core CSP graph execution benchmarks."""

from datetime import datetime, timedelta, timezone

import csp
import pytest

UTC = timezone(timedelta(0))


@pytest.fixture
def run_times(num_ticks):
    start_time = datetime(2020, 1, 1, tzinfo=UTC)
    return start_time, start_time + timedelta(seconds=num_ticks)


@pytest.mark.benchmark(group="core")
@pytest.mark.parametrize("num_nodes", [10, 100, 1000])
@pytest.mark.parametrize("num_ticks", [100, 1000, 10000])
def test_linear_graph(benchmark, run_times, num_nodes):
    """Time a linear chain of nodes passing data through."""

    @csp.node
    def passthrough(x: csp.ts[float]) -> csp.ts[float]:
        if csp.ticked(x):
            return x

    @csp.graph
    def linear_graph():
        current = csp.timer(timedelta(seconds=1), 1.0)
        for _ in range(num_nodes):
            current = passthrough(current)
        csp.add_graph_output("output", current)

    start_time, end_time = run_times
    benchmark(csp.run, linear_graph, starttime=start_time, endtime=end_time, realtime=False)


@pytest.mark.benchmark(group="core")
@pytest.mark.parametrize("num_nodes", [10, 100, 1000])
@pytest.mark.parametrize("num_ticks", [100, 1000, 10000])
def test_fan_out_graph(benchmark, run_times, num_nodes):
    """Time a graph with one source fanning out to many nodes."""

    @csp.node
    def consumer(x: csp.ts[float]) -> csp.ts[float]:
        if csp.ticked(x):
            return x * 2

    @csp.graph
    def fan_out_graph():
        timer = csp.timer(timedelta(seconds=1), 1.0)
        for index in range(num_nodes):
            csp.add_graph_output(f"output_{index}", consumer(timer))

    start_time, end_time = run_times
    benchmark(csp.run, fan_out_graph, starttime=start_time, endtime=end_time, realtime=False)


@pytest.mark.benchmark(group="core")
@pytest.mark.parametrize("num_nodes", [10, 100, 1000])
@pytest.mark.parametrize("num_ticks", [100, 1000, 10000])
def test_fan_in_graph(benchmark, run_times, num_nodes):
    """Time a graph with many sources merging into one."""

    @csp.graph
    def fan_in_graph():
        sources = [csp.timer(timedelta(seconds=1), float(index)) for index in range(num_nodes)]
        csp.add_graph_output("output", csp.merge(*sources))

    start_time, end_time = run_times
    benchmark(csp.run, fan_in_graph, starttime=start_time, endtime=end_time, realtime=False)


@pytest.mark.benchmark(group="core")
@pytest.mark.parametrize("num_ticks", [100, 1000, 10000, 100000])
def test_empty_node(benchmark, run_times):
    """Measure overhead of an empty node that passes data through."""

    @csp.node
    def empty_node(x: csp.ts[float]) -> csp.ts[float]:
        if csp.ticked(x):
            return x

    @csp.graph
    def graph():
        timer = csp.timer(timedelta(seconds=1), 1.0)
        csp.add_graph_output("output", empty_node(timer))

    start_time, end_time = run_times
    benchmark(csp.run, graph, starttime=start_time, endtime=end_time, realtime=False)


@pytest.mark.benchmark(group="core")
@pytest.mark.parametrize("num_ticks", [100, 1000, 10000, 100000])
def test_compute_node(benchmark, run_times):
    """Measure overhead of a node doing simple computation."""

    @csp.node
    def compute_node(x: csp.ts[float]) -> csp.ts[float]:
        if csp.ticked(x):
            return x * 2.0 + 1.0

    @csp.graph
    def graph():
        timer = csp.timer(timedelta(seconds=1), 1.0)
        csp.add_graph_output("output", compute_node(timer))

    start_time, end_time = run_times
    benchmark(csp.run, graph, starttime=start_time, endtime=end_time, realtime=False)


@pytest.mark.benchmark(group="core")
@pytest.mark.parametrize("num_ticks", [100, 1000, 10000, 100000])
def test_stateful_node(benchmark, run_times):
    """Measure overhead of a stateful node."""

    @csp.node
    def stateful_node(x: csp.ts[float]) -> csp.ts[float]:
        with csp.state():
            s_sum = 0.0
            s_count = 0

        if csp.ticked(x):
            s_sum += x
            s_count += 1
            return s_sum / s_count

    @csp.graph
    def graph():
        timer = csp.timer(timedelta(seconds=1), 1.0)
        csp.add_graph_output("output", stateful_node(timer))

    start_time, end_time = run_times
    benchmark(csp.run, graph, starttime=start_time, endtime=end_time, realtime=False)
