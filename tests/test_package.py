"""
Smoke tests for the gambix package itself.

These run on every CI push and verify the package is importable,
the version string is set, and the CI gate scripts behave correctly.
These are the only tests that exist at the chore/ci-setup stage —
more tests are added in subsequent branches.
"""

from __future__ import annotations

import importlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

# Helper path to CI scripts
CI_SCRIPTS_DIR = Path(__file__).parent.parent / "scripts" / "ci"
LICENCE_CHECKER = str(CI_SCRIPTS_DIR / "check_licence_tiers.py")


# ---------------------------------------------------------------------------
# Package import & metadata
# ---------------------------------------------------------------------------

class TestPackageImport:
    def test_gambix_importable(self) -> None:
        """gambix package must be importable after `pip install -e .`"""
        gambix = importlib.import_module("gambix")
        assert gambix is not None

    def test_version_string_set(self) -> None:
        """__version__ must be a non-empty semver-like string."""
        import gambix
        assert hasattr(gambix, "__version__")
        parts = gambix.__version__.split(".")
        assert len(parts) == 3, f"Expected semver, got {gambix.__version__!r}"
        assert all(p.isdigit() for p in parts)

    def test_licence_attribute(self) -> None:
        """Licence must be GPLv3 or later."""
        import gambix
        assert "GPL-3.0" in gambix.__license__


# ---------------------------------------------------------------------------
# CI gate: check_licence_tiers.py
# ---------------------------------------------------------------------------

class TestLicenceTierGate:
    def test_passes_when_no_manifest(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Gate must exit 0 (pass) when MANIFEST.jsonl does not exist yet."""
        monkeypatch.chdir(tmp_path)
        result = subprocess.run(
            [sys.executable, LICENCE_CHECKER],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr

    def test_passes_with_tier_a_only(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Gate must exit 0 when manifest contains only Tier A entries."""
        monkeypatch.chdir(tmp_path)
        manifest = tmp_path / "data" / "MANIFEST.jsonl"
        manifest.parent.mkdir(parents=True)
        manifest.write_text(
            json.dumps({
                "path": "data/processed/lichess_games.parquet",
                "source": "lichess",
                "licence_tier": "A",
                "retrieved_on": "2026-10-01",
                "sha256": "abc123",
            }) + "\n"
        )
        result = subprocess.run(
            [sys.executable, LICENCE_CHECKER],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr

    def test_fails_with_tier_c_in_release_folder(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Gate must exit 1 when Tier C data is found in data/processed/."""
        monkeypatch.chdir(tmp_path)
        manifest = tmp_path / "data" / "MANIFEST.jsonl"
        manifest.parent.mkdir(parents=True)
        manifest.write_text(
            json.dumps({
                "path": "data/processed/chesscom_games.parquet",
                "source": "chesscom",
                "licence_tier": "C",
                "retrieved_on": "2026-10-01",
                "sha256": "def456",
            }) + "\n"
        )
        result = subprocess.run(
            [sys.executable, LICENCE_CHECKER],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1, "Expected gate to fail on Tier C data"
        assert "CI GATE FAILED" in result.stdout

    def test_tier_c_outside_processed_is_allowed(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Tier C data in data/raw/ (not release folder) is allowed."""
        monkeypatch.chdir(tmp_path)
        manifest = tmp_path / "data" / "MANIFEST.jsonl"
        manifest.parent.mkdir(parents=True)
        manifest.write_text(
            json.dumps({
                "path": "data/raw/chesscom_games.pgn.zst",
                "source": "chesscom",
                "licence_tier": "C",
                "retrieved_on": "2026-10-01",
                "sha256": "def456",
            }) + "\n"
        )
        result = subprocess.run(
            [sys.executable, LICENCE_CHECKER],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr

    def test_invalid_json_in_manifest_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Malformed JSON lines in MANIFEST.jsonl must cause gate to exit 1."""
        monkeypatch.chdir(tmp_path)
        manifest = tmp_path / "data" / "MANIFEST.jsonl"
        manifest.parent.mkdir(parents=True)
        manifest.write_text("THIS IS NOT JSON\n")
        result = subprocess.run(
            [sys.executable, LICENCE_CHECKER],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1


# ---------------------------------------------------------------------------
# Project structure sanity checks
# ---------------------------------------------------------------------------

class TestProjectStructure:
    ROOT = Path(__file__).parent.parent

    def test_pyproject_toml_exists(self) -> None:
        assert (self.ROOT / "pyproject.toml").is_file()

    def test_gitignore_exists(self) -> None:
        assert (self.ROOT / ".gitignore").is_file()

    def test_pre_commit_config_exists(self) -> None:
        assert (self.ROOT / ".pre-commit-config.yaml").is_file()

    def test_ci_workflow_exists(self) -> None:
        assert (self.ROOT / ".github" / "workflows" / "ci.yml").is_file()

    def test_release_workflow_exists(self) -> None:
        assert (self.ROOT / ".github" / "workflows" / "release.yml").is_file()

    def test_licence_is_gplv3(self) -> None:
        licence_text = (self.ROOT / "LICENSE").read_text()
        assert "GNU GENERAL PUBLIC LICENSE" in licence_text
        assert "Version 3" in licence_text

    def test_data_raw_is_gitignored(self) -> None:
        """Verify .gitignore contains data/raw/ to prevent accidental commits."""
        gitignore = (self.ROOT / ".gitignore").read_text()
        assert "data/raw/" in gitignore

    def test_models_dir_is_gitignored(self) -> None:
        gitignore = (self.ROOT / ".gitignore").read_text()
        assert "models/" in gitignore

    def test_env_files_are_gitignored(self) -> None:
        gitignore = (self.ROOT / ".gitignore").read_text()
        assert ".env" in gitignore
