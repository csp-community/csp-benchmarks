#!/usr/bin/env python3
"""CSP benchmark command-line entry point."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path

from benched.cli import main as benched_main


def _arguments(argv: Sequence[str]) -> list[str]:
    arguments = list(argv)
    if not arguments or arguments[0] == "serve" or "--pyproject" in arguments:
        return arguments
    local_config = Path.cwd() / "pyproject.toml"
    if local_config.is_file() and "[tool.benched" in local_config.read_text(encoding="utf-8"):
        return [*arguments, "--pyproject", str(local_config)]
    packaged_config = Path(__file__).with_name("benched.toml")
    if "--results-dir" not in arguments:
        arguments.extend(["--results-dir", str(Path.cwd() / ".benched" / "results")])
    if arguments[0] in {"list", "run"}:
        arguments.append("--override-ini=python_files=bench_*.py")
    return [*arguments, "--pyproject", str(packaged_config)]


def main(argv: Sequence[str] | None = None) -> int:
    """Run Benched with the CSP benchmark suite configuration."""
    return benched_main(_arguments(argv if argv is not None else sys.argv[1:]))


if __name__ == "__main__":
    sys.exit(main())
