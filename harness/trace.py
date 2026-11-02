"""The trace:  one receipt per run, one JSON line per step (see docs/trace-plan.md).

A trace never holds a key.  Text that looks like a key is replaced, and text that is cut is
noted in `removed_text`, so a reader can see what the harness removed.

A tool-result line also says how many characters the tool returned (`sent_chars`) and how many
the model received (`received_chars`), so a cut made before the model saw the text shows in the
line itself:  sent is not the same as received.
"""

import json
import re
from pathlib import Path

KEY_LIKE = re.compile(r"sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9_]{16,}|github_pat_[A-Za-z0-9_]{16,}")
BEARER = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+")
ASSIGNED_SECRET = re.compile(
    r"(?i)(\b(?:api[_-]?key|access[_-]?token|password|client[_-]?secret)\b\s*[:=]\s*)"
    r"[\"']?[^\s,;\"'}]+")
SECRET_FIELDS = {"api_key", "apikey", "authorization", "access_token", "token", "password", "secret", "client_secret"}
MAX_TEXT = 400


def sanitize(value, path=""):
    """Redact structured secret fields and recognizable credentials without cutting context."""
    notes = []
    if isinstance(value, dict):
        clean = {}
        for key, item in value.items():
            safe_key, found = sanitize(str(key), path)
            notes += found
            location = f"{path}.{safe_key}" if path else safe_key
            if str(key).lower().replace("-", "_") in SECRET_FIELDS:
                clean[safe_key] = "[redacted secret field]"
                notes.append(f"{location}: redacted secret field")
            else:
                clean[safe_key], found = sanitize(item, location)
                notes += found
        return clean, notes
    if isinstance(value, (list, tuple)):
        clean = []
        for index, item in enumerate(value):
            safe, found = sanitize(item, f"{path}[{index}]")
            clean.append(safe)
            notes += found
        return clean, notes
    if isinstance(value, str):
        value, found = KEY_LIKE.subn("[redacted key-like text]", value)
        if found:
            notes.append(f"{path}: redacted {found} key-like string(s)")
        value, found = BEARER.subn("Bearer [redacted]", value)
        if found:
            notes.append(f"{path}: redacted {found} bearer credential(s)")
        value, found = ASSIGNED_SECRET.subn(r"\1[redacted]", value)
        if found:
            notes.append(f"{path}: redacted {found} assigned secret(s)")
    return value, notes


def scrub(value, limit=MAX_TEXT):
    """Return (text, notes):  key-like strings redacted, long text cut, nothing removed silently."""
    value, notes = sanitize(value)
    text = value if isinstance(value, str) else json.dumps(value, sort_keys=True, default=str)
    if len(text) > limit:
        notes.append(f"cut {len(text) - limit} characters")
        text = text[:limit]
    return text, notes


class Trace:
    """Append-only; refuses an existing file; writes each line as it happens."""

    def __init__(self, path):
        self.path = Path(path)
        if self.path.exists():
            raise FileExistsError(f"trace already exists: {self.path}")
        self.step = 0
        self.input_hashes = None
        self.case_id = self.path.parent.name
        self.run_id = None
        self.revision_round = None
        self.calls = 0
        self.created = False

    def new_call_id(self, role):
        self.calls += 1
        return f"{role}-{self.calls}"

    def add(self, role, message, *, tool=None, tool_args=None, tool_result=None, validator=None,
            evaluator_status=None, revision_round=None, prompt_version=None,
            sent_chars=None, received_chars=None, event=None, context=None,
            role_call_id=None, tool_call_id=None, model_removed_text=None):
        removed = []
        fields = {}
        for name, value in (("message", message), ("tool_args", tool_args),
                            ("tool_result_summary", tool_result), ("validator_verdict", validator)):
            if value is None:
                fields[name] = None
            else:
                fields[name], notes = scrub(value)
                removed += [f"{name}: {note}" for note in notes]
        line = dict(step=self.step + 1, role=role, prompt_version=prompt_version,
                    input_hashes=self.input_hashes, tool=tool, evaluator_status=evaluator_status,
                    revision_round=self.revision_round if revision_round is None else revision_round,
                    case_id=self.case_id, run_id=self.run_id, event=event, context=context,
                    role_call_id=role_call_id, tool_call_id=tool_call_id,
                    model_removed_text=model_removed_text,
                    sent_chars=sent_chars, received_chars=received_chars,
                    removed_text=removed, **fields)
        line, notes = sanitize(line)
        line["removed_text"] += notes
        # Exclusively claim the file on the first write, including when two Trace objects race.
        with self.path.open("a" if self.created else "x", encoding="utf-8") as handle:
            handle.write(json.dumps(line, allow_nan=False) + "\n")
        self.created = True
        self.step += 1
        return line
