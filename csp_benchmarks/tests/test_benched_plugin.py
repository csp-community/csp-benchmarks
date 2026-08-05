"""Tests for CSP-specific Benched metadata normalization."""

import hashlib
import json
from dataclasses import replace
from types import SimpleNamespace

import pytest
from benched.storage import read_runs

from csp_benchmarks.benched_plugin import benched_enrich_run


@pytest.fixture
def current_run():
    return next(stored.run for stored in read_runs("csp_benchmarks/benched-results") if stored.run.provenance.source_format == "pytest-benchmark")


@pytest.mark.parametrize(("recorded", "expected"), [(3.5, 4.0), (15.5, 16.0)])
def test_normalizes_memory_aliases_and_fingerprint(current_run, recorded, expected):
    metadata = {**current_run.machine.metadata, "memory_gib": recorded}
    machine = replace(current_run.machine, fingerprint="original", metadata=metadata)
    context = SimpleNamespace(run=replace(current_run, machine=machine))

    benched_enrich_run(context)

    assert context.run.machine.metadata["memory_gib"] == expected
    payload = json.dumps(context.run.machine.metadata, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    assert context.run.machine.fingerprint == hashlib.sha256(payload.encode()).hexdigest()


def test_preserves_other_memory_buckets(current_run):
    context = SimpleNamespace(run=current_run)

    benched_enrich_run(context)

    assert context.run is current_run
