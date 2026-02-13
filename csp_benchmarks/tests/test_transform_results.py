"""Tests for transform_results module."""

import json
from pathlib import Path

from csp_benchmarks.transform_results import (
    CSP_VERSION_TO_COMMIT,
    extract_csp_version,
    transform_all_results,
    transform_result_file,
)


class TestExtractCspVersion:
    """Test extract_csp_version function."""

    def test_extract_from_standard_filename(self):
        """Test extracting CSP version from standard ASV filename."""
        assert extract_csp_version("01ce9cfc-virtualenv-py3.12-csp0.13.0.json") == "0.13.0"
        assert extract_csp_version("abcd1234-virtualenv-py3.11-csp0.12.0.json") == "0.12.0"
        assert extract_csp_version("12345678-virtualenv-py3.13-csp0.14.0.json") == "0.14.0"

    def test_extract_with_patch_version(self):
        """Test extracting CSP versions with patch numbers."""
        assert extract_csp_version("01ce9cfc-virtualenv-py3.12-csp0.13.1.json") == "0.13.1"
        assert extract_csp_version("01ce9cfc-virtualenv-py3.12-csp0.13.2.json") == "0.13.2"

    def test_returns_none_for_transformed_file(self):
        """Test that already-transformed files return None."""
        # Transformed files don't have -csp in the name
        assert extract_csp_version("277a3200-virtualenv-py3.12.json") is None

    def test_returns_none_for_machine_json(self):
        """Test that machine.json returns None."""
        assert extract_csp_version("machine.json") is None

    def test_returns_none_for_invalid_format(self):
        """Test that invalid filenames return None."""
        assert extract_csp_version("random-file.json") is None
        assert extract_csp_version("no-version.json") is None


class TestCspVersionToCommit:
    """Test CSP_VERSION_TO_COMMIT mapping."""

    def test_all_commits_are_valid_hashes(self):
        """Test that all commit hashes are valid 40-char hex strings."""
        for version, commit in CSP_VERSION_TO_COMMIT.items():
            assert len(commit) == 40, f"Commit for {version} is not 40 chars"
            assert all(c in "0123456789abcdef" for c in commit), f"Commit for {version} has invalid chars"

    def test_known_versions_exist(self):
        """Test that expected CSP versions are in the mapping."""
        expected_versions = ["0.12.0", "0.13.0", "0.13.1", "0.13.2", "0.14.0"]
        for version in expected_versions:
            assert version in CSP_VERSION_TO_COMMIT, f"Missing version {version}"

    def test_commits_are_unique(self):
        """Test that all commit hashes are unique."""
        commits = list(CSP_VERSION_TO_COMMIT.values())
        assert len(commits) == len(set(commits)), "Duplicate commit hashes found"


class TestTransformResultFile:
    """Test transform_result_file function."""

    def _create_test_result(self, tmp_path: Path, filename: str, csp_version: str) -> Path:
        """Create a test result file."""
        machine_dir = tmp_path / "test-machine"
        machine_dir.mkdir(exist_ok=True)

        result_file = machine_dir / filename
        result_data = {
            "commit_hash": "01ce9cfc12345678901234567890123456789012",
            "env_name": f"virtualenv-py3.12-csp{csp_version}",
            "params": {
                "arch": "x86_64",
                "cpu": "Test CPU",
                "machine": "test-machine",
                "python": "3.12",
                "csp": csp_version,
            },
            "requirements": {"csp": csp_version},
            "results": {"bench_test.time_test": [0.001, 0.002]},
        }
        with open(result_file, "w") as f:
            json.dump(result_data, f)

        return result_file

    def test_transforms_filename_correctly(self, tmp_path):
        """Test that filename is transformed to use real commit hash."""
        src = self._create_test_result(tmp_path, "01ce9cfc-virtualenv-py3.12-csp0.13.0.json", "0.13.0")

        new_path = transform_result_file(src, tmp_path)

        assert new_path is not None
        assert new_path.name == "0d92361f-virtualenv-py3.12.json"
        assert new_path.exists()
        assert not src.exists()  # Old file removed

    def test_updates_commit_hash_in_json(self, tmp_path):
        """Test that commit_hash field is updated in JSON."""
        src = self._create_test_result(tmp_path, "01ce9cfc-virtualenv-py3.12-csp0.13.0.json", "0.13.0")

        new_path = transform_result_file(src, tmp_path)

        with open(new_path) as f:
            data = json.load(f)

        assert data["commit_hash"] == CSP_VERSION_TO_COMMIT["0.13.0"]

    def test_removes_csp_from_env_name(self, tmp_path):
        """Test that csp is removed from env_name field."""
        src = self._create_test_result(tmp_path, "01ce9cfc-virtualenv-py3.12-csp0.13.0.json", "0.13.0")

        new_path = transform_result_file(src, tmp_path)

        with open(new_path) as f:
            data = json.load(f)

        assert data["env_name"] == "virtualenv-py3.12"
        assert "csp" not in data["env_name"]

    def test_removes_csp_from_params(self, tmp_path):
        """Test that csp is removed from params dict."""
        src = self._create_test_result(tmp_path, "01ce9cfc-virtualenv-py3.12-csp0.13.0.json", "0.13.0")

        new_path = transform_result_file(src, tmp_path)

        with open(new_path) as f:
            data = json.load(f)

        assert "csp" not in data["params"]
        # Other params should remain
        assert data["params"]["python"] == "3.12"
        assert data["params"]["machine"] == "test-machine"

    def test_preserves_requirements(self, tmp_path):
        """Test that requirements dict is preserved (needed for install)."""
        src = self._create_test_result(tmp_path, "01ce9cfc-virtualenv-py3.12-csp0.13.0.json", "0.13.0")

        new_path = transform_result_file(src, tmp_path)

        with open(new_path) as f:
            data = json.load(f)

        assert data["requirements"]["csp"] == "0.13.0"

    def test_skips_machine_json(self, tmp_path):
        """Test that machine.json is skipped."""
        machine_dir = tmp_path / "test-machine"
        machine_dir.mkdir()
        machine_file = machine_dir / "machine.json"
        machine_file.write_text("{}")

        result = transform_result_file(machine_file, tmp_path)

        assert result is None

    def test_skips_unknown_csp_version(self, tmp_path):
        """Test that unknown CSP versions are skipped."""
        src = self._create_test_result(tmp_path, "01ce9cfc-virtualenv-py3.12-csp9.99.99.json", "9.99.99")

        result = transform_result_file(src, tmp_path)

        assert result is None
        assert src.exists()  # Original file not deleted

    def test_skips_already_transformed_file(self, tmp_path):
        """Test that already-transformed files are skipped."""
        machine_dir = tmp_path / "test-machine"
        machine_dir.mkdir()

        # Create a file that looks already transformed (no -csp in name)
        transformed_file = machine_dir / "277a3200-virtualenv-py3.12.json"
        transformed_file.write_text('{"commit_hash": "277a3200c601c4c2982b871cfea8ba9085e8640b"}')

        result = transform_result_file(transformed_file, tmp_path)

        assert result is None

    def test_all_known_versions(self, tmp_path):
        """Test transformation works for all known CSP versions."""
        for version, expected_commit in CSP_VERSION_TO_COMMIT.items():
            filename = f"01ce9cfc-virtualenv-py3.12-csp{version}.json"
            src = self._create_test_result(tmp_path, filename, version)

            new_path = transform_result_file(src, tmp_path)

            assert new_path is not None
            assert new_path.name == f"{expected_commit[:8]}-virtualenv-py3.12.json"

            with open(new_path) as f:
                data = json.load(f)
            assert data["commit_hash"] == expected_commit


class TestTransformAllResults:
    """Test transform_all_results function."""

    def _create_result_file(self, machine_dir: Path, filename: str, csp_version: str):
        """Helper to create a result file."""
        result_file = machine_dir / filename
        result_data = {
            "commit_hash": "01ce9cfc12345678901234567890123456789012",
            "env_name": f"virtualenv-py3.12-csp{csp_version}",
            "params": {"csp": csp_version, "python": "3.12"},
            "requirements": {"csp": csp_version},
        }
        with open(result_file, "w") as f:
            json.dump(result_data, f)

    def test_transforms_multiple_machines(self, tmp_path):
        """Test transformation across multiple machine directories."""
        machine1 = tmp_path / "machine-1"
        machine2 = tmp_path / "machine-2"
        machine1.mkdir()
        machine2.mkdir()

        self._create_result_file(machine1, "01ce9cfc-virtualenv-py3.12-csp0.13.0.json", "0.13.0")
        self._create_result_file(machine2, "01ce9cfc-virtualenv-py3.12-csp0.14.0.json", "0.14.0")

        count = transform_all_results(tmp_path)

        assert count == 2
        assert (machine1 / "0d92361f-virtualenv-py3.12.json").exists()
        assert (machine2 / "952de074-virtualenv-py3.12.json").exists()

    def test_transforms_multiple_versions_same_machine(self, tmp_path):
        """Test transformation of multiple versions in same machine dir."""
        machine_dir = tmp_path / "test-machine"
        machine_dir.mkdir()

        for version in ["0.12.0", "0.13.0", "0.14.0"]:
            self._create_result_file(machine_dir, f"01ce9cfc-virtualenv-py3.12-csp{version}.json", version)

        count = transform_all_results(tmp_path)

        assert count == 3

    def test_preserves_machine_json(self, tmp_path):
        """Test that machine.json files are preserved."""
        machine_dir = tmp_path / "test-machine"
        machine_dir.mkdir()

        machine_file = machine_dir / "machine.json"
        machine_file.write_text('{"machine": "test"}')

        self._create_result_file(machine_dir, "01ce9cfc-virtualenv-py3.12-csp0.13.0.json", "0.13.0")

        transform_all_results(tmp_path)

        assert machine_file.exists()
        assert json.loads(machine_file.read_text()) == {"machine": "test"}

    def test_skips_non_directory_entries(self, tmp_path):
        """Test that non-directory entries in results dir are skipped."""
        # Create a file at root level (like benchmarks.json)
        (tmp_path / "benchmarks.json").write_text("{}")

        machine_dir = tmp_path / "test-machine"
        machine_dir.mkdir()
        self._create_result_file(machine_dir, "01ce9cfc-virtualenv-py3.12-csp0.13.0.json", "0.13.0")

        # Should not raise and should transform the valid file
        count = transform_all_results(tmp_path)

        assert count == 1

    def test_idempotent_transformation(self, tmp_path):
        """Test that running transform twice doesn't break anything."""
        machine_dir = tmp_path / "test-machine"
        machine_dir.mkdir()

        self._create_result_file(machine_dir, "01ce9cfc-virtualenv-py3.12-csp0.13.0.json", "0.13.0")

        # First run
        count1 = transform_all_results(tmp_path)
        assert count1 == 1

        # Second run - already transformed files should be skipped
        count2 = transform_all_results(tmp_path)
        assert count2 == 0

        # File should still exist and be valid
        transformed = machine_dir / "0d92361f-virtualenv-py3.12.json"
        assert transformed.exists()
        with open(transformed) as f:
            data = json.load(f)
        assert data["commit_hash"] == CSP_VERSION_TO_COMMIT["0.13.0"]
