"""
Math module benchmarks - testing csp.math operations.
"""

from datetime import datetime, timedelta

import csp


class MathSuite:
    """
    Benchmarks for csp.math operations.
    """

    params = [1000, 10000, 100000]
    param_names = ["num_ticks"]

    def setup(self, num_ticks):
        self.start_time = datetime(2020, 1, 1)
        self.end_time = self.start_time + timedelta(seconds=num_ticks)

    def time_abs(self, num_ticks):
        """Benchmark csp.abs operation."""

        @csp.graph
        def graph():
            timer = csp.timer(timedelta(seconds=1), -1.5)
            result = abs(timer)
            csp.add_graph_output("output", result)

        csp.run(graph, starttime=self.start_time, endtime=self.end_time, realtime=False)

    def time_arithmetic_chain(self, num_ticks):
        """Benchmark chained arithmetic operations."""

        @csp.graph
        def graph():
            t1 = csp.timer(timedelta(seconds=1), 1.0)
            t2 = csp.timer(timedelta(seconds=1), 2.0)
            result = (t1 + t2) * t1 - t2 / (t1 + 1)
            csp.add_graph_output("output", result)

        csp.run(graph, starttime=self.start_time, endtime=self.end_time, realtime=False)

    def time_comparisons(self, num_ticks):
        """Benchmark comparison operations."""

        @csp.graph
        def graph():
            t1 = csp.timer(timedelta(seconds=1), 1.0)
            t2 = csp.timer(timedelta(seconds=1), 2.0)
            gt = t1 > t2
            lt = t1 < t2
            eq = t1 == t2
            csp.add_graph_output("gt", gt)
            csp.add_graph_output("lt", lt)
            csp.add_graph_output("eq", eq)

        csp.run(graph, starttime=self.start_time, endtime=self.end_time, realtime=False)


class AccumulatorSuite:
    """
    Benchmarks for accumulating operations.
    """

    params = [1000, 10000, 100000]
    param_names = ["num_ticks"]

    def setup(self, num_ticks):
        self.start_time = datetime(2020, 1, 1)
        self.end_time = self.start_time + timedelta(seconds=num_ticks)

    def time_accum(self, num_ticks):
        """Benchmark csp.accum operation."""

        @csp.graph
        def graph():
            timer = csp.timer(timedelta(seconds=1), 1.0)
            accumulated = csp.accum(timer)
            csp.add_graph_output("output", accumulated)

        csp.run(graph, starttime=self.start_time, endtime=self.end_time, realtime=False)

    def time_count(self, num_ticks):
        """Benchmark csp.count operation."""

        @csp.graph
        def graph():
            timer = csp.timer(timedelta(seconds=1), 1.0)
            counted = csp.count(timer)
            csp.add_graph_output("output", counted)

        csp.run(graph, starttime=self.start_time, endtime=self.end_time, realtime=False)

    def time_diff(self, num_ticks):
        """Benchmark csp.diff operation."""

        @csp.graph
        def graph():
            timer = csp.timer(timedelta(seconds=1), 1.0)
            accumulated = csp.accum(timer)
            diffed = csp.diff(accumulated, 1)
            csp.add_graph_output("output", diffed)

        csp.run(graph, starttime=self.start_time, endtime=self.end_time, realtime=False)
