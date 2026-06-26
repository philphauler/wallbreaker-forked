from rtharness.agent.messages import (
    Message,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    user,
)
from rtharness.config import Endpoint
from rtharness.providers.anthropic_provider import _messages_to_wire as ant_msgs
from rtharness.providers.anthropic_provider import _tools_to_wire as ant_tools
from rtharness.providers.factory import build_provider
from rtharness.providers.openai_provider import _messages_to_wire as oai_msgs
from rtharness.providers.openai_provider import _tools_to_wire as oai_tools

CONVO = [
    user("hello"),
    Message(
        role="assistant",
        content=[TextBlock("checking"), ToolUseBlock("c1", "run_shell", {"command": "ls"})],
    ),
    Message(role="user", content=[ToolResultBlock("c1", "out")]),
]

TOOLS = [{"name": "run_shell", "description": "run", "parameters": {"type": "object"}}]


def test_factory_picks_protocol():
    oai = build_provider(Endpoint("a", "openai", "http://x", "m"))
    ant = build_provider(Endpoint("b", "anthropic", "http://y", "m"))
    assert type(oai).__name__ == "OpenAIProvider"
    assert type(ant).__name__ == "AnthropicProvider"


def test_openai_message_conversion():
    wire = oai_msgs(CONVO, "sys")
    assert wire[0] == {"role": "system", "content": "sys"}
    assistant = next(m for m in wire if m["role"] == "assistant")
    assert assistant["tool_calls"][0]["function"]["name"] == "run_shell"
    tool_msg = next(m for m in wire if m["role"] == "tool")
    assert tool_msg["tool_call_id"] == "c1"


def test_anthropic_message_conversion():
    wire = ant_msgs(CONVO)
    assistant = next(m for m in wire if m["role"] == "assistant")
    blocks = {b["type"] for b in assistant["content"]}
    assert "tool_use" in blocks
    last = wire[-1]
    assert last["content"][0]["type"] == "tool_result"
    assert last["content"][0]["tool_use_id"] == "c1"


def test_tool_schema_shapes():
    assert oai_tools(TOOLS)[0]["type"] == "function"
    assert ant_tools(TOOLS)[0]["input_schema"] == {"type": "object"}
