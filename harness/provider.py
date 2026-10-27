"""The model interface of the harness, and a scripted fake for tests.

A provider takes a system prompt, the messages so far, and the names of the tools that the role
may call, and returns text and tool calls. `harness.litellm_provider` supplies the Claude adapter.
Tests use `FakeProvider`, so no key and no network are needed.
"""

from dataclasses import dataclass, field


class ProviderError(Exception):
    """The provider could not return a reply."""


@dataclass
class FakeProvider:
    """Returns scripted replies in order.  Each reply is `dict(text=..., tool_calls=[dict(name, arguments)])`."""
    replies: list
    calls: list = field(default_factory=list)

    def complete(self, system, messages, tools):
        self.calls.append(dict(system=system, messages=[dict(m) for m in messages], tools=list(tools)))
        if len(self.calls) > len(self.replies):
            raise ProviderError("the fake provider has no more scripted replies")
        reply = self.replies[len(self.calls) - 1]
        return dict(text=reply.get("text", ""), tool_calls=list(reply.get("tool_calls", [])))
