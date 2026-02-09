"""Tests for data directory isolation fixture.

Verifies that GENGLOSSARY_DATA_DIR and GENGLOSSARY_REGISTRY_PATH
are redirected to tmp_path to prevent test data from leaking
into the production directory (~/.genglossary/).
"""

import os
from pathlib import Path


class TestIsolateDataDir:
    """Tests for isolate_data_dir fixture."""

    def test_genglossary_data_dir_is_set(self):
        """GENGLOSSARY_DATA_DIR should be set to a temp directory."""
        data_dir = os.environ.get("GENGLOSSARY_DATA_DIR")
        assert data_dir is not None, "GENGLOSSARY_DATA_DIR should be set"

    def test_genglossary_data_dir_is_not_home(self):
        """GENGLOSSARY_DATA_DIR should NOT point to ~/.genglossary."""
        data_dir = os.environ.get("GENGLOSSARY_DATA_DIR", "")
        home_genglossary = str(Path.home() / ".genglossary")
        assert not data_dir.startswith(home_genglossary), (
            f"GENGLOSSARY_DATA_DIR should not point to production directory: {data_dir}"
        )

    def test_genglossary_registry_path_is_set(self):
        """GENGLOSSARY_REGISTRY_PATH should be set to a temp path."""
        registry_path = os.environ.get("GENGLOSSARY_REGISTRY_PATH")
        assert registry_path is not None, "GENGLOSSARY_REGISTRY_PATH should be set"

    def test_genglossary_registry_path_is_not_home(self):
        """GENGLOSSARY_REGISTRY_PATH should NOT point to ~/.genglossary."""
        registry_path = os.environ.get("GENGLOSSARY_REGISTRY_PATH", "")
        home_genglossary = str(Path.home() / ".genglossary")
        assert not registry_path.startswith(home_genglossary), (
            f"GENGLOSSARY_REGISTRY_PATH should not point to production directory: {registry_path}"
        )

    def test_data_dir_exists(self):
        """GENGLOSSARY_DATA_DIR directory should exist."""
        data_dir = os.environ.get("GENGLOSSARY_DATA_DIR", "")
        assert Path(data_dir).is_dir(), (
            f"GENGLOSSARY_DATA_DIR should be an existing directory: {data_dir}"
        )
