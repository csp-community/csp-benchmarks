"""
Core CSP benchmarks - testing graph execution performance.
"""

from datetime import datetime, timedelta

import csp


class GraphExecutionSuite:
    """
    Benchmarks for basic csp graph execution.

    These tests measure the overhead of running csp graphs with varying
    numbers of nodes and ticks.
    """

    params = ([10, 100, 1000], [100, 1000, 10000])
    param_names = ["num_nodes", "num_ticks"]

    def setup(self, num_nodes, num_ticks):
        self.start_time = datetime(2020, 1, 1)
        self.end_time = self.start_time + timedelta(seconds=num_ticks)

    def time_linear_graph(self, num_nodes, num_ticks):
        """Time a linear chain of nodes passing data through."""

        @csp.node
        def passthrough(x: csp.ts[float]) -> csp.ts[float]:
            if csp.ticked(x):
                return x

        @csp.graph
        def linear_graph():
            # Create initial timer-based source
            timer = csp.timer(timedelta(seconds=1), 1.0)
            current = timer

            # Chain nodes together
            for _ in range(num_nodes):
                current = passthrough(current)

            csp.add_graph_output("output", current)

        csp.run(linear_graph, starttime=self.start_time, endtime=self.end_time, realtime=False)

    def time_fan_out_graph(self, num_nodes, num_ticks):
        """Time a graph with one source fanning out to many nodes."""

        @csp.node
        def consumer(x: csp.ts[float]) -> csp.ts[float]:
            if csp.ticked(x):
                return x * 2

        @csp.graph
        def fan_out_graph():
            timer = csp.timer(timedelta(seconds=1), 1.0)

            for i in range(num_nodes):
                result = consumer(timer)
                csp.add_graph_output(f"output_{i}", result)

        csp.run(fan_out_graph, starttime=self.start_time, endtime=self.end_time, realtime=False)

    def time_fan_in_graph(self, num_nodes, num_ticks):
        """Time a graph with many sources merging into one."""

        @csp.graph
        def fan_in_graph():
            sources = [csp.timer(timedelta(seconds=1), float(i)) for i in range(num_nodes)]
            result = csp.merge(*sources)
            csp.add_graph_output("output", result)

        csp.run(fan_in_graph, starttime=self.start_time, endtime=self.end_time, realtime=False)


class NodeOverheadSuite:
    """
    Benchmarks for measuring node invocation overhead.
    """

    params = [100, 1000, 10000, 100000]
    param_names = ["num_ticks"]

    def setup(self, num_ticks):
        self.start_time = datetime(2020, 1, 1)
        self.end_time = self.start_time + timedelta(seconds=num_ticks)

    def time_empty_node(self, num_ticks):
        """Measure overhead of an empty node that just passes data."""

        @csp.node
        def empty_node(x: csp.ts[float]) -> csp.ts[float]:
            if csp.ticked(x):
                return x

        @csp.graph
        def graph():
            timer = csp.timer(timedelta(seconds=1), 1.0)
            result = empty_node(timer)
            csp.add_graph_output("output", result)

        csp.run(graph, starttime=self.start_time, endtime=self.end_time, realtime=False)

    def time_compute_node(self, num_ticks):
        """Measure overhead of a node doing simple computation."""

        @csp.node
        def compute_node(x: csp.ts[float]) -> csp.ts[float]:
            if csp.ticked(x):
                return x * 2.0 + 1.0

        @csp.graph
        def graph():
            timer = csp.timer(timedelta(seconds=1), 1.0)
            result = compute_node(timer)
            csp.add_graph_output("output", result)

        csp.run(graph, starttime=self.start_time, endtime=self.end_time, realtime=False)

    def time_stateful_node(self, num_ticks):
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
            result = stateful_node(timer)
            csp.add_graph_output("output", result)

        csp.run(graph, starttime=self.start_time, endtime=self.end_time, realtime=False)
