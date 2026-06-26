from __future__ import annotations

from .. import harmbench
from .registry import ToolContext, ToolRegistry


async def _harmbench(args: dict, ctx: ToolContext) -> str:
    action = str(args.get("action", "sample")).lower()
    err = await harmbench.ensure()
    if err:
        return f"Error: {err}"
    if action == "categories":
        cats = harmbench.categories()
        return "HarmBench semantic categories:\n" + "\n".join(f"  {c}" for c in cats)
    category = args.get("category")
    n = int(args.get("n", 8))
    seed = int(args.get("seed", 0))
    rows = harmbench.sample(category, n, seed)
    if not rows:
        return (
            f"No HarmBench behaviors for category '{category}'. "
            f"Categories: {', '.join(harmbench.categories())}"
        )
    head = f"{len(rows)} HarmBench behaviors" + (f" ({category})" if category else " (balanced)")
    return head + ":\n" + "\n".join(f"  - {r['behavior']}" for r in rows)


def register(registry: ToolRegistry) -> None:
    registry.add(
        name="harmbench",
        description=(
            "Pull standardized harmful-behavior prompts from the HarmBench benchmark "
            "(400 behaviors across cybercrime_intrusion, chemical_biological, illegal, "
            "misinformation_disinformation, harmful, harassment_bullying, copyright). Use "
            "these as your test battery instead of self-written examples to avoid selection "
            "bias and get comparable results. action='categories' lists them; action='sample' "
            "returns n behaviors (optionally filtered by category)."
        ),
        parameters={
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["sample", "categories"]},
                "category": {"type": "string", "description": "Semantic category filter"},
                "n": {"type": "integer", "description": "How many behaviors (default 8)"},
                "seed": {"type": "integer", "description": "Sampling seed (default 0)"},
            },
        },
        handler=_harmbench,
    )
