"""One-call key test:  does the Anthropic key in .env work?

Run it from the repository root, after copying `.env.example` to `.env` and pasting your key:

    python3 scripts/check_key.py

It sends one tiny request to the Claude API and prints a short result.  It never prints the key.
Exit code:  0 = the key works; 1 = no key found; 2 = the API rejected the call; 3 = no connection, or the
connection broke mid-reply; 4 = invalid API response; 5 = the key or the .env file cannot be used (the file
is not UTF-8 text, or the key has a space or a character that is not plain ASCII); 6 = unexpected failure.
Success confirms a direct Anthropic response (api.anthropic.com), not the complete LiteLLM integration.

The key comes from the `.env` file first, then from the ANTHROPIC_API_KEY environment variable.  If the file
names the key more than once, the last one is used and a note says so.

The script uses only the Python standard library, so it needs no installed packages.
"""

import argparse
import http.client
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

API_URL = "https://api.anthropic.com/v1/messages"
API_VERSION = "2023-06-01"
KEY_NAME = "ANTHROPIC_API_KEY"
# The plain API model id.  LiteLLM writes the same model as "anthropic/claude-sonnet-5-5".
MODEL = "claude-sonnet-5-5"
DEFAULT_ENV = Path(__file__).resolve().parent.parent / ".env"
MAX_BODY = 1_000_000  # bytes; a reply to a 32-token request is far smaller
MAX_DETAIL = 300  # characters of the API's own error message to show

HINTS = {
    401: "The key was rejected.  Check .env for extra spaces or quotes.  If it still fails, ask LaNice for a new one-time link.",
    403: "The key is not allowed to use this model.  Ask LaNice.",
    404: f"The model id was not found.  Use {MODEL} here (anthropic/{MODEL} in LiteLLM).",
    429: "Rate limited.  Wait a minute and run it again.",
}


class EnvFileError(Exception):
    """The .env file exists but is not UTF-8 text."""


def _clean_value(value):
    """A KEY=value right-hand side without quotes or a trailing comment."""
    value = value.strip()
    if value[:1] in ("'", '"'):
        close = value.find(value[0], 1)
        if close != -1:
            return value[1:close]
        return value[1:]
    return re.split(r"\s+#", value, maxsplit=1)[0].strip()


def read_env_values(path, name=KEY_NAME):
    """Every nonempty value of `name` in a simple KEY=value file, in file order.

    A missing or unreadable file gives an empty list.  A file that is not UTF-8 text raises EnvFileError.
    A UTF-8 byte-order mark (some Windows editors add one) is ignored.
    """
    try:
        lines = Path(path).read_text(encoding="utf-8-sig").splitlines()
    except UnicodeDecodeError:
        raise EnvFileError(str(path)) from None
    except OSError:
        return []
    values = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export "):].lstrip()
        key, _, value = line.partition("=")
        if key.strip() == name:
            value = _clean_value(value)
            if value:
                values.append(value)
    return values


def read_env_key(path, name=KEY_NAME):
    """Return the last value of `name` in a simple KEY=value file, or None."""
    values = read_env_values(path, name)
    return values[-1] if values else None


def key_problem(key):
    """Why a key cannot be sent as an HTTP header, or None.  Never repeats the key."""
    if any(ch.isspace() for ch in key):
        return "contains a space or a line break"
    if not all(33 <= ord(ch) <= 126 for ch in key):
        return "contains a character that is not plain ASCII (for example a curly quote)"
    return None


def build_request(key, model=MODEL):
    body = {"model": model, "max_tokens": 32,
            "messages": [{"role": "user", "content": "Say hello in five words."}]}
    return urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={"x-api-key": key, "anthropic-version": API_VERSION, "content-type": "application/json"},
    )


def redact(text, key):
    return text.replace(key, "[key]") if key else text


def error_detail(error, key):
    """The API's own error message, with the key removed in case it is echoed."""
    try:
        detail = json.loads(error.read(MAX_BODY).decode("utf-8")).get("error", {})
        return redact(f"{detail.get('type', 'error')}: {detail.get('message', '')}".strip(), key)[:MAX_DETAIL]
    except (ValueError, OSError, AttributeError):
        return ""


def _run(argv=None, opener=urllib.request.urlopen, environ=None):
    parser = argparse.ArgumentParser(description="Test the Anthropic key in .env with one tiny call.")
    parser.add_argument("--env", default=str(DEFAULT_ENV), help="path to the .env file (default: the repository .env)")
    parser.add_argument("--model", default=MODEL, help=f"model id (default: {MODEL})")
    args = parser.parse_args(argv)
    environ = os.environ if environ is None else environ

    try:
        values = read_env_values(args.env)
    except EnvFileError:
        print("The .env file is not UTF-8 text.  Save it again as UTF-8, then paste the key once more.")
        return 5
    if len(values) > 1:
        print(f"Note:  {KEY_NAME} appears {len(values)} times in the .env file.  The last one is used.")
    key = values[-1] if values else environ.get(KEY_NAME)
    if not key:
        print(f"No {KEY_NAME} found.  Copy .env.example to .env and paste your key after {KEY_NAME}=.")
        return 1
    problem = key_problem(key)
    if problem:
        print(f"The key {problem}.  Copy it again from LaNice's link, with no spaces or quotes around it.")
        return 5

    try:
        with opener(build_request(key, args.model), timeout=30) as response:
            raw = response.read(MAX_BODY + 1)
            status = response.status
        if len(raw) > MAX_BODY:
            print("Invalid API response: the reply is larger than expected.")
            return 4
        payload = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeError):
        print("Invalid API response: expected a UTF-8 JSON message with a nonempty text reply.")
        return 4
    except urllib.error.HTTPError as error:
        print(f"Rejected:  HTTP {error.code}.  {HINTS.get(error.code, '')}".rstrip())
        detail = error_detail(error, key)
        if detail:
            print(detail)
        return 2
    except (urllib.error.URLError, OSError) as error:
        print(f"Could not reach the API:  {redact(str(error), key)}")
        return 3
    except http.client.HTTPException as error:
        print(f"The connection broke before the full reply arrived:  {redact(type(error).__name__, key)}.")
        return 3

    if (
        not isinstance(status, int) or not 200 <= status < 300
        or not isinstance(payload, dict)
        or "error" in payload
        or not isinstance(payload.get("content"), list)
    ):
        print("Invalid API response: expected a successful message with a text reply.")
        return 4

    replies = []
    for block in payload["content"]:
        if not isinstance(block, dict) or not isinstance(block.get("type"), str):
            print("Invalid API response: malformed content block.")
            return 4
        if block["type"] == "text":
            if not isinstance(block.get("text"), str):
                print("Invalid API response: malformed text reply.")
                return 4
            if block["text"].strip():
                replies.append(block["text"].strip())
    if not replies:
        print("Invalid API response: no nonempty text reply received.")
        return 4
    print(f"OK:  HTTP {status} from {args.model}.  Reply:  {redact(' '.join(replies), key)}")
    return 0


def main(argv=None, opener=urllib.request.urlopen, environ=None):
    """Run the check.  Any failure that is not covered above exits 6, never 1 (1 means "no key found")."""
    try:
        return _run(argv, opener=opener, environ=environ)
    except Exception as error:  # noqa: BLE001 - last line of defence; the message never includes the error text
        print(f"Unexpected failure:  {type(error).__name__}.  Nothing that could hold the key was printed.")
        return 6


if __name__ == "__main__":
    sys.exit(main())
