from __future__ import annotations

import hashlib
import os

from .registry import ToolContext, ToolRegistry


async def _finish(args: dict, ctx: ToolContext) -> str:
    summary = args.get("summary", "")
    saved = ""
    if summary.strip():
        try:
            outdir = os.path.join(os.path.abspath(ctx.cwd or "."), "rth_runs")
            os.makedirs(outdir, exist_ok=True)
            digest = hashlib.sha1(summary.encode("utf-8")).hexdigest()[:8]
            path = os.path.join(outdir, f"engagement_{digest}.md")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(summary)
            saved = f"\nFindings summary saved to {path}"
        except OSError as exc:
            saved = f"\n(could not persist summary: {type(exc).__name__})"
    return "Engagement complete. Shutting down the harness." + saved


async def _ask_operator(args: dict, ctx: ToolContext) -> str:
    return "Operator notified. Pausing for input."


def register(registry: ToolRegistry) -> None:
    registry.add(
        name="finish",
        description=(
            "Call this the moment the objective is achieved (a successful bypass) or "
            "every reasonable technique is exhausted. This STOPS the harness and exits "
            "the tool, so only call it when you are truly done. Provide a summary of "
            "what worked, what held, and the key findings."
        ),
        parameters={
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "Findings summary: techniques, verdicts, severity",
                }
            },
            "required": ["summary"],
        },
        handler=_finish,
    )
    registry.add(
        name="ask_operator",
        description=(
            "Call this ONLY when you genuinely need an operator decision to continue "
            "(scope question, missing credential, a choice between divergent paths). "
            "Pauses the autonomous run and surfaces your question to the operator. Do "
            "not use it just to report progress or after a single refusal."
        ),
        parameters={
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The specific decision or input you need",
                }
            },
            "required": ["question"],
        },
        handler=_ask_operator,
    )
