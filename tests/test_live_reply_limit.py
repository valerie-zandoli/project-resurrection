"""The live reply limit leaves room for the model's reasoning (found by the shake-down of 2026-10-29).  No key or network."""

from types import SimpleNamespace

from harness.litellm_provider import MAX_TOKENS, LiteLLMProvider


def test_the_request_asks_for_the_reply_limit():
    sent = {}

    def completion(**request):
        sent.update(request)
        message = SimpleNamespace(content="done", tool_calls=None)
        return SimpleNamespace(choices=[SimpleNamespace(finish_reason="stop", message=message)])

    LiteLLMProvider(api_key="test-key", completion=completion).complete("rules", [], [])
    assert sent["max_tokens"] == MAX_TOKENS


def test_the_reply_limit_leaves_room_for_reasoning():
    # Reasoning tokens count against the limit.  The largest live reply used 1,003 tokens (493 reasoning, 510 visible), and a
    # limit of 1,200 failed three live runs of three.  Lower this number only with a measured reason in the commit.
    assert MAX_TOKENS >= 4000
