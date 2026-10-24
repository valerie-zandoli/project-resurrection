"""More model-free tests for scripts/check_key.py:  odd .env files, odd keys, broken connections.

Each case was found by trying it against the script (2026-10-22).  Every key here is fake.  The
in-process tests use a fake opener, and tests/conftest.py blocks the network.  The subprocess tests
run the script the way a person does and stop before any network call.
"""
import ast
import http.client
import io
import json
import os
import re
import subprocess
import sys
import urllib.error
from pathlib import Path

import pytest

import test_check_key as base  # same folder; reuses the module loader and the fake key

check_key = base.check_key
FAKE_KEY = base.FAKE_KEY
SCRIPT = Path(base.REPO) / "scripts" / "check_key.py"
GOOD_REPLY = {"content": [{"type": "text", "text": "Hello there, nice to meet you"}]}


def write_env(tmp_path, content):
    path = tmp_path / ".env"
    path.write_bytes(content if isinstance(content, bytes) else content.encode("utf-8"))
    return str(path)


def run_main(env_path, opener, environ=None):
    return check_key.main(["--env", env_path], opener=opener, environ={} if environ is None else environ)


def no_call(*args, **kwargs):
    pytest.fail("the script must stop before it sends a request")


class Capture:
    """An opener that records the key it was asked to send and returns a good reply."""

    def __init__(self):
        self.sent_keys = []

    def __call__(self, request, timeout):
        self.sent_keys.append({k.lower(): v for k, v in request.header_items()}["x-api-key"])
        return base.FakeResponse(GOOD_REPLY)


# --- broken connections -----------------------------------------------------------------------


class CutShortResponse(base.FakeResponse):
    def read(self, size=-1):
        raise http.client.IncompleteRead(b'{"content":[{"type":"te', 477)


def test_reply_cut_short_exits_3_not_a_crash(tmp_path, capsys):
    code = run_main(write_env(tmp_path, f"ANTHROPIC_API_KEY={FAKE_KEY}\n"), lambda *a, **k: CutShortResponse(None))
    out = capsys.readouterr()
    assert code == 3
    assert "full reply" in out.out
    assert FAKE_KEY not in out.out + out.err


def test_server_that_hangs_up_exits_3(tmp_path, capsys):
    def opener(request, timeout):
        raise http.client.RemoteDisconnected("Remote end closed connection without response")

    code = run_main(write_env(tmp_path, f"ANTHROPIC_API_KEY={FAKE_KEY}\n"), opener)
    assert code == 3
    assert FAKE_KEY not in capsys.readouterr().out


def test_unexpected_exception_exits_6_and_never_exits_1(tmp_path, capsys):
    def opener(request, timeout):
        raise RuntimeError(f"boom {FAKE_KEY}")

    code = run_main(write_env(tmp_path, f"ANTHROPIC_API_KEY={FAKE_KEY}\n"), opener)
    out = capsys.readouterr()
    assert code == 6  # exit 1 is reserved for "no key found"
    assert "RuntimeError" in out.out
    assert FAKE_KEY not in out.out + out.err


def test_oversized_reply_exits_4(tmp_path, capsys):
    class Huge(base.FakeResponse):
        def read(self, size=-1):
            return b"x" * (check_key.MAX_BODY + 1)

    code = run_main(write_env(tmp_path, f"ANTHROPIC_API_KEY={FAKE_KEY}\n"), lambda *a, **k: Huge(None))
    assert code == 4
    assert "larger than expected" in capsys.readouterr().out


def test_error_detail_is_capped_and_the_key_is_removed(tmp_path, capsys):
    body = json.dumps({"error": {"type": "api_error", "message": f"{FAKE_KEY} " + "x" * 5000}}).encode()

    def opener(request, timeout):
        raise urllib.error.HTTPError(request.full_url, 500, "Server Error", {}, io.BytesIO(body))

    code = run_main(write_env(tmp_path, f"ANTHROPIC_API_KEY={FAKE_KEY}\n"), opener)
    out = capsys.readouterr().out
    assert code == 2
    assert FAKE_KEY not in out
    assert len(out) < 1000


# --- odd .env files ----------------------------------------------------------------------------


def test_utf16_env_file_exits_5_without_a_crash(tmp_path, capsys):
    """PowerShell's `echo ... > .env` writes UTF-16."""
    code = run_main(write_env(tmp_path, f"ANTHROPIC_API_KEY={FAKE_KEY}\n".encode("utf-16")), no_call)
    assert code == 5
    assert "UTF-8" in capsys.readouterr().out


def test_utf8_byte_order_mark_is_ignored(tmp_path):
    seen = Capture()
    code = run_main(write_env(tmp_path, b"\xef\xbb\xbf" + f"ANTHROPIC_API_KEY={FAKE_KEY}\n".encode()), seen)
    assert code == 0
    assert seen.sent_keys == [FAKE_KEY]


def test_inline_comment_is_not_part_of_the_key(tmp_path):
    seen = Capture()
    code = run_main(write_env(tmp_path, f"ANTHROPIC_API_KEY={FAKE_KEY}   # pursuit key\n"), seen)
    assert code == 0
    assert seen.sent_keys == [FAKE_KEY]


def test_quoted_key_with_a_trailing_comment(tmp_path):
    seen = Capture()
    code = run_main(write_env(tmp_path, f"ANTHROPIC_API_KEY=\"{FAKE_KEY}\" # note\n"), seen)
    assert code == 0
    assert seen.sent_keys == [FAKE_KEY]


def test_duplicate_lines_use_the_last_one_and_say_so(tmp_path, capsys):
    seen = Capture()
    code = run_main(write_env(tmp_path, f"ANTHROPIC_API_KEY=old-key\nANTHROPIC_API_KEY={FAKE_KEY}\n"), seen)
    out = capsys.readouterr().out
    assert code == 0
    assert seen.sent_keys == [FAKE_KEY]
    assert "2 times" in out and "last one is used" in out


def test_the_env_file_wins_over_the_environment_variable(tmp_path):
    seen = Capture()
    code = run_main(write_env(tmp_path, f"ANTHROPIC_API_KEY={FAKE_KEY}\n"), seen, environ={"ANTHROPIC_API_KEY": "other-key"})
    assert code == 0
    assert seen.sent_keys == [FAKE_KEY]


# --- keys that cannot be sent ------------------------------------------------------------------


@pytest.mark.parametrize("bad", [FAKE_KEY + "”", "“" + FAKE_KEY, "sk-ant test-key", "sk-ant-café"])
def test_unsendable_key_exits_5_before_any_call_and_is_not_printed(tmp_path, capsys, bad):
    code = run_main(write_env(tmp_path, f"ANTHROPIC_API_KEY={bad}\n"), no_call)
    out = capsys.readouterr()
    assert code == 5
    assert "Invalid API response" not in out.out  # the cause is the key, not the reply
    assert bad not in out.out + out.err


def test_unsendable_key_from_the_environment_is_also_caught(tmp_path, capsys):
    code = run_main(write_env(tmp_path, ""), no_call, environ={"ANTHROPIC_API_KEY": "bad key"})
    assert code == 5


# --- the exit-code contract --------------------------------------------------------------------


def test_every_exit_code_the_script_returns_is_documented():
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    returned = {
        node.value.value
        for func in ast.walk(tree) if isinstance(func, ast.FunctionDef) and func.name in {"_run", "main"}
        for node in ast.walk(func)
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, int)
    }
    documented = {int(n) for n in re.findall(r"(\d) = ", ast.get_docstring(tree))}
    assert returned <= documented
    assert returned == {0, 1, 2, 3, 4, 5, 6}


# --- the script as a person runs it (no network is reached) ------------------------------------


def run_script(*args, env=None):
    clean_env = {"PATH": os.environ.get("PATH", "")}
    clean_env.update(env or {})
    return subprocess.run([sys.executable, "-I", str(SCRIPT), *args], capture_output=True, text=True, env=clean_env, timeout=30)


def test_script_with_no_key_exits_1_and_points_to_the_example(tmp_path):
    result = run_script("--env", str(tmp_path / "missing.env"))
    assert result.returncode == 1
    assert ".env.example" in result.stdout
    assert "Traceback" not in result.stderr


def test_script_with_a_curly_quote_exits_5_with_no_traceback(tmp_path):
    result = run_script("--env", write_env(tmp_path, f"ANTHROPIC_API_KEY={FAKE_KEY}”\n"))
    assert result.returncode == 5
    assert "Traceback" not in result.stderr
    assert FAKE_KEY not in result.stdout + result.stderr


def test_script_help_exits_0():
    assert run_script("--help").returncode == 0
