"""Model-free tests for scripts/check_key.py.

No test reads the real .env, uses a real key, or opens a network connection:  every call goes through a fake opener.
"""
import importlib.util
import io
import json
import urllib.error
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("check_key", REPO / "scripts" / "check_key.py")
check_key = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_key)

FAKE_KEY = "sk-ant-test-0000000000000000"


class FakeResponse:
    status = 200

    def __init__(self, payload):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self, size=-1):
        return json.dumps(self._payload).encode("utf-8")


def env_file(tmp_path, text):
    path = tmp_path / ".env"
    path.write_text(text)
    return str(path)


def test_reads_key_and_ignores_comments_quotes_and_export(tmp_path):
    assert check_key.read_env_key(env_file(tmp_path, f"# note\nOTHER=1\nexport ANTHROPIC_API_KEY='{FAKE_KEY}'\n")) == FAKE_KEY
    assert check_key.read_env_key(env_file(tmp_path, f"ANTHROPIC_API_KEY={FAKE_KEY}\n")) == FAKE_KEY


def test_blank_or_missing_key_reads_as_none(tmp_path):
    assert check_key.read_env_key(env_file(tmp_path, "ANTHROPIC_API_KEY=\n")) is None
    assert check_key.read_env_key(tmp_path / "missing.env") is None


def test_no_key_exits_1_and_points_to_env_example(tmp_path, capsys):
    code = check_key.main(["--env", env_file(tmp_path, "ANTHROPIC_API_KEY=\n")], opener=None, environ={})
    assert code == 1
    assert ".env.example" in capsys.readouterr().out


def test_success_sends_the_key_and_model_and_never_prints_the_key(tmp_path, capsys):
    seen = {}

    def opener(request, timeout):
        seen["headers"] = {k.lower(): v for k, v in request.header_items()}
        seen["body"] = json.loads(request.data)
        return FakeResponse({"content": [{"type": "text", "text": "Hello there, nice to meet you"}]})

    code = check_key.main(["--env", env_file(tmp_path, f"ANTHROPIC_API_KEY={FAKE_KEY}\n")], opener=opener, environ={})
    out = capsys.readouterr()
    assert code == 0
    assert "HTTP 200" in out.out and "Hello there" in out.out
    assert FAKE_KEY not in out.out + out.err
    assert seen["headers"]["x-api-key"] == FAKE_KEY
    assert seen["headers"]["anthropic-version"] == check_key.API_VERSION
    assert seen["body"]["model"] == "claude-sonnet-5"
    assert seen["body"]["max_tokens"] <= 64


def test_environment_variable_is_the_fallback(tmp_path):
    def opener(request, timeout):
        return FakeResponse({"content": [{"type": "text", "text": "Hello"}]})

    code = check_key.main(["--env", str(tmp_path / "none.env")], opener=opener, environ={"ANTHROPIC_API_KEY": FAKE_KEY})
    assert code == 0


@pytest.mark.parametrize("status,hint", [(401, "ask LaNice"), (404, "model id"), (429, "Rate limited")])
def test_http_errors_exit_2_with_a_hint_and_never_print_the_key(tmp_path, capsys, status, hint):
    def opener(request, timeout):
        body = json.dumps({"error": {"type": "api_error", "message": f"problem with {FAKE_KEY}"}}).encode("utf-8")
        raise urllib.error.HTTPError(request.full_url, status, "error", {}, io.BytesIO(body))

    code = check_key.main(["--env", env_file(tmp_path, f"ANTHROPIC_API_KEY={FAKE_KEY}\n")], opener=opener, environ={})
    out = capsys.readouterr()
    assert code == 2
    assert f"HTTP {status}" in out.out and hint in out.out
    assert FAKE_KEY not in out.out + out.err


def test_no_connection_exits_3(tmp_path, capsys):
    def opener(request, timeout):
        raise urllib.error.URLError(f"cannot reach host (key {FAKE_KEY})")

    code = check_key.main(["--env", env_file(tmp_path, f"ANTHROPIC_API_KEY={FAKE_KEY}\n")], opener=opener, environ={})
    out = capsys.readouterr()
    assert code == 3
    assert FAKE_KEY not in out.out + out.err


@pytest.mark.parametrize("payload", [
    {}, [], None, {"content": None}, {"content": "not a list"},
    {"content": []}, {"content": [None]},
    {"content": [{"type": "text"}]},
    {"content": [{"type": "text", "text": 123}]},
    {"content": [{"type": "text", "text": "  "}]},
    {"content": [{"type": "thinking", "thinking": "not the reply"}]},
    {"error": {"message": FAKE_KEY}, "content": [{"type": "text", "text": "Hello"}]},
])
def test_unexpected_payload_exits_4_without_false_success(tmp_path, capsys, payload):
    code = check_key.main(
        ["--env", str(tmp_path / "missing.env")],
        opener=lambda *a, **k: FakeResponse(payload),
        environ={"ANTHROPIC_API_KEY": FAKE_KEY},
    )
    output = capsys.readouterr()
    assert code == 4
    assert "Invalid API response" in output.out
    assert "OK:" not in output.out
    assert FAKE_KEY not in output.out + output.err


@pytest.mark.parametrize("raw", [b"not json", b"\xff", b"{truncated"])
def test_invalid_json_or_encoding_exits_4(tmp_path, capsys, raw):
    class RawResponse(FakeResponse):
        def read(self, size=-1):
            return raw

    code = check_key.main(
        ["--env", str(tmp_path / "missing.env")],
        opener=lambda *a, **k: RawResponse(None),
        environ={"ANTHROPIC_API_KEY": FAKE_KEY},
    )
    output = capsys.readouterr()
    assert code == 4
    assert "Invalid API response" in output.out
    assert "OK:" not in output.out
    assert FAKE_KEY not in output.out + output.err


def test_unexpected_http_status_is_not_success(tmp_path, capsys):
    response = FakeResponse({"content": [{"type": "text", "text": "Hello"}]})
    response.status = 503
    assert check_key.main(
        ["--env", str(tmp_path / "missing.env")],
        opener=lambda *a, **k: response,
        environ={"ANTHROPIC_API_KEY": FAKE_KEY},
    ) == 4
    assert "OK:" not in capsys.readouterr().out
