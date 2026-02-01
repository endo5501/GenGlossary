"""Tests for path utilities."""

from pathlib import Path

import pytest

from genglossary.utils.path_utils import to_safe_relative_path


class TestToSafeRelativePath:
    """Tests for to_safe_relative_path function."""

    def test_converts_absolute_path_to_relative(self, tmp_path: Path) -> None:
        """絶対パスを相対パスに変換する"""
        file_path = tmp_path / "subdir" / "file.txt"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.touch()

        result = to_safe_relative_path(file_path, tmp_path)
        assert result == "subdir/file.txt"

    def test_returns_posix_format(self, tmp_path: Path) -> None:
        """POSIX形式（/）で返す"""
        file_path = tmp_path / "a" / "b" / "c" / "file.txt"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.touch()

        result = to_safe_relative_path(file_path, tmp_path)
        assert "/" in result
        assert "\\" not in result
        assert result == "a/b/c/file.txt"

    def test_accepts_string_paths(self, tmp_path: Path) -> None:
        """文字列パスを受け付ける"""
        file_path = tmp_path / "file.txt"
        file_path.touch()

        result = to_safe_relative_path(str(file_path), str(tmp_path))
        assert result == "file.txt"

    def test_rejects_file_outside_root(self, tmp_path: Path) -> None:
        """root外のファイルを拒否する"""
        # Create a file in a different location
        root = tmp_path / "root"
        root.mkdir()
        outside_file = tmp_path / "outside" / "file.txt"
        outside_file.parent.mkdir()
        outside_file.touch()

        with pytest.raises(ValueError, match="outside doc_root"):
            to_safe_relative_path(outside_file, root)

    def test_rejects_parent_traversal(self, tmp_path: Path) -> None:
        """親ディレクトリへのトラバーサルを拒否する"""
        root = tmp_path / "root" / "subdir"
        root.mkdir(parents=True)
        # File is in parent of root
        outside_file = tmp_path / "root" / "file.txt"
        outside_file.touch()

        with pytest.raises(ValueError, match="outside doc_root"):
            to_safe_relative_path(outside_file, root)

    def test_handles_symlinks_safely(self, tmp_path: Path) -> None:
        """シンボリックリンクを安全に処理する（resolve後に検証）"""
        root = tmp_path / "root"
        root.mkdir()
        real_file = root / "real.txt"
        real_file.touch()

        # Create symlink inside root pointing to real file
        symlink = root / "link.txt"
        symlink.symlink_to(real_file)

        # Should work - resolved path is inside root
        result = to_safe_relative_path(symlink, root)
        assert result == "real.txt"

    def test_handles_deeply_nested_paths(self, tmp_path: Path) -> None:
        """深くネストされたパスを処理する"""
        deep_path = tmp_path
        for i in range(10):
            deep_path = deep_path / f"level{i}"
        deep_path.mkdir(parents=True)
        file_path = deep_path / "file.txt"
        file_path.touch()

        result = to_safe_relative_path(file_path, tmp_path)
        expected = "/".join([f"level{i}" for i in range(10)]) + "/file.txt"
        assert result == expected
