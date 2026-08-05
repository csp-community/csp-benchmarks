"""Tests for the CSP benchmark CLI wrapper."""

from unittest.mock import patch

from csp_benchmarks.cli import main


@patch("csp_benchmarks.cli.benched_main", return_value=0)
def test_forwards_explicit_arguments_to_benched(mock_main):
    assert main(["run", "--pyproject", "custom.toml", "--quick", "-k", "linear_graph"]) == 0
    mock_main.assert_called_once_with(["run", "--pyproject", "custom.toml", "--quick", "-k", "linear_graph"])


@patch("csp_benchmarks.cli.benched_main", return_value=3)
def test_preserves_benched_exit_code(mock_main):
    assert main(["compare", "previous", "latest", "--pyproject", "custom.toml"]) == 3


@patch("csp_benchmarks.cli.benched_main", return_value=0)
def test_installed_cli_uses_packaged_suite_and_local_results(mock_main, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    assert main(["run", "--quick"]) == 0

    arguments = mock_main.call_args.args[0]
    assert arguments[:2] == ["run", "--quick"]
    assert arguments[arguments.index("--results-dir") + 1] == str(tmp_path / ".benched" / "results")
    assert "--override-ini=python_files=bench_*.py" in arguments
    assert arguments[arguments.index("--pyproject") + 1].endswith("csp_benchmarks/benched.toml")
