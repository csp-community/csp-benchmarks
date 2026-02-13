"""
Benchmark runner for Hetzner Cloud servers.
"""

from __future__ import annotations

import logging
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hcloud.servers import BoundServer

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkConfig:
    """Configuration for benchmark runs."""

    csp_repo: str = "https://github.com/Point72/csp.git"
    benchmark_repo: str = "https://github.com/csp-community/csp-benchmarks.git"
    branches: list[str] = field(default_factory=lambda: ["main"])
    python_version: str = "3.11"
    commit_range: str | None = None  # e.g., "HEAD~5..HEAD"


class HetznerBenchmarkRunner:
    """
    Runs ASV benchmarks on a Hetzner Cloud server.

    This class handles:
    1. SSH connection to the server
    2. Setting up the benchmark environment
    3. Running ASV benchmarks
    4. Collecting and returning results
    """

    def __init__(
        self,
        server: BoundServer,
        config: BenchmarkConfig | None = None,
        ssh_key_path: str | None = None,
    ):
        """
        Initialize the benchmark runner.

        Args:
            server: The Hetzner server to run benchmarks on
            config: Benchmark configuration
            ssh_key_path: Path to SSH private key for authentication
        """
        self.server = server
        self.config = config or BenchmarkConfig()
        self.ssh_key_path = ssh_key_path
        self.server_ip = server.public_net.ipv4.ip

    def run_benchmarks(self) -> dict:
        """
        Run the full benchmark suite on the remote server.

        Returns:
            Dictionary containing benchmark results and metadata
        """
        logger.info(f"Starting benchmarks on {self.server_ip}")

        # Setup the environment
        self._setup_environment()

        # Run ASV benchmarks
        results = self._run_asv()

        # Collect results
        return self._collect_results(results)

    def _run_ssh_command(self, command: str, check: bool = True) -> subprocess.CompletedProcess:
        """Run a command on the remote server via SSH."""
        ssh_args = [
            "ssh",
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "UserKnownHostsFile=/dev/null",
        ]

        if self.ssh_key_path:
            ssh_args.extend(["-i", self.ssh_key_path])

        ssh_args.extend([f"root@{self.server_ip}", command])

        logger.debug(f"Running SSH command: {command}")
        result = subprocess.run(ssh_args, capture_output=True, text=True, check=check)

        if result.stdout:
            logger.debug(f"stdout: {result.stdout}")
        if result.stderr:
            logger.debug(f"stderr: {result.stderr}")

        return result

    def _scp_to_server(self, local_path: str, remote_path: str) -> None:
        """Copy a file to the remote server."""
        scp_args = [
            "scp",
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "UserKnownHostsFile=/dev/null",
        ]

        if self.ssh_key_path:
            scp_args.extend(["-i", self.ssh_key_path])

        scp_args.extend([local_path, f"root@{self.server_ip}:{remote_path}"])

        subprocess.run(scp_args, check=True)

    def _scp_from_server(self, remote_path: str, local_path: str) -> None:
        """Copy a file from the remote server."""
        scp_args = [
            "scp",
            "-r",
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "UserKnownHostsFile=/dev/null",
        ]

        if self.ssh_key_path:
            scp_args.extend(["-i", self.ssh_key_path])

        scp_args.extend([f"root@{self.server_ip}:{remote_path}", local_path])

        subprocess.run(scp_args, check=True)

    def _wait_for_ssh(self, timeout: int = 300, interval: int = 15) -> None:
        """Wait for SSH to become available on the server."""
        import time

        logger.info("Waiting for SSH to become available...")
        start_time = time.time()
        last_error = None

        while time.time() - start_time < timeout:
            try:
                result = self._run_ssh_command("echo 'SSH ready'", check=False)
                if result.returncode == 0:
                    logger.info("SSH connection established")
                    return
                last_error = f"exit code {result.returncode}: {result.stderr}"
            except Exception as e:
                last_error = str(e)

            elapsed = int(time.time() - start_time)
            logger.info(f"SSH not ready after {elapsed}s, retrying... (last error: {last_error})")
            time.sleep(interval)

        raise TimeoutError(f"SSH not available after {timeout} seconds. Last error: {last_error}")

    def _setup_environment(self) -> None:
        """Set up the benchmark environment on the remote server."""
        logger.info("Setting up benchmark environment...")

        # Wait for SSH to become available
        self._wait_for_ssh()

        # Determine machine name based on server type
        server_type = self.server.server_type.name
        machine_name = f"hetzner-{server_type}"

        commands = [
            # Wait for cloud-init to complete
            "cloud-init status --wait || true",
            # Install uv
            "curl -LsSf https://astral.sh/uv/install.sh | sh",
            # Add uv to PATH for this session
            "export PATH=$HOME/.local/bin:$PATH",
            # Install Python versions with uv
            "$HOME/.local/bin/uv python install 3.11 3.12 3.13",
            # Clone the benchmark repository
            f"git clone {self.config.benchmark_repo} /root/csp-benchmarks",
            # Set up Python environment using uv
            "cd /root/csp-benchmarks && $HOME/.local/bin/uv venv .venv --python 3.11",
            "cd /root/csp-benchmarks && $HOME/.local/bin/uv pip install --upgrade pip",
            "cd /root/csp-benchmarks && $HOME/.local/bin/uv pip install -e '.[develop]'",
            # Copy machine file to ~/.asv-machine.json
            "cp /root/csp-benchmarks/csp_benchmarks/asv-machine.json ~/.asv-machine.json",
        ]

        for cmd in commands:
            self._run_ssh_command(cmd)

        # Store machine name for use in _run_asv
        self._machine_name = machine_name
        logger.info(f"Environment setup complete (machine: {machine_name})")

    def _run_asv(self) -> str:
        """Run ASV benchmarks and return the output."""
        logger.info("Running ASV benchmarks...")

        # Determine which commits to benchmark
        if self.config.commit_range:
            commit_spec = self.config.commit_range
        else:
            # Just benchmark the latest commit on each branch
            commit_spec = " ".join(f"{branch}^!" for branch in self.config.branches)

        # Use the machine name determined during setup
        machine_arg = f"--machine {self._machine_name}" if hasattr(self, "_machine_name") else ""

        # Use absolute path for ASV config (like Makefile uses CURDIR)
        asv_config = "/root/csp-benchmarks/csp_benchmarks/asv.conf.json"
        cmd = f"cd /root/csp-benchmarks && .venv/bin/python -m asv run --config {asv_config} {machine_arg} --verbose {commit_spec}"
        result = self._run_ssh_command(cmd, check=False)

        return result.stdout + result.stderr

    def _collect_results(self, asv_output: str) -> dict:
        """Collect benchmark results from the remote server."""
        logger.info("Collecting benchmark results...")

        # Results are relative to the ASV config file location (csp_benchmarks/asv.conf.json)
        # So results_dir: "results" means /root/csp-benchmarks/csp_benchmarks/results/
        results_path = "/root/csp-benchmarks/csp_benchmarks/results/"

        # Check if results directory exists
        check_result = self._run_ssh_command(f"ls -la {results_path} 2>&1 || echo 'NO_RESULTS'", check=False)
        if "NO_RESULTS" in check_result.stdout or "No such file" in check_result.stdout:
            logger.warning("No results directory found - ASV may have failed to run")
            logger.warning(f"ASV output: {asv_output}")
            return {
                "server": {
                    "name": self.server.name,
                    "id": self.server.id,
                    "type": self.server.server_type.name,
                    "ip": self.server_ip,
                },
                "asv_output": asv_output,
                "results_files": [],
                "error": "No results directory found",
            }

        # Create a temporary directory to store results
        with tempfile.TemporaryDirectory() as tmpdir:
            local_results = Path(tmpdir) / "results"
            local_results.mkdir()

            # Copy results from server (results_dir is relative to config file location)
            self._scp_from_server(results_path, str(local_results))

            # Read and parse results
            results = {
                "server": {
                    "name": self.server.name,
                    "id": self.server.id,
                    "type": self.server.server_type.name,
                    "ip": self.server_ip,
                },
                "asv_output": asv_output,
                "results_files": [],
            }

            for result_file in local_results.rglob("*.json"):
                results["results_files"].append(
                    {
                        "name": result_file.name,
                        "content": result_file.read_text(),
                    }
                )

            return results

    def push_results_to_repo(self, github_token: str | None = None) -> None:
        """
        Push benchmark results back to the repository.

        Args:
            github_token: Optional GitHub token for authentication
        """
        logger.info("Pushing results to repository...")

        commands = [
            "cd /root/csp-benchmarks && git config user.email 'benchmark-bot@example.com'",
            "cd /root/csp-benchmarks && git config user.name 'Benchmark Bot'",
            "cd /root/csp-benchmarks && git add csp_benchmarks/results/",
            "cd /root/csp-benchmarks && git commit -m 'Add benchmark results' || true",
        ]

        if github_token:
            # Use token for authentication
            push_url = self.config.benchmark_repo.replace("https://", f"https://x-access-token:{github_token}@")
            commands.append(f"cd /root/csp-benchmarks && git push {push_url} HEAD:main")
        else:
            commands.append("cd /root/csp-benchmarks && git push origin main")

        for cmd in commands:
            self._run_ssh_command(cmd, check=False)

        logger.info("Results pushed successfully")
