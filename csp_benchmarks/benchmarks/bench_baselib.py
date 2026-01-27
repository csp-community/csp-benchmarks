"""
Baselib benchmarks - testing built-in csp operations.
"""

from datetime import datetime, timedelta

import csp


class BaselibSuite:
    """
    Benchmarks for csp.baselib operations.
    """

    params = [1000, 10000, 100000]
    param_names = ["num_ticks"]

    def setup(self, num_ticks):
        self.start_time = datetime(2020, 1, 1)
        self.end_time = self.start_time + timedelta(seconds=num_ticks)

    def time_filter(self, num_ticks):
        """Benchmark csp.filter operation."""

        @csp.graph
        def graph():
            timer = csp.timer(timedelta(seconds=1), 1.0)
            counter = csp.count(timer)
            # Filter to only even counts
            is_even = csp.apply(counter, lambda x: x % 2 == 0, bool)
            filtered = csp.filter(is_even, timer)
            csp.add_graph_output("output", filtered)

        csp.run(graph, starttime=self.start_time, endtime=self.end_time, realtime=False)

    def time_sample(self, num_ticks):
        """Benchmark csp.sample operation."""

        @csp.graph
        def graph():
            fast_timer = csp.timer(timedelta(seconds=1), 1.0)
            slow_trigger = csp.timer(timedelta(seconds=10), True)
            sampled = csp.sample(slow_trigger, fast_timer)
            csp.add_graph_output("output", sampled)

        csp.run(graph, starttime=self.start_time, endtime=self.end_time, realtime=False)

    def time_delay(self, num_ticks):
        """Benchmark csp.delay operation."""

        @csp.graph
        def graph():
            timer = csp.timer(timedelta(seconds=1), 1.0)
            delayed = csp.delay(timer, timedelta(seconds=5))
            csp.add_graph_output("output", delayed)

        csp.run(graph, starttime=self.start_time, endtime=self.end_time, realtime=False)

    def time_merge(self, num_ticks):
        """Benchmark csp.merge operation."""

        @csp.graph
        def graph():
            t1 = csp.timer(timedelta(seconds=1), 1.0)
            t2 = csp.timer(timedelta(seconds=2), 2.0)
            t3 = csp.timer(timedelta(seconds=3), 3.0)
            merged = csp.merge(t1, t2, t3)
            csp.add_graph_output("output", merged)

        csp.run(graph, starttime=self.start_time, endtime=self.end_time, realtime=False)

    def time_flatten(self, num_ticks):
        """Benchmark csp.flatten operation."""

        @csp.graph
        def graph():
            timer1 = csp.timer(timedelta(seconds=1), 1.0)
            timer2 = csp.timer(timedelta(seconds=2), 2.0)
            timer3 = csp.timer(timedelta(seconds=3), 3.0)
            flattened = csp.flatten([timer1, timer2, timer3])
            csp.add_graph_output("output", flattened)

        csp.run(graph, starttime=self.start_time, endtime=self.end_time, realtime=False)


class CurveSuite:
    """
    Benchmarks for csp.curve - loading historical data.
    """

    params = [100, 1000, 10000]
    param_names = ["num_points"]

    def setup(self, num_points):
        self.start_time = datetime(2020, 1, 1)
        self.end_time = self.start_time + timedelta(seconds=num_points)
        # Pre-generate the curve data
        self.data = [(self.start_time + timedelta(seconds=i), float(i)) for i in range(num_points)]

    def time_curve_load(self, num_points):
        """Benchmark loading data via csp.curve."""

        @csp.graph
        def graph():
            data = csp.curve(float, self.data)
            csp.add_graph_output("output", data)

        csp.run(graph, starttime=self.start_time, endtime=self.end_time, realtime=False)

    def time_curve_with_processing(self, num_points):
        """Benchmark loading and processing curve data."""

        @csp.node
        def process(x: csp.ts[float]) -> csp.ts[float]:
            if csp.ticked(x):
                return x * 2.0

        @csp.graph
        def graph():
            data = csp.curve(float, self.data)
            processed = process(data)
            csp.add_graph_output("output", processed)

        csp.run(graph, starttime=self.start_time, endtime=self.end_time, realtime=False)
