#!/usr/bin/env python3
"""
CLI tool for running benchmarks on Hetzner Cloud.

Usage:
    python -m csp_benchmarks.hetzner.cli run --token $HCLOUD_TOKEN
    python -m csp_benchmarks.hetzner.cli cleanup --token $HCLOUD_TOKEN
"""

from __future__ import annotations

import argparse
import logging
import os
import sys

from .runner import BenchmarkConfig, HetznerBenchmarkRunner
from .server import HetznerServerManager, ServerConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def run_benchmarks(args: argparse.Namespace) -> int:
    """Run benchmarks on a Hetzner Cloud server."""
    token = args.token or os.environ.get("HCLOUD_TOKEN")
    if not token:
        logger.error("Hetzner Cloud token required. Set HCLOUD_TOKEN or use --token")
        return 1

    # Configure server
    server_config = ServerConfig(
        name=args.server_name,
        server_type=args.server_type,
        ssh_key_name=args.ssh_key_name,
    )

    # Configure benchmarks
    benchmark_config = BenchmarkConfig(
        branches=args.branches.split(",") if args.branches else ["main"],
        commit_range=args.commits,
    )

    manager = HetznerServerManager(token=token, config=server_config)

    try:
        # Check if server already exists
        server = manager.get_server()
        if server and not args.reuse:
            logger.info(f"Server {server.name} already exists. Use --reuse to reuse it.")
            return 1
        elif not server:
            server = manager.create_server()

        # Run benchmarks
        runner = HetznerBenchmarkRunner(
            server=server,
            config=benchmark_config,
            ssh_key_path=args.ssh_key,
        )

        results = runner.run_benchmarks()
        logger.info(f"Benchmarks completed. Results: {len(results.get('results_files', []))} files")

        # Push results if requested
        if args.push:
            github_token = args.github_token or os.environ.get("GITHUB_TOKEN")
            runner.push_results_to_repo(github_token=github_token)

        return 0

    except Exception as e:
        logger.exception(f"Benchmark run failed: {e}")
        return 1

    finally:
        if not args.keep_server and server:
            logger.info("Cleaning up server...")
            manager.delete_server(server)


def cleanup_servers(args: argparse.Namespace) -> int:
    """Clean up any leftover benchmark servers."""
    token = args.token or os.environ.get("HCLOUD_TOKEN")
    if not token:
        logger.error("Hetzner Cloud token required. Set HCLOUD_TOKEN or use --token")
        return 1

    manager = HetznerServerManager(token=token)

    # Find and delete all csp-benchmark servers
    servers = manager.client.servers.get_all()
    deleted = 0

    for server in servers:
        if server.name.startswith("csp-benchmark"):
            logger.info(f"Deleting server: {server.name}")
            manager.delete_server(server)
            deleted += 1

    logger.info(f"Cleaned up {deleted} servers")
    return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run CSP benchmarks on Hetzner Cloud",
        prog="python -m csp_benchmarks.hetzner.cli",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Run command
    run_parser = subparsers.add_parser("run", help="Run benchmarks on Hetzner Cloud")
    run_parser.add_argument("--token", help="Hetzner Cloud API token")
    run_parser.add_argument("--server-name", default="csp-benchmark-runner", help="Server name")
    run_parser.add_argument("--server-type", default="cx23", help="Hetzner server type (cx23, cx43)")
    run_parser.add_argument("--ssh-key", help="Path to SSH private key")
    run_parser.add_argument("--ssh-key-name", help="Name of SSH key in Hetzner")
    run_parser.add_argument("--branches", default="main", help="Comma-separated list of branches")
    run_parser.add_argument("--commits", help="Commit range to benchmark (e.g., HEAD~5..HEAD)")
    run_parser.add_argument("--reuse", action="store_true", help="Reuse existing server")
    run_parser.add_argument("--keep-server", action="store_true", help="Keep server after benchmarks")
    run_parser.add_argument("--push", action="store_true", help="Push results to repository")
    run_parser.add_argument("--github-token", help="GitHub token for pushing results")
    run_parser.set_defaults(func=run_benchmarks)

    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up benchmark servers")
    cleanup_parser.add_argument("--token", help="Hetzner Cloud API token")
    cleanup_parser.set_defaults(func=cleanup_servers)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
