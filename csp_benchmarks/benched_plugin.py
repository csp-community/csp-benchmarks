"""Benched metadata normalization for the CSP benchmark suite."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from typing import Any

from benched.hooks import RunHookContext, hookimpl

MEMORY_ALIASES = {3.5: 4.0, 15.5: 16.0}


def _fingerprint(metadata: dict[str, Any]) -> str:
    payload = json.dumps(metadata, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode()).hexdigest()


@hookimpl
def benched_enrich_run(context: RunHookContext) -> None:
    """Normalize VM memory buckets to their nominal capacities."""
    metadata = context.run.machine.metadata
    memory_gib = metadata.get("memory_gib")
    normalized = MEMORY_ALIASES.get(memory_gib)
    if normalized is None:
        return
    normalized_metadata = {**metadata, "memory_gib": normalized}
    machine = replace(context.run.machine, metadata=normalized_metadata, fingerprint=_fingerprint(normalized_metadata))
    context.run = replace(context.run, machine=machine)
