import os
import tempfile

import pytest

from shared.config import load_lines


class TestLoadLines:
    def test_load_valid_file(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("python\njavascript\nrust\n")
        result = load_lines(str(f))
        assert result == ["python", "javascript", "rust"]

    def test_skip_comments(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("# this is a comment\npython\n# another\nrust\n")
        result = load_lines(str(f))
        assert result == ["python", "rust"]

    def test_skip_empty_lines(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("python\n\n\nrust\n\n")
        result = load_lines(str(f))
        assert result == ["python", "rust"]

    def test_strip_whitespace(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("  python  \n  rust  \n")
        result = load_lines(str(f))
        assert result == ["python", "rust"]

    def test_nonexistent_file(self):
        result = load_lines("/nonexistent/path/file.txt")
        assert result == []

    def test_empty_file(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("")
        result = load_lines(str(f))
        assert result == []
