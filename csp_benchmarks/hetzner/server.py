"""
Hetzner Cloud server management for benchmarks.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hcloud.servers import BoundServer

logger = logging.getLogger(__name__)


@dataclass
class ServerConfig:
    """Configuration for a Hetzner benchmark server."""

    name: str = "csp-benchmark-runner"
    server_type: str = "cx32"  # 4 vCPU, 8GB RAM - good balance for benchmarks
    image: str = "ubuntu-24.04"
    location: str = "fsn1"  # Falkenstein, Germany
    ssh_key_name: str | None = None


class HetznerServerManager:
    """
    Manages Hetzner Cloud servers for running benchmarks.

    Usage:
        manager = HetznerServerManager(token="your-hcloud-token")
        server = manager.create_server()
        # ... run benchmarks ...
        manager.delete_server(server)
    """

    def __init__(self, token: str, config: ServerConfig | None = None):
        """
        Initialize the server manager.

        Args:
            token: Hetzner Cloud API token
            config: Optional server configuration
        """
        from hcloud import Client

        self.client = Client(
            token=token,
            application_name="csp-benchmarks",
            application_version="1.0.0",
        )
        self.config = config or ServerConfig()

    def create_server(self, wait_for_ready: bool = True) -> BoundServer:
        """
        Create a new Hetzner server for benchmarking.

        Args:
            wait_for_ready: Whether to wait for the server to be ready

        Returns:
            The created server object
        """
        from hcloud.images import Image
        from hcloud.locations import Location
        from hcloud.server_types import ServerType

        logger.info(f"Creating Hetzner server: {self.config.name}")

        # Get SSH keys if specified
        ssh_keys = []
        if self.config.ssh_key_name:
            ssh_key = self.client.ssh_keys.get_by_name(self.config.ssh_key_name)
            if ssh_key:
                ssh_keys.append(ssh_key)

        # Create the server
        response = self.client.servers.create(
            name=self.config.name,
            server_type=ServerType(name=self.config.server_type),
            image=Image(name=self.config.image),
            location=Location(name=self.config.location),
            ssh_keys=ssh_keys if ssh_keys else None,
            user_data=self._get_cloud_init_script(),
        )

        server = response.server
        root_password = response.root_password

        logger.info(f"Server created: {server.name} (ID: {server.id})")
        if root_password:
            logger.info(f"Root password: {root_password}")

        if wait_for_ready:
            self._wait_for_server_ready(server)

        return server

    def delete_server(self, server: BoundServer) -> None:
        """
        Delete a Hetzner server.

        Args:
            server: The server to delete
        """
        logger.info(f"Deleting server: {server.name} (ID: {server.id})")
        server.delete()
        logger.info("Server deleted successfully")

    def get_server(self, name: str | None = None) -> BoundServer | None:
        """
        Get an existing server by name.

        Args:
            name: Server name (defaults to config name)

        Returns:
            The server if found, None otherwise
        """
        name = name or self.config.name
        return self.client.servers.get_by_name(name)

    def _wait_for_server_ready(self, server: BoundServer, timeout: int = 300) -> None:
        """Wait for the server to be running and SSH-accessible."""
        logger.info("Waiting for server to be ready...")

        start_time = time.time()
        while time.time() - start_time < timeout:
            # Refresh server status
            server = self.client.servers.get_by_id(server.id)

            if server.status == "running":
                logger.info(f"Server is running at {server.public_net.ipv4.ip}")
                # Give SSH a bit more time to be ready
                time.sleep(30)
                return

            logger.debug(f"Server status: {server.status}")
            time.sleep(10)

        raise TimeoutError(f"Server did not become ready within {timeout} seconds")

    def _get_cloud_init_script(self) -> str:
        """Get the cloud-init script for server setup."""
        return """#cloud-config
package_update: true
package_upgrade: true

packages:
  - git
  - python3
  - python3-pip
  - python3-venv
  - build-essential
  - cmake
  - ninja-build
  - libboost-all-dev

runcmd:
  - python3 -m pip install --upgrade pip
  - python3 -m pip install uv
"""
