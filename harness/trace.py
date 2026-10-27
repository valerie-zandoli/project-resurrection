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

KEY_LIKE = re.compile(r"sk-[A-Za-z0-9_-]{16,}")
MAX_TEXT = 400


def scrub(value, limit=MAX_TEXT):
    """Return (text, notes):  key-like strings redacted, long text cut, nothing removed silently."""
    text = value if isinstance(value, str) else json.dumps(value, sort_keys=True, default=str)
    notes = []
    text, found = KEY_LIKE.subn("[redacted key-like text]", text)
    if found:
        notes.append(f"redacted {found} key-like string(s)")
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

    def add(self, role, message, *, tool=None, tool_args=None, tool_result=None, validator=None,
            evaluator_status=None, revision_round=None, prompt_version=None,
            sent_chars=None, received_chars=None):
        self.step += 1
        removed = []
        fields = {}
        for name, value in (("message", message), ("tool_args", tool_args),
                            ("tool_result_summary", tool_result), ("validator_verdict", validator)):
            if value is None:
                fields[name] = None
            else:
                fields[name], notes = scrub(value)
                removed += [f"{name}: {note}" for note in notes]
        line = dict(step=self.step, role=role, prompt_version=prompt_version,
                    input_hashes=self.input_hashes, tool=tool, evaluator_status=evaluator_status,
                    revision_round=revision_round, sent_chars=sent_chars, received_chars=received_chars,
                    removed_text=removed, **fields)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(line, allow_nan=False) + "\n")
        return line
