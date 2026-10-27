"""The real-provider adapter is tested with a local LiteLLM stand-in; tests make no API calls."""

import json
from types import SimpleNamespace

import pytest

from harness.litellm_provider import LiteLLMProvider
from harness.provider import ProviderError
from harness.roles import run_role


def _completion(message, seen):
    def call(**request):
        seen.append(request)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])
    return call


def test_provider_sends_only_the_role_tools_and_normalizes_tool_calls():
    seen = []
    provider = LiteLLMProvider(api_key="secret-test-key", completion=_completion(
        SimpleNamespace(content="", tool_calls=[SimpleNamespace(
            id="call-1", function=SimpleNamespace(name="read_research", arguments='{"key":"source-a"}'))]), seen))

    result = provider.complete("role rules", [dict(role="user", content="read source-a")], ["read_research"])

    assert result == {"text": "", "tool_calls": [
        {"id": "call-1", "name": "read_research", "arguments": {"key": "source-a"}}
    ]}
    assert seen[0]["model"] == "anthropic/claude-sonnet-5-5"
    assert seen[0]["api_key"] == "secret-test-key"
    assert [tool["function"]["name"] for tool in seen[0]["tools"]] == ["read_research"]
    assert seen[0]["tools"][0]["function"]["parameters"]["required"] == ["key"]
    assert "secret-test-key" not in repr(provider)
    assert seen[0]["num_retries"] == 0


def test_provider_preserves_tool_call_history_for_the_next_model_step():
    seen = []
    provider = LiteLLMProvider(api_key="test-key", completion=_completion(
        {"content": "done", "tool_calls": []}, seen))
    prior = [
        {"role": "user", "content": "read"},
        {"role": "assistant", "content": "", "tool_calls": [
            {"id": "call-1", "name": "read_research", "arguments": {"key": "source-a"}}
        ]},
        {"role": "tool", "name": "read_research", "tool_call_id": "call-1", "content": "source text"},
    ]

    provider.complete("rules", prior, ["read_research"])

    assert seen[0]["messages"][2]["tool_calls"] == [{
        "id": "call-1", "type": "function",
        "function": {"name": "read_research", "arguments": json.dumps({"key": "source-a"})},
    }]
    assert seen[0]["messages"][3]["tool_call_id"] == "call-1"


def test_role_runner_keeps_tool_calls_and_results_in_the_provider_conversation():
    seen = []
    replies = [
        SimpleNamespace(content="", tool_calls=[SimpleNamespace(
            id="call-1", function=SimpleNamespace(name="check_artifacts", arguments="{}"))]),
        SimpleNamespace(content="The check passed.", tool_calls=[]),
    ]

    def completion(**request):
        seen.append(request)
        return SimpleNamespace(choices=[SimpleNamespace(message=replies[len(seen) - 1])])

    provider = LiteLLMProvider(api_key="test-key", completion=completion)
    result = run_role("evaluator", provider, "check this run", {"check_artifacts": lambda: {"status": "pass"}})

    assert result["text"] == "The check passed."
    assert result["tool_results"] == {"check_artifacts": {"status": "pass"}}
    assert seen[1]["messages"][2]["tool_calls"][0]["id"] == "call-1"
    assert seen[1]["messages"][3]["tool_call_id"] == "call-1"


def test_invalid_tool_arguments_fail_without_including_provider_response_text():
    provider = LiteLLMProvider(api_key="test-key", completion=_completion(
        SimpleNamespace(content="sk-ant-secret-value", tool_calls=[SimpleNamespace(
            id="call-1", function=SimpleNamespace(name="read_research", arguments="not-json"))]), []))

    with pytest.raises(ProviderError, match=r"Claude request failed \(JSONDecodeError\)") as error:
        provider.complete("rules", [], ["read_research"])
    assert "sk-ant-secret-value" not in str(error.value)


def test_environment_factory_reads_key_silently_and_accepts_model_override(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "ANTHROPIC_API_KEY=secret-test-key\nCLAUDE_MODEL=anthropic/claude-sonnet-5-override\n",
        encoding="utf-8",
    )
    provider = LiteLLMProvider.from_environment(
        env_file=env_file, environ={"CLAUDE_MODEL": "anthropic/claude-sonnet-5"})
    assert provider.model == "anthropic/claude-sonnet-5-override"
    assert "secret-test-key" not in repr(provider)


def test_environment_factory_fails_clearly_when_key_is_missing(tmp_path):
    with pytest.raises(ProviderError, match="no Claude API key found"):
        LiteLLMProvider.from_environment(env_file=tmp_path / "missing.env", environ={})


def test_provider_refuses_non_claude_model_names():
    with pytest.raises(ProviderError, match="CLAUDE_MODEL"):
        LiteLLMProvider(api_key="test-key", model="openai/example")


def _reply_ending(reason):
    message = SimpleNamespace(content="sk-ant-partial-text", tool_calls=None)
    return lambda **request: SimpleNamespace(choices=[SimpleNamespace(finish_reason=reason, message=message)])


def test_a_reply_cut_off_at_the_token_limit_fails_loudly_without_its_text():
    provider = LiteLLMProvider(api_key="test-key", completion=_reply_ending("length"))

    with pytest.raises(ProviderError, match=r"cut off at the 1200-token limit") as error:
        provider.complete("rules", [], [])
    assert "sk-ant-partial-text" not in str(error.value)


@pytest.mark.parametrize("reason", ["stop", "tool_calls", None])
def test_a_reply_that_ended_normally_is_accepted(reason):
    provider = LiteLLMProvider(api_key="test-key", completion=_reply_ending(reason))

    assert provider.complete("rules", [], [])["text"] == "sk-ant-partial-text"
