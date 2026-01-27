"""Tests for the CLI module."""

from unittest.mock import patch


class TestDiscoverBenchmarks:
    """Tests for benchmark discovery."""

    def test_discover_benchmarks_returns_dict(self):
        """Test that discover_benchmarks returns a dictionary."""
        from csp_benchmarks.cli import discover_benchmarks

        result = discover_benchmarks()
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_discover_benchmarks_has_expected_suites(self):
        """Test that known benchmark suites are discovered."""
        from csp_benchmarks.cli import discover_benchmarks

        result = discover_benchmarks()
        suite_names = list(result.keys())

        # Check for some expected suites
        assert any("core" in name.lower() for name in suite_names)
        assert any("baselib" in name.lower() for name in suite_names)

    def test_benchmark_info_structure(self):
        """Test that benchmark info has expected structure."""
        from csp_benchmarks.cli import discover_benchmarks

        result = discover_benchmarks()
        for name, info in result.items():
            assert "class" in info
            assert "module" in info
            assert "methods" in info
            assert isinstance(info["methods"], list)
            assert all(m.startswith("time_") for m in info["methods"])


class TestNormalizeParams:
    """Tests for parameter normalization."""

    def test_normalize_empty(self):
        """Test normalizing empty params."""
        from csp_benchmarks.cli import _normalize_params

        assert _normalize_params(None) == []
        assert _normalize_params([]) == []

    def test_normalize_single_list(self):
        """Test normalizing a single parameter list."""
        from csp_benchmarks.cli import _normalize_params

        result = _normalize_params([1, 2, 3])
        assert result == [[1, 2, 3]]

    def test_normalize_multiple_lists(self):
        """Test normalizing multiple parameter lists."""
        from csp_benchmarks.cli import _normalize_params

        result = _normalize_params([[1, 2], [3, 4]])
        assert result == [[1, 2], [3, 4]]


class TestGetParamCombinations:
    """Tests for parameter combination generation."""

    def test_no_params(self):
        """Test with no parameters."""
        from csp_benchmarks.cli import _get_param_combinations

        result = _get_param_combinations(None, None)
        assert result == [{}]

    def test_single_param(self):
        """Test with single parameter."""
        from csp_benchmarks.cli import _get_param_combinations

        result = _get_param_combinations([1, 2, 3], ["x"])
        assert result == [{"x": 1}, {"x": 2}, {"x": 3}]

    def test_multiple_params(self):
        """Test with multiple parameters (product)."""
        from csp_benchmarks.cli import _get_param_combinations

        result = _get_param_combinations([[1, 2], [3, 4]], ["a", "b"])
        assert len(result) == 4
        assert {"a": 1, "b": 3} in result
        assert {"a": 2, "b": 4} in result

    def test_quick_mode(self):
        """Test quick mode reduces combinations."""
        from csp_benchmarks.cli import _get_param_combinations

        result = _get_param_combinations([1, 2, 3, 4, 5], ["x"], quick=True)
        assert result == [{"x": 1}, {"x": 5}]


class TestFormatTime:
    """Tests for time formatting."""

    def test_nanoseconds(self):
        """Test formatting nanoseconds."""
        from csp_benchmarks.cli import format_time

        assert "ns" in format_time(1e-9)

    def test_microseconds(self):
        """Test formatting microseconds."""
        from csp_benchmarks.cli import format_time

        assert "µs" in format_time(1e-6)

    def test_milliseconds(self):
        """Test formatting milliseconds."""
        from csp_benchmarks.cli import format_time

        assert "ms" in format_time(0.001)

    def test_seconds(self):
        """Test formatting seconds."""
        from csp_benchmarks.cli import format_time

        assert "s" in format_time(1.5)
        assert "1.500" in format_time(1.5)


class TestRunBenchmarkMethod:
    """Tests for running individual benchmark methods."""

    def test_run_simple_benchmark(self):
        """Test running a simple benchmark."""
        from csp_benchmarks.cli import run_benchmark_method

        class FakeBenchmark:
            def time_simple(self):
                pass

        instance = FakeBenchmark()
        result = run_benchmark_method(instance, "time_simple", {}, num_runs=2)

        assert "error" not in result
        assert "min" in result
        assert "max" in result
        assert "mean" in result
        assert result["runs"] == 2

    def test_run_benchmark_with_params(self):
        """Test running benchmark with parameters."""
        from csp_benchmarks.cli import run_benchmark_method

        class FakeBenchmark:
            def time_param(self, x, y):
                pass

        instance = FakeBenchmark()
        result = run_benchmark_method(instance, "time_param", {"x": 1, "y": 2})

        assert "error" not in result

    def test_run_benchmark_with_error(self):
        """Test running benchmark that raises error."""
        from csp_benchmarks.cli import run_benchmark_method

        class FakeBenchmark:
            def time_error(self):
                raise ValueError("test error")

        instance = FakeBenchmark()
        result = run_benchmark_method(instance, "time_error", {})

        assert "error" in result
        assert "test error" in result["error"]


class TestListBenchmarks:
    """Tests for list_benchmarks function."""

    def test_list_benchmarks_returns_zero(self):
        """Test that list_benchmarks returns 0 on success."""
        from csp_benchmarks.cli import list_benchmarks

        result = list_benchmarks()
        assert result == 0


class TestRunBenchmarks:
    """Tests for run_benchmarks function."""

    def test_run_benchmarks_returns_int(self):
        """Test that run_benchmarks returns an integer."""
        from csp_benchmarks.cli import run_benchmarks

        # Run with method filter that won't match to make test fast
        result = run_benchmarks(method_filter="nonexistent_method_xyz")
        assert isinstance(result, int)


class TestMainEntryPoint:
    """Tests for main CLI entry point."""

    def test_main_list(self):
        """Test main with list command."""
        from csp_benchmarks.cli import main

        with patch("sys.argv", ["csp-benchmarks", "list"]):
            result = main()
            assert result == 0

    def test_main_run_quick(self):
        """Test main with run command in quick mode."""
        from csp_benchmarks.cli import main

        # Use method filter to make test fast
        with patch("sys.argv", ["csp-benchmarks", "run", "-m", "nonexistent_xyz", "-q"]):
            result = main()
            assert isinstance(result, int)
