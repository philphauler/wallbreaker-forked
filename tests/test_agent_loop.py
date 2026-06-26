from rtharness.agent.loop import AgentEvents, run_turn
from rtharness.agent.messages import (
    StopEvent,
    TextDelta,
    ToolResultBlock,
    ToolUseEvent,
    user,
)
from rtharness.config import Config
from rtharness.tools import files, shell
from rtharness.tools.registry import ToolContext, ToolRegistry


class ScriptedProvider:
    def __init__(self, script):
        self.script = script
        self.calls = 0

    async def stream(self, messages, tools=None, system=None, max_tokens=4096, temperature=None):
        events = self.script[min(self.calls, len(self.script) - 1)]
        self.calls += 1
        for ev in events:
            yield ev


def _registry():
    ctx = ToolContext(config=Config(default_profile="x", profiles={}))
    reg = ToolRegistry(ctx)
    shell.register(reg)
    files.register(reg)
    return reg


async def test_loop_executes_tool_and_finishes():
    provider = ScriptedProvider(
        [
            [
                TextDelta("running"),
                ToolUseEvent("c1", "run_shell", {"command": "echo hi"}),
                StopEvent("tool_use"),
            ],
            [TextDelta("done"), StopEvent("end_turn")],
        ]
    )
    seen = []
    events = AgentEvents(
        on_tool_result=lambda i, n, c, e: seen.append((n, c.strip(), e))
    )
    history = [user("go")]
    result = await run_turn(provider, _registry(), history, events=events)

    assert result.text() == "done"
    assert provider.calls == 2
    assert seen and seen[0][0] == "run_shell" and "hi" in seen[0][1]
    tool_results = [
        b for m in history for b in m.content if isinstance(b, ToolResultBlock)
    ]
    assert len(tool_results) == 1


async def test_loop_stops_without_tools():
    provider = ScriptedProvider([[TextDelta("just text"), StopEvent("end_turn")]])
    history = [user("hi")]
    result = await run_turn(provider, _registry(), history)
    assert result.text() == "just text"
    assert provider.calls == 1


async def test_unknown_tool_reported_as_error():
    provider = ScriptedProvider(
        [
            [ToolUseEvent("c1", "nope", {}), StopEvent("tool_use")],
            [TextDelta("ok"), StopEvent("end_turn")],
        ]
    )
    errors = []
    events = AgentEvents(on_tool_result=lambda i, n, c, e: errors.append(e))
    await run_turn(provider, _registry(), [user("x")], events=events)
    assert errors and errors[0] is True
