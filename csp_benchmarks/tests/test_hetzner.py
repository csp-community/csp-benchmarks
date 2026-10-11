"""Tests for Hetzner Cloud integration."""

import argparse
import importlib.util
from types import SimpleNamespace
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
        assert config.server_type == "cx23"
        assert config.image == "ubuntu-24.04"
        assert config.location == "nbg1"
        assert config.ssh_key_name is None

    def test_custom_config(self):
        """Test custom server configuration."""
        from csp_benchmarks.hetzner.server import ServerConfig

        config = ServerConfig(
            name="custom-runner",
            server_type="cpx51",
            image="ubuntu-22.04",
            location="nbg1",
            ssh_key_name="my-key",
        )
        assert config.name == "custom-runner"
        assert config.server_type == "cpx51"
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
        assert config.python_version == "3.11"

    def test_custom_config(self):
        """Test custom benchmark configuration."""
        from csp_benchmarks.hetzner.runner import BenchmarkConfig

        config = BenchmarkConfig(
            python_version="3.12",
        )
        assert config.python_version == "3.12"


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

    @patch("csp_benchmarks.hetzner.server.time.sleep")
    @patch("hcloud.Client")
    def test_creates_server_with_ssh_key_and_waits_until_running(self, mock_client_class, mock_sleep):
        from csp_benchmarks.hetzner.server import HetznerServerManager, ServerConfig

        client = mock_client_class.return_value
        server = MagicMock()
        server.id = 123
        server.status = "running"
        server.public_net.ipv4.ip = "1.2.3.4"
        client.servers.create.return_value.server = server
        client.servers.get_by_id.return_value = server
        manager = HetznerServerManager(token="test-token", config=ServerConfig(ssh_key_name="benchmarks"))

        assert manager.create_server() is server

        assert client.servers.create.call_args.kwargs["ssh_keys"] == [client.ssh_keys.get_by_name.return_value]
        client.ssh_keys.get_by_name.assert_called_once_with("benchmarks")
        client.servers.get_by_id.assert_called_once_with(123)
        mock_sleep.assert_called_once_with(30)


class TestHetznerBenchmarkRunner:
    @pytest.mark.parametrize("missing_network", [True, False])
    def test_requires_public_ipv4(self, missing_network):
        from csp_benchmarks.hetzner.runner import HetznerBenchmarkRunner

        server = MagicMock()
        if missing_network:
            server.public_net = None
        else:
            server.public_net.ipv4 = None

        with pytest.raises(ValueError, match="public IPv4 address"):
            HetznerBenchmarkRunner(server=server)

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
        assert runner.branch == "main"

    def test_init_with_config(self):
        """Test benchmark runner with custom config."""
        from csp_benchmarks.hetzner.runner import BenchmarkConfig, HetznerBenchmarkRunner

        mock_server = MagicMock()
        mock_server.public_net.ipv4.ip = "1.2.3.4"

        config = BenchmarkConfig()
        runner = HetznerBenchmarkRunner(
            server=mock_server,
            config=config,
            ssh_key_path="/path/to/key",
            branch="develop",
        )

        assert runner.branch == "develop"
        assert runner.ssh_key_path == "/path/to/key"

    def test_setup_installs_project_without_asv_initialization(self):
        from csp_benchmarks.hetzner.runner import HetznerBenchmarkRunner

        mock_server = MagicMock()
        mock_server.public_net.ipv4.ip = "1.2.3.4"
        mock_server.server_type.name = "cx23"
        runner = HetznerBenchmarkRunner(server=mock_server)

        with patch.object(runner, "_wait_for_ssh"), patch.object(runner, "_run_ssh_command") as mock_run:
            runner._setup_environment()

        commands = [call.args[0] for call in mock_run.call_args_list]
        assert any("make develop" in command for command in commands)
        assert not any("asv" in command.lower() for command in commands)

    def test_runs_benched_make_target_with_machine(self):
        from csp_benchmarks.hetzner.runner import HetznerBenchmarkRunner

        mock_server = MagicMock()
        mock_server.public_net.ipv4.ip = "1.2.3.4"
        runner = HetznerBenchmarkRunner(server=mock_server)
        runner._machine_name = "hetzner-cx23"

        completed = MagicMock(returncode=0, stdout="done", stderr="")
        with patch.object(runner, "_run_ssh_command", return_value=completed) as mock_run:
            assert runner._run_benched() == "done"

        command = mock_run.call_args_list[0].args[0]
        assert "make benchmark MACHINE=hetzner-cx23" in command
        assert "asv" not in command.lower()

    def test_pushes_results_to_selected_branch(self):
        from csp_benchmarks.hetzner.runner import HetznerBenchmarkRunner

        mock_server = MagicMock()
        mock_server.public_net.ipv4.ip = "1.2.3.4"
        runner = HetznerBenchmarkRunner(server=mock_server, branch="develop")

        completed = MagicMock(returncode=0, stdout="", stderr="")
        with patch.object(runner, "_run_ssh_command", return_value=completed) as mock_run:
            runner.push_results_to_repo(github_token="token")

        commands = [call.args[0] for call in mock_run.call_args_list]
        assert any(
            "git push https://x-access-token:token@github.com/csp-community/csp-benchmarks.git HEAD:develop" in command for command in commands
        )


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
        args.server_type = "cx23"
        args.ssh_key_name = None
        args.branch = "main"
        args.python_version = "3.11"
        args.reuse = False
        args.keep_server = False
        args.push = False
        args.ssh_key = None
        args.github_token = None

        # Patch os.environ to not have HCLOUD_TOKEN
        with patch.dict("os.environ", {}, clear=True):
            result = run_benchmarks(args)

        assert result == 1  # Should fail without token


@patch("csp_benchmarks.hetzner.cli.HetznerServerManager")
def test_cleanup_skips_servers_without_matching_names(mock_manager_class, monkeypatch):
    from csp_benchmarks.hetzner.cli import cleanup_servers

    monkeypatch.setenv("HCLOUD_TOKEN", "test-token")
    matching = SimpleNamespace(name="csp-benchmark-owned")
    manager = mock_manager_class.return_value
    manager.client.servers.get_all.return_value = [SimpleNamespace(name=None), SimpleNamespace(name="other"), matching]

    assert cleanup_servers(argparse.Namespace(token=None)) == 0

    manager.delete_server.assert_called_once_with(matching)
