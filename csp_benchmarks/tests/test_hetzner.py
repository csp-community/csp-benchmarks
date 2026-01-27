"""Tests for Hetzner Cloud integration."""

import importlib.util
from unittest.mock import MagicMock, patch

import pytest

# Check if hcloud is available
HAS_HCLOUD = importlib.util.find_spec("hcloud") is not None


class TestServerConfig:
    """Test ServerConfig dataclass."""

    def test_default_config(self):
        """Test default server configuration."""
        from csp_benchmarks.hetzner.server import ServerConfig

        config = ServerConfig()
        assert config.name == "csp-benchmark-runner"
        assert config.server_type == "cx32"
        assert config.image == "ubuntu-24.04"
        assert config.location == "fsn1"
        assert config.ssh_key_name is None

    def test_custom_config(self):
        """Test custom server configuration."""
        from csp_benchmarks.hetzner.server import ServerConfig

        config = ServerConfig(
            name="custom-runner",
            server_type="cx52",
            image="ubuntu-22.04",
            location="nbg1",
            ssh_key_name="my-key",
        )
        assert config.name == "custom-runner"
        assert config.server_type == "cx52"
        assert config.image == "ubuntu-22.04"
        assert config.location == "nbg1"
        assert config.ssh_key_name == "my-key"


class TestBenchmarkConfig:
    """Test BenchmarkConfig dataclass."""

    def test_default_config(self):
        """Test default benchmark configuration."""
        from csp_benchmarks.hetzner.runner import BenchmarkConfig

        config = BenchmarkConfig()
        assert config.csp_repo == "https://github.com/Point72/csp.git"
        assert config.benchmark_repo == "https://github.com/csp-community/csp-benchmarks.git"
        assert config.branches == ["main"]
        assert config.python_version == "3.11"
        assert config.commit_range is None

    def test_custom_config(self):
        """Test custom benchmark configuration."""
        from csp_benchmarks.hetzner.runner import BenchmarkConfig

        config = BenchmarkConfig(
            branches=["main", "develop"],
            commit_range="HEAD~5..HEAD",
        )
        assert config.branches == ["main", "develop"]
        assert config.commit_range == "HEAD~5..HEAD"


@pytest.mark.skipif(not HAS_HCLOUD, reason="hcloud not installed")
class TestHetznerServerManager:
    """Test HetznerServerManager class."""

    @patch("hcloud.Client")
    def test_init(self, mock_client_class):
        """Test server manager initialization."""
        from csp_benchmarks.hetzner.server import HetznerServerManager

        manager = HetznerServerManager(token="test-token")

        mock_client_class.assert_called_once_with(
            token="test-token",
            application_name="csp-benchmarks",
            application_version="1.0.0",
        )
        assert manager.config.name == "csp-benchmark-runner"

    @patch("hcloud.Client")
    def test_get_cloud_init_script(self, mock_client_class):
        """Test cloud-init script generation."""
        from csp_benchmarks.hetzner.server import HetznerServerManager

        manager = HetznerServerManager(token="test-token")
        script = manager._get_cloud_init_script()

        assert "#cloud-config" in script
        assert "package_update: true" in script
        assert "git" in script
        assert "python3" in script
        assert "cmake" in script


class TestHetznerBenchmarkRunner:
    """Test HetznerBenchmarkRunner class."""

    def test_init(self):
        """Test benchmark runner initialization."""
        from csp_benchmarks.hetzner.runner import HetznerBenchmarkRunner

        # Create mock server
        mock_server = MagicMock()
        mock_server.public_net.ipv4.ip = "1.2.3.4"

        runner = HetznerBenchmarkRunner(server=mock_server)

        assert runner.server == mock_server
        assert runner.server_ip == "1.2.3.4"
        assert runner.config.branches == ["main"]

    def test_init_with_config(self):
        """Test benchmark runner with custom config."""
        from csp_benchmarks.hetzner.runner import BenchmarkConfig, HetznerBenchmarkRunner

        mock_server = MagicMock()
        mock_server.public_net.ipv4.ip = "1.2.3.4"

        config = BenchmarkConfig(commit_range="HEAD~3..HEAD")
        runner = HetznerBenchmarkRunner(
            server=mock_server,
            config=config,
            ssh_key_path="/path/to/key",
        )

        assert runner.config.commit_range == "HEAD~3..HEAD"
        assert runner.ssh_key_path == "/path/to/key"


class TestHetznerCLI:
    """Test CLI functionality."""

    def test_cli_module_importable(self):
        """Test that CLI module can be imported."""
        from csp_benchmarks.hetzner import cli

        assert hasattr(cli, "main")
        assert hasattr(cli, "run_benchmarks")
        assert hasattr(cli, "cleanup_servers")

    @patch("csp_benchmarks.hetzner.cli.HetznerServerManager")
    @patch("csp_benchmarks.hetzner.cli.HetznerBenchmarkRunner")
    def test_run_benchmarks_no_token(self, mock_runner, mock_manager):
        """Test run_benchmarks fails without token."""
        from csp_benchmarks.hetzner.cli import run_benchmarks

        # Create mock args without token
        args = MagicMock()
        args.token = None
        args.server_name = "test"
        args.server_type = "cx32"
        args.ssh_key_name = None
        args.branches = "main"
        args.commits = None
        args.reuse = False
        args.keep_server = False
        args.push = False
        args.ssh_key = None
        args.github_token = None

        # Patch os.environ to not have HCLOUD_TOKEN
        with patch.dict("os.environ", {}, clear=True):
            result = run_benchmarks(args)

        assert result == 1  # Should fail without token
