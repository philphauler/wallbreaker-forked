from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from . import bridge

mcp = FastMCP("p4rs3lt0ngv3", log_level="WARNING")


def _fmt_transform_row(t: dict[str, Any]) -> str:
    flag = "decode+encode" if t.get("canDecode") else "encode-only "
    return f"  {t['key']:26} {t['category']:12} {flag}  {t['name']}"


def _err(exc: Exception) -> str:
    return f"[parsel error] {exc}"


@mcp.tool()
def parsel_list(category: str = "") -> str:
    """List the P4RS3LT0NGV3 transform catalog (222 transforms in 11 categories).

    This is the discovery entry point: call it first to see what is available, then use
    parsel_inspect for one transform's options, and parsel_transform / parsel_chain to apply.
    Pass an empty category for the full catalog, or one of: case, cipher, concealment,
    encoding, format, signwriting, special, symbol, technical, unicode, visual.
    Each row shows the transform KEY (use that with the other tools), its category, whether
    it can decode as well as encode, and its display name.
    """
    try:
        transforms = bridge.list_transforms()
    except Exception as exc:  # noqa: BLE001
        return _err(exc)
    cat = category.strip().lower()
    if cat:
        transforms = [t for t in transforms if t["category"].lower() == cat]
        if not transforms:
            return (
                f"No transforms in category '{category}'. Categories: "
                + ", ".join(bridge.categories())
            )
    header = (
        f"{len(transforms)} transforms"
        + (f" in '{cat}'" if cat else " (categories: " + ", ".join(
            f"{k}={v}" for k, v in bridge.categories().items()) + ")")
        + ":"
    )
    return header + "\n" + "\n".join(_fmt_transform_row(t) for t in transforms)


@mcp.tool()
def parsel_search(query: str) -> str:
    """Search the transform catalog by keyword (matches key, name, and category).

    Use when you want an obfuscation of a certain flavor but don't know the exact key,
    e.g. 'zero width', 'rune', 'emoji', 'base', 'morse', 'reverse'. Returns ranked matches;
    take the KEY from a row and pass it to parsel_transform / parsel_inspect.
    """
    try:
        hits = bridge.search(query)
    except Exception as exc:  # noqa: BLE001
        return _err(exc)
    if not hits:
        return f"No transforms matched '{query}'. Try parsel_list to browse all 222."
    return f"{len(hits)} match(es) for '{query}':\n" + "\n".join(
        _fmt_transform_row(t) for t in hits
    )


@mcp.tool()
def parsel_inspect(transform: str) -> str:
    """Inspect one transform: its category, whether it decodes, and its configurable options.

    `transform` is a key (e.g. 'caesar') or a loose name (e.g. 'Pig Latin', 'rot 13') — it is
    fuzzily resolved. Read the options here, then pass them as `options` to parsel_transform.
    Example: parsel_inspect('caesar') shows option 'shift' (number, default 3, 1-25).
    """
    try:
        key = bridge.resolve_key(transform)
        if not key:
            return f"Unknown transform '{transform}'. Use parsel_search or parsel_list."
        meta = bridge.inspect(key)
    except Exception as exc:  # noqa: BLE001
        return _err(exc)
    lines = [
        f"{meta['key']}  ({meta['name']})",
        f"  category : {meta['category']}",
        f"  decodes  : {'yes' if meta.get('canDecode') else 'no (encode-only)'}",
    ]
    opts = meta.get("configurableOptions") or []
    if not opts:
        lines.append("  options  : none")
    else:
        lines.append("  options  :")
        for o in opts:
            bits = [f"type={o.get('type')}", f"default={o.get('default')!r}"]
            if o.get("min") is not None or o.get("max") is not None:
                bits.append(f"range={o.get('min')}..{o.get('max')}")
            if o.get("options"):
                choices = ", ".join(
                    str(c.get("value", c)) for c in o["options"] if isinstance(c, dict)
                ) or str(o["options"])
                bits.append(f"choices=[{choices}]")
            lines.append(f"    - {o['id']}: {o.get('label','')}  ({', '.join(bits)})")
    defaults = meta.get("defaultOptions")
    if defaults:
        lines.append(f"  defaults : {json.dumps(defaults, ensure_ascii=False)}")
    return "\n".join(lines)


@mcp.tool()
def parsel_transform(
    transform: str,
    text: str,
    action: str = "encode",
    options: dict[str, Any] | None = None,
) -> str:
    """Apply ONE transform to text. The core encoder/cipher/obfuscator tool.

    - transform: key or loose name (fuzzily resolved), e.g. 'base64', 'caesar', 'zalgo',
      'emoji_encoding', 'zerowidth_steganography', 'elder_futhark', 'morse_code'.
    - text: the input string.
    - action: 'encode' (default), 'decode' (reverse it; only for decodable transforms),
      or 'preview' (a short sample).
    - options: transform-specific settings from parsel_inspect, e.g. {"shift": 5} for caesar.
      Omit for defaults.
    Returns the transformed text. Example: parsel_transform('caesar','Attack at dawn',
    options={'shift':5}) -> 'Fyyfhp fy ifbs'.
    """
    try:
        key = bridge.resolve_key(transform)
        if not key:
            return f"Unknown transform '{transform}'. Use parsel_search or parsel_list."
        result = bridge.run_transform(action.strip().lower(), key, text, options)
    except Exception as exc:  # noqa: BLE001
        return _err(exc)
    return result["output"]


@mcp.tool()
def parsel_chain(
    text: str,
    steps: list[dict[str, Any]],
    decode: bool = False,
) -> str:
    """Apply an ordered CHAIN of transforms (left-to-right) to craft layered payloads.

    `steps` is a list, each item {"transform": <key-or-name>, "options": {...}} (options
    optional). Example to leetspeak then base64 then zero-width-hide:
      steps=[{"transform":"leetspeak"},{"transform":"base64"},
             {"transform":"zerowidth_steganography"}]
    Set decode=true to REVERSE a chain: steps are applied in reverse order with action=decode
    (every transform in the chain must be decodable). Returns the final text.
    Stack encodings to defeat keyword filters, then tell the target how to decode.
    """
    if not steps:
        return "[parsel error] 'steps' must contain at least one {transform, options}."
    try:
        ordered = list(reversed(steps)) if decode else steps
        action = "decode" if decode else "encode"
        out = text
        applied: list[str] = []
        for step in ordered:
            name = str(step.get("transform", "")).strip()
            if not name:
                return "[parsel error] each step needs a 'transform' key."
            key = bridge.resolve_key(name)
            if not key:
                return f"[parsel error] unknown transform '{name}' in chain."
            opts = step.get("options") if isinstance(step.get("options"), dict) else None
            out = bridge.run_transform(action, key, out, opts)["output"]
            applied.append(key)
    except Exception as exc:  # noqa: BLE001
        return _err(exc)
    arrow = " <- " if decode else " -> "
    return f"[chain {arrow.join(applied)}]\n{out}"


@mcp.tool()
def parsel_decode(text: str) -> str:
    """Universal smart decoder: auto-detect the encoding of `text` and decode it.

    Use when you have obfuscated/encoded text and don't know the scheme. Returns the best
    guess (method + decoded text) plus a few ranked alternatives, since detection is
    heuristic. For a known scheme, prefer parsel_transform(action='decode').
    """
    try:
        result = bridge.auto_decode(text)
    except Exception as exc:  # noqa: BLE001
        return _err(exc)
    if not result:
        return "No decoding matched. Try parsel_transform with an explicit transform+decode."
    lines = [f"best guess: {result.get('method')}", result.get("text", "")]
    alts = result.get("alternatives") or []
    if alts:
        lines.append("")
        lines.append("alternatives:")
        for a in alts[:8]:
            lines.append(f"  [{a.get('method')}] {str(a.get('text',''))[:120]}")
    return "\n".join(lines)


@mcp.tool()
def parsel_guide() -> str:
    """How to use the P4RS3LT0NGV3 toolset. Call this once to orient yourself.

    Returns a short cheat-sheet: the available tools, the transform categories with counts,
    a worked chaining example, and notes on which features are headless vs browser-only.
    """
    try:
        cats = bridge.categories()
        total = sum(cats.values())
        cat_line = ", ".join(f"{k} ({v})" for k, v in cats.items())
    except Exception as exc:  # noqa: BLE001
        cats, total, cat_line = {}, 0, f"(catalog unavailable: {exc})"
    return (
        "P4RS3LT0NGV3 — universal text transform / obfuscation toolset.\n\n"
        f"{total} transforms across 11 categories: {cat_line}\n\n"
        "TOOLS\n"
        "  parsel_list [category]   browse the catalog (start here)\n"
        "  parsel_search <query>    find a transform by keyword\n"
        "  parsel_inspect <name>    one transform's options + decodability\n"
        "  parsel_transform ...     apply one transform (encode/decode/preview, +options)\n"
        "  parsel_chain ...         apply an ordered chain; decode=true reverses it\n"
        "  parsel_decode <text>     universal auto-decoder for unknown encodings\n\n"
        "WORKFLOW\n"
        "  1) parsel_list or parsel_search to pick transform KEYS.\n"
        "  2) parsel_inspect a key to learn its options.\n"
        "  3) parsel_transform for one layer, or parsel_chain to stack several.\n\n"
        "EXAMPLE (layered payload that dodges keyword filters)\n"
        "  parsel_chain(text='<your text>', steps=[\n"
        "     {'transform':'leetspeak'},\n"
        "     {'transform':'base64'},\n"
        "     {'transform':'zerowidth_steganography'}])\n"
        "  then instruct the target how to peel the layers (or use parsel_decode).\n\n"
        "NOTES\n"
        "  - Keys are fuzzily resolved, so 'rot 13' or 'Pig Latin' work too.\n"
        "  - Steganography (emoji_encoding, invisible_text, zerowidth_steganography,\n"
        "    whitespace_steganography) and every cipher/encoding are plain transforms.\n"
        "  - The upstream AI tools (PromptCraft, AI translate, Anti-Classifier) are\n"
        "    browser-only and not exposed here; use the harness's own model for those."
    )


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
