"""Send one short live Claude request through the harness's LiteLLM adapter.

Run from the repository root after putting your own API key in ignored `.env`:

    python scripts/check_litellm_provider.py

This prints only a short reply and never prints the key.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harness.litellm_provider import LiteLLMProvider
from harness.provider import ProviderError


def main():
    try:
        provider = LiteLLMProvider.from_environment()
        reply = provider.complete(
            "You are checking the Project Resurrection Claude connection. Reply with a brief greeting.",
            [dict(role="user", content="Say hello in a few words.")],
            [],
        )
    except ProviderError as exc:
        print(f"Claude connection check failed: {exc}")
        return 1
    text = " ".join(reply["text"].split())[:240]
    if not text:
        print("Claude connection returned no text.")
        return 2
    print(f"Claude connection works: {text}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
