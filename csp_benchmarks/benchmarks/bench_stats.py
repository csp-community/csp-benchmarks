"""Benchmarks for CSP statistics operations."""

from datetime import datetime, timedelta, timezone

import csp
import numpy as np
import pytest

UTC = timezone(timedelta(0))


@pytest.fixture
def stats_data():
    def build(array_size, num_rows):
        start_date = datetime(2020, 1, 1, tzinfo=UTC)
        generator = np.random.default_rng(0)
        data = [(start_date + timedelta(seconds=index), generator.normal(size=(array_size,))) for index in range(num_rows)]
        return start_date, data

    return build


@pytest.mark.benchmark(group="stats")
@pytest.mark.parametrize("array_size", [100])
@pytest.mark.parametrize("function", ["median", "quantile", "rank"])
@pytest.mark.parametrize("interval", [100, 500, 1000])
def test_stats(benchmark, stats_data, array_size, function, interval):
    """Benchmark a CSP statistics function."""
    num_rows = 1000
    start_date, data = stats_data(array_size=array_size, num_rows=num_rows)
    function_args = {"quantile": {"quant": 0.95}}

    def graph():
        curve = csp.curve(typ=np.ndarray, data=data)
        value = getattr(csp.stats, function)(curve, interval=interval, **function_args.get(function, {}))
        csp.add_graph_output("final_value", value, tick_count=1)

    benchmark(csp.run, graph, realtime=False, starttime=start_date, endtime=timedelta(seconds=num_rows))


@pytest.mark.benchmark(group="stats")
@pytest.mark.parametrize("array_size", [10, 50, 100, 500])
@pytest.mark.parametrize("function", ["mean", "stddev"])
def test_stats_scaling(benchmark, stats_data, array_size, function):
    """Benchmark statistics scaling with array size."""
    num_rows = 500
    start_date, data = stats_data(array_size=array_size, num_rows=num_rows)

    def graph():
        curve = csp.curve(typ=np.ndarray, data=data)
        value = getattr(csp.stats, function)(curve, interval=100)
        csp.add_graph_output("result", value, tick_count=1)

    benchmark(csp.run, graph, realtime=False, starttime=start_date, endtime=timedelta(seconds=num_rows))
