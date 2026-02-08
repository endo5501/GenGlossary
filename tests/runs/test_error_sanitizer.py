"""Tests for error message sanitization."""

from genglossary.runs.error_sanitizer import sanitize_error_message


class TestSanitizeErrorMessage:
    """Tests for sanitize_error_message function."""

    # --- Empty message fallback ---

    def test_empty_exception_message_returns_class_name(self):
        """When str(e) is empty, fall back to exception class name."""
        error = RuntimeError()
        result = sanitize_error_message(error)
        assert result == "RuntimeError"

    def test_empty_exception_message_with_prefix(self):
        """When str(e) is empty and prefix is given, format as 'prefix (ClassName)'."""
        error = RuntimeError()
        result = sanitize_error_message(error, prefix="Failed to start")
        assert result == "Failed to start (RuntimeError)"

    def test_nonempty_exception_message_with_prefix(self):
        """When str(e) is not empty and prefix is given, format as 'prefix: msg (ClassName)'."""
        error = ValueError("bad value")
        result = sanitize_error_message(error, prefix="Validation failed")
        assert result == "Validation failed: bad value (ValueError)"

    def test_nonempty_exception_message_without_prefix(self):
        """When str(e) is not empty and no prefix, format as 'msg (ClassName)'."""
        error = ValueError("bad value")
        result = sanitize_error_message(error)
        assert result == "bad value (ValueError)"

    # --- UTF-8 normalization ---

    def test_non_utf8_bytes_are_replaced(self):
        """Non-UTF-8 characters should be replaced with replacement character."""
        # Create an exception with a message containing invalid surrogate
        msg = "error: \udcff data"
        error = RuntimeError(msg)
        result = sanitize_error_message(error)
        # Should not raise and should contain replacement character
        assert "\udcff" not in result
        assert "RuntimeError" in result

    # --- Control character removal ---

    def test_control_characters_removed(self):
        """Control characters (except newline and tab) should be removed."""
        error = RuntimeError("error\x00message\x01here")
        result = sanitize_error_message(error)
        assert "\x00" not in result
        assert "\x01" not in result
        assert "errormessagehere" in result

    def test_newline_and_tab_preserved(self):
        """Newlines and tabs should be preserved in error messages."""
        error = RuntimeError("line1\nline2\ttab")
        result = sanitize_error_message(error)
        assert "line1\nline2\ttab" in result

    def test_high_control_characters_removed(self):
        """High control characters (0x7f-0x9f) should be removed."""
        error = RuntimeError("error\x7fmsg\x80end")
        result = sanitize_error_message(error)
        assert "\x7f" not in result
        assert "\x80" not in result
        assert "errormsgend" in result

    # --- Path masking ---

    def test_unix_home_path_masked(self):
        """Unix /home/ paths should be masked."""
        error = RuntimeError("File not found: /home/user/project/file.py")
        result = sanitize_error_message(error)
        assert "/home/user" not in result
        assert "<path>" in result

    def test_unix_users_path_masked(self):
        """macOS /Users/ paths should be masked."""
        error = RuntimeError("Error at /Users/john/Work/app/main.py")
        result = sanitize_error_message(error)
        assert "/Users/john" not in result
        assert "<path>" in result

    def test_unix_var_path_masked(self):
        """/var/ paths should be masked."""
        error = RuntimeError("Log at /var/log/app/error.log")
        result = sanitize_error_message(error)
        assert "/var/log" not in result
        assert "<path>" in result

    def test_unix_tmp_path_masked(self):
        """/tmp/ multi-segment paths should be masked."""
        error = RuntimeError("Temp file: /tmp/session/data.tmp")
        result = sanitize_error_message(error)
        assert "/tmp/session" not in result
        assert "<path>" in result

    def test_unix_etc_path_masked(self):
        """/etc/ paths should be masked."""
        error = RuntimeError("Config: /etc/app/config.yaml")
        result = sanitize_error_message(error)
        assert "/etc/app" not in result
        assert "<path>" in result

    def test_unix_opt_path_masked(self):
        """/opt/ paths should be masked."""
        error = RuntimeError("Binary: /opt/tools/bin/app")
        result = sanitize_error_message(error)
        assert "/opt/tools" not in result
        assert "<path>" in result

    def test_windows_path_masked(self):
        """Windows drive paths should be masked."""
        error = RuntimeError(r"File: C:\Users\john\project\file.py")
        result = sanitize_error_message(error)
        assert r"C:\Users" not in result
        assert "<path>" in result

    def test_url_not_masked(self):
        """HTTP/HTTPS URLs should not be masked."""
        error = RuntimeError("Failed to connect to http://localhost:11434/api/generate")
        result = sanitize_error_message(error)
        assert "http://localhost:11434/api/generate" in result

    def test_https_url_not_masked(self):
        """HTTPS URLs should not be masked."""
        error = RuntimeError("SSL error for https://api.example.com/v1/chat")
        result = sanitize_error_message(error)
        assert "https://api.example.com/v1/chat" in result

    def test_single_segment_path_not_masked(self):
        """Single segment paths like /tmp should not be masked."""
        error = RuntimeError("Cannot write to /tmp")
        result = sanitize_error_message(error)
        assert "/tmp" in result

    def test_windows_lowercase_drive_letter_masked(self):
        """Lowercase Windows drive letters should also be masked."""
        error = RuntimeError(r"File: c:\users\john\project\file.py")
        result = sanitize_error_message(error)
        assert r"c:\users" not in result
        assert "<path>" in result

    def test_url_with_sensitive_path_prefix_not_masked(self):
        """URLs containing /home/ or /Users/ in path should not be masked."""
        error = RuntimeError("Error at https://host/home/user/data")
        result = sanitize_error_message(error)
        assert "https://host/home/user/data" in result

    # --- Length truncation ---

    def test_message_within_limit_not_truncated(self):
        """Messages within limit should not be truncated."""
        error = RuntimeError("short error")
        result = sanitize_error_message(error, max_length=1024)
        assert result == "short error (RuntimeError)"

    def test_message_exceeding_limit_truncated(self):
        """Messages exceeding limit should be truncated with indicator."""
        long_msg = "x" * 2000
        error = RuntimeError(long_msg)
        result = sanitize_error_message(error, max_length=100)
        assert len(result) <= 100
        assert result.endswith("...(truncated)")

    def test_custom_max_length(self):
        """Custom max_length should be respected."""
        long_msg = "a" * 500
        error = RuntimeError(long_msg)
        result = sanitize_error_message(error, max_length=50)
        assert len(result) <= 50

    def test_default_max_length_is_1024(self):
        """Default max_length should be 1024."""
        long_msg = "b" * 2000
        error = RuntimeError(long_msg)
        result = sanitize_error_message(error)
        assert len(result) <= 1024

    def test_max_length_smaller_than_truncation_suffix(self):
        """When max_length is smaller than truncation suffix, still respect limit."""
        long_msg = "x" * 100
        error = RuntimeError(long_msg)
        result = sanitize_error_message(error, max_length=5)
        assert len(result) <= 5

    # --- Combined scenarios ---

    def test_path_masked_and_truncated(self):
        """Both path masking and truncation should work together."""
        long_path = "/home/user/" + "a" * 2000 + "/file.py"
        error = RuntimeError(f"Error: {long_path}")
        result = sanitize_error_message(error, max_length=100)
        assert "/home/user" not in result
        assert len(result) <= 100

    def test_control_chars_and_path_in_same_message(self):
        """Control chars removed and paths masked in same message."""
        error = RuntimeError("err\x00or at /home/user/project/file.py")
        result = sanitize_error_message(error)
        assert "\x00" not in result
        assert "/home/user" not in result
        assert "<path>" in result

    def test_prefix_with_path_masking(self):
        """Prefix should work correctly with path masking."""
        error = OSError("No such file: /Users/dev/app/config.json")
        result = sanitize_error_message(error, prefix="Config load failed")
        assert result.startswith("Config load failed:")
        assert "/Users/dev" not in result
        assert "<path>" in result
        assert "(OSError)" in result
