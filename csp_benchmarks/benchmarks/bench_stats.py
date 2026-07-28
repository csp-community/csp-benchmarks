"""
Stats module benchmarks - ported from csp/benchmarks/stats.
"""

from datetime import datetime, timedelta, timezone
from typing import ClassVar

import csp
import numpy as np

UTC = timezone(timedelta(0))


class StatsBenchmarkSuite:
    """
    Benchmarks for csp.stats module functions.

    Tests statistical functions like median, quantile, and rank
    operating on time series of numpy arrays.
    """

    params: ClassVar[tuple[list[str], list[int]]] = (["median", "quantile", "rank"], [100, 500, 1000])
    param_names: ClassVar[list[str]] = ["function", "interval"]

    # Additional args for specific functions
    function_args: ClassVar[dict[str, dict[str, float]]] = {"quantile": {"quant": 0.95}}

    def setup(self, function, interval):
        self.start_date = datetime(2020, 1, 1, tzinfo=UTC)
        self.num_rows = 1_000
        self.array_size = 100
        self.test_times = [self.start_date + timedelta(seconds=i) for i in range(self.num_rows)]
        self.random_values = [np.random.normal(size=(self.array_size,)) for i in range(self.num_rows)]
        self.data = list(zip(self.test_times, self.random_values))
        self.interval = interval

    def time_stats(self, function, interval):
        """Time various stats functions."""

        def g():
            data = csp.curve(typ=np.ndarray, data=self.data)
            value = getattr(csp.stats, function)(data, interval=self.interval, **self.function_args.get(function, {}))
            csp.add_graph_output("final_value", value, tick_count=1)

        csp.run(g, realtime=False, starttime=self.start_date, endtime=timedelta(seconds=self.num_rows))


class StatsScalingSuite:
    """
    Benchmarks for testing how stats functions scale with data size.
    """

    params: ClassVar[list[int]] = [10, 50, 100, 500]
    param_names: ClassVar[list[str]] = ["array_size"]

    def setup(self, array_size):
        self.start_date = datetime(2020, 1, 1, tzinfo=UTC)
        self.num_rows = 500
        self.test_times = [self.start_date + timedelta(seconds=i) for i in range(self.num_rows)]
        self.random_values = [np.random.normal(size=(array_size,)) for i in range(self.num_rows)]
        self.data = list(zip(self.test_times, self.random_values))

    def time_mean_scaling(self, array_size):
        """Test how mean computation scales with array size."""

        def g():
            data = csp.curve(typ=np.ndarray, data=self.data)
            value = csp.stats.mean(data, interval=100)
            csp.add_graph_output("result", value, tick_count=1)

        csp.run(g, realtime=False, starttime=self.start_date, endtime=timedelta(seconds=self.num_rows))

    def time_stddev_scaling(self, array_size):
        """Test how stddev computation scales with array size."""

        def g():
            data = csp.curve(typ=np.ndarray, data=self.data)
            value = csp.stats.stddev(data, interval=100)
            csp.add_graph_output("result", value, tick_count=1)

        csp.run(g, realtime=False, starttime=self.start_date, endtime=timedelta(seconds=self.num_rows))
