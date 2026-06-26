# rth — project notes

Red-team harness: configurable agentic LLM terminal with Parseltongue + L1B3RT4S.

## Architecture
- `providers/` normalize OpenAI and Anthropic wire formats to one event stream
  (`agent/messages.py`); `agent/loop.py` is protocol-agnostic.
- Tools register into `tools/registry.py`; specs are emitted per-protocol by the
  providers. Add a tool by writing `register(registry)` in a `tools/` module and listing
  it in `tools/__init__.py`.
- Transforms are pure functions in `transforms/`, indexed in `transforms/__init__.py`
  with `lossy` flags.

## Lessons Learned
- **[cli]**: An optional top-level positional (the one-shot prompt) collides with
  argparse subparsers — the positional swallows the subcommand token. Route subcommands
  manually by scanning argv for the first non-flag token before parsing.
- **[transforms]**: morse, nato, leet, and bijection are lossy (they fold case and/or
  spacing). Mark them `lossy=True` and test them with normalized comparison, not exact
  round-trip.
- **[textual]**: `Static` has no public `.renderable`; don't introspect widget internals
  in tests. Assert on app/agent state (history, busy flag) via `App.run_test()` pilot.
- **[providers]**: OpenAI represents tool results as separate `{role:"tool"}` messages;
  Anthropic nests `tool_result` blocks inside a user message. Keep both in
  `_messages_to_wire`.
