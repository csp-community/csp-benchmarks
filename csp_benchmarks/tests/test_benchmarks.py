"""Tests for benchmark module discovery and structure."""

import inspect
from pathlib import Path

import pytest


class TestBenchmarkDiscovery:
    """Test that ASV can discover all benchmarks."""

    @pytest.fixture
    def benchmark_dir(self):
        """Get the benchmarks directory."""
        return Path(__file__).parent.parent / "benchmarks"

    def test_benchmarks_directory_exists(self, benchmark_dir):
        """Verify benchmarks directory exists."""
        assert benchmark_dir.exists(), f"Benchmarks directory not found: {benchmark_dir}"
        assert benchmark_dir.is_dir()

    def test_benchmark_files_exist(self, benchmark_dir):
        """Verify expected benchmark files exist."""
        expected_files = [
            "bench_core.py",
            "bench_stats.py",
            "bench_baselib.py",
            "bench_math.py",
        ]
        for filename in expected_files:
            filepath = benchmark_dir / filename
            assert filepath.exists(), f"Benchmark file not found: {filepath}"

    def test_benchmark_modules_importable(self, benchmark_dir):
        """Verify all benchmark modules can be imported."""
        import sys

        # Add benchmarks to path temporarily
        sys.path.insert(0, str(benchmark_dir.parent))
        try:
            from csp_benchmarks.benchmarks import bench_baselib, bench_core, bench_math, bench_stats

            assert bench_core is not None
            assert bench_stats is not None
            assert bench_baselib is not None
            assert bench_math is not None
        finally:
            sys.path.pop(0)


class TestBenchmarkClasses:
    """Test benchmark class structure for ASV compatibility."""

    @pytest.fixture
    def benchmark_modules(self):
        """Import all benchmark modules."""
        from csp_benchmarks.benchmarks import bench_baselib, bench_core, bench_math, bench_stats

        return {
            "bench_core": bench_core,
            "bench_stats": bench_stats,
            "bench_baselib": bench_baselib,
            "bench_math": bench_math,
        }

    def test_benchmark_classes_have_time_methods(self, benchmark_modules):
        """Verify benchmark classes have time_* methods."""
        for module_name, module in benchmark_modules.items():
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if name.endswith("Suite"):
                    time_methods = [m for m in dir(obj) if m.startswith("time_")]
                    assert len(time_methods) > 0, f"{module_name}.{name} has no time_* methods"

    def test_benchmark_classes_have_setup(self, benchmark_modules):
        """Verify benchmark classes have setup methods."""
        for module_name, module in benchmark_modules.items():
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if name.endswith("Suite"):
                    assert hasattr(obj, "setup"), f"{module_name}.{name} missing setup method"

    def test_core_benchmarks_structure(self, benchmark_modules):
        """Test specific structure of core benchmarks."""
        core = benchmark_modules["bench_core"]

        # Check GraphExecutionSuite
        assert hasattr(core, "GraphExecutionSuite")
        suite = core.GraphExecutionSuite
        assert hasattr(suite, "params")
        assert hasattr(suite, "param_names")
        assert hasattr(suite, "time_linear_graph")
        assert hasattr(suite, "time_fan_out_graph")
        assert hasattr(suite, "time_fan_in_graph")

        # Check NodeOverheadSuite
        assert hasattr(core, "NodeOverheadSuite")
        suite = core.NodeOverheadSuite
        assert hasattr(suite, "time_empty_node")
        assert hasattr(suite, "time_compute_node")
        assert hasattr(suite, "time_stateful_node")

    def test_stats_benchmarks_structure(self, benchmark_modules):
        """Test specific structure of stats benchmarks."""
        stats = benchmark_modules["bench_stats"]

        assert hasattr(stats, "StatsBenchmarkSuite")
        suite = stats.StatsBenchmarkSuite
        assert hasattr(suite, "params")
        assert hasattr(suite, "time_stats")

        assert hasattr(stats, "StatsScalingSuite")


class TestASVConfig:
    """Test ASV configuration."""

    @pytest.fixture
    def asv_config_path(self):
        """Get the ASV config path."""
        return Path(__file__).parent.parent / "asv.conf.json"

    def test_asv_config_exists(self, asv_config_path):
        """Verify asv.conf.json exists."""
        assert asv_config_path.exists(), f"ASV config not found: {asv_config_path}"

    def test_asv_config_valid_json(self, asv_config_path):
        """Verify asv.conf.json is valid JSON."""
        import json

        with open(asv_config_path) as f:
            config = json.load(f)

        assert isinstance(config, dict)
        assert "version" in config
        assert "project" in config
        assert "benchmark_dir" in config

    def test_asv_config_paths(self, asv_config_path):
        """Verify ASV config has correct paths."""
        import json

        with open(asv_config_path) as f:
            config = json.load(f)

        # Project is "csp" because we benchmark the CSP repo, not csp-benchmarks
        assert config["project"] == "csp"
        assert config["repo"] == "https://github.com/Point72/csp.git"
        assert config["benchmark_dir"] == "benchmarks"
        assert config["results_dir"] == "results"
