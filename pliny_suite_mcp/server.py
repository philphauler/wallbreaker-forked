"""
Pliny suite MCP server — everything besides pure parsel transforms.

Parsel lives in wallbreaker-parsel (p4rs3lt0ngv3_mcp). This server exposes:
  - pliny_status / pliny_guide
  - l1b_* (L1B3RT4S seed catalog)
  - sysprompt_* (leaked product system-prompt corpus)
  - st3gg_* (steganography detect/analyze)
  - imagedefender_info
  - t3mp3st_selftest (offline harness)
"""

from __future__ import annotations

import json
import os
import re
import struct
import subprocess
import sys
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

WB_ROOT = Path(os.environ.get("WALLBREAKER_ROOT", r"C:\Users\philp\wallbreaker")).resolve()
PLINY_ROOT = Path(os.environ.get("PLINY_ROOT", r"C:\Users\philp\research\elder-plinius")).resolve()
ST3GG = PLINY_ROOT / "ST3GG"
T3MP3ST = PLINY_ROOT / "T3MP3ST"
IMAGEDEF = PLINY_ROOT / "ImageDefender"
L1B_DIRS = [
    WB_ROOT / "library" / "L1B3RT4S",
    PLINY_ROOT / "L1B3RT4S",
]
SP_DIR = WB_ROOT / "library" / "system_prompts"
CLARITAS = WB_ROOT / "library" / "CL4R1T4S"

# Prefer wallbreaker venv python for ST3GG if needed; system python works for ST3GG
PY = sys.executable

mcp = FastMCP("pliny-suite", log_level="WARNING")


def _ok(data: Any) -> str:
    if isinstance(data, str):
        return data
    return json.dumps(data, indent=2, ensure_ascii=False, default=str)


def _l1b_dir() -> Path | None:
    for d in L1B_DIRS:
        if d.is_dir() and any(d.glob("*.mkd")):
            return d
    return None


def _l1b_files() -> list[Path]:
    d = _l1b_dir()
    if not d:
        return []
    skip = {"token80m8", "tokenade"}
    out = []
    for p in sorted(d.glob("*.mkd")):
        if p.stem.lower() in skip:
            continue
        try:
            if p.stat().st_size > 400_000:
                continue
        except OSError:
            continue
        out.append(p)
    return out


@mcp.tool()
def pliny_guide() -> str:
    """How to use the full Pliny/Wallbreaker MCP stack from an agent session.

    Call once when cold. Explains which MCP server owns which tools and the
    intended workflow for cyber / Bob hardening (not jailbreaking the host chat).
    """
    return """\
PLINY + WALLBREAKER MCP STACK (authorized cyber hardening only)

MCP SERVERS
  wallbreaker-parsel  → parsel_guide, parsel_list, parsel_search, parsel_inspect,
                        parsel_transform, parsel_chain, parsel_decode
                        (222 text transforms / P4RS3LT0NGV3)
  pliny-suite         → this server: status, L1B3RT4S seeds, system prompts,
                        ST3GG stego analysis, ImageDefender info, T3MP3ST self-tests
  t3mp3st             → security_recon (nmap/DNS) when dig/nmap on PATH

WORKFLOW
  1) pliny_status          — see what is READY
  2) parsel_*              — mutate/encode adversarial cases for Bob redteam
  3) l1b_list / l1b_search / l1b_get — vendor seed catalog (defense research)
  4) sysprompt_list / sysprompt_search / sysprompt_get — format reference
  5) st3gg_analyze_text or st3gg_analyze_image — stego detect
  6) t3mp3st_selftest      — offline harness gates
  7) cyber: node scripts/cyber-pliny-redteam.mjs  (uses live wallbreaker mutations)

NEVER claim Pliny unlocks Grok. Tools harden Bob/cyber product surfaces.
"""


@mcp.tool()
def pliny_status() -> str:
    """Health check for every Pliny/Wallbreaker component used by agents."""
    status: dict[str, Any] = {"roots": {"wallbreaker": str(WB_ROOT), "elder_plinius": str(PLINY_ROOT)}}

    # parsel
    try:
        sys.path.insert(0, str(WB_ROOT))
        from p4rs3lt0ngv3_mcp import bridge  # type: ignore

        status["parsel"] = {"ok": True, "transforms": len(bridge.list_transforms()), "categories": bridge.categories()}
    except Exception as e:  # noqa: BLE001
        status["parsel"] = {"ok": False, "error": str(e)}

    # L1B3RT4S
    d = _l1b_dir()
    files = _l1b_files()
    status["l1b3rt4s"] = {
        "ok": bool(files),
        "path": str(d) if d else None,
        "seeds": len(files),
        "models": [p.stem for p in files[:12]],
    }

    # system_prompts
    sp_ok = SP_DIR.is_dir() and any(SP_DIR.rglob("*.md"))
    vendors = sorted({p.relative_to(SP_DIR).parts[0] for p in SP_DIR.rglob("*.md")}) if sp_ok else []
    status["system_prompts"] = {"ok": sp_ok, "path": str(SP_DIR), "vendors": len(vendors), "vendor_names": vendors[:20]}

    # CL4R1T4S
    status["cl4r1t4s"] = {"ok": CLARITAS.is_dir(), "path": str(CLARITAS)}

    # ST3GG
    status["st3gg"] = {
        "ok": (ST3GG / "stegg_cli.py").is_file(),
        "path": str(ST3GG),
        "cli": str(ST3GG / "stegg_cli.py"),
    }

    # ImageDefender
    status["imagedefender"] = {
        "ok": (IMAGEDEF / "index.html").is_file(),
        "path": str(IMAGEDEF),
        "index_bytes": (IMAGEDEF / "index.html").stat().st_size if (IMAGEDEF / "index.html").is_file() else 0,
    }

    # T3MP3ST
    status["t3mp3st"] = {
        "ok": (T3MP3ST / "package.json").is_file() and (T3MP3ST / "dist" / "mcp-server.js").is_file(),
        "path": str(T3MP3ST),
        "mcp": str(T3MP3ST / "dist" / "mcp-server.js"),
        "has_node_modules": (T3MP3ST / "node_modules").is_dir(),
    }

    # P4RS3 on disk
    p4 = PLINY_ROOT / "P4RS3LT0NGV3"
    status["p4rs3lt0ngv3_repo"] = {"ok": p4.is_dir(), "path": str(p4)}

    status["summary"] = {
        "ready": [k for k, v in status.items() if isinstance(v, dict) and v.get("ok")],
        "not_ready": [k for k, v in status.items() if isinstance(v, dict) and "ok" in v and not v.get("ok")],
    }
    return _ok(status)


@mcp.tool()
def l1b_list() -> str:
    """List L1B3RT4S jailbreak seed models (.mkd files) available on disk."""
    files = _l1b_files()
    if not files:
        return _ok({"ok": False, "error": "L1B3RT4S not present. Run install-pliny-libs.ps1"})
    return _ok({
        "ok": True,
        "count": len(files),
        "path": str(_l1b_dir()),
        "models": [{"name": p.stem, "bytes": p.stat().st_size} for p in files],
    })


@mcp.tool()
def l1b_search(query: str) -> str:
    """Search L1B3RT4S seed names and contents for a keyword (max 20 hits)."""
    q = (query or "").strip().lower()
    if not q:
        return _ok({"ok": False, "error": "query required"})
    files = _l1b_files()
    hits = []
    for p in files:
        score = 0
        if q in p.stem.lower():
            score += 10
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if q in text.lower():
            score += 1 + text.lower().count(q)
            # first matching line snippet
            snip = ""
            for line in text.splitlines():
                if q in line.lower():
                    snip = line.strip()[:160]
                    break
            hits.append({"model": p.stem, "score": score, "snippet": snip})
        elif score:
            hits.append({"model": p.stem, "score": score, "snippet": ""})
    hits.sort(key=lambda h: h["score"], reverse=True)
    return _ok({"ok": True, "query": query, "hits": hits[:20]})


@mcp.tool()
def l1b_get(model: str, max_chars: int = 8000) -> str:
    """Fetch one L1B3RT4S seed by model name (e.g. ANTHROPIC, XAI, CHATGPT). Truncated for agents."""
    name = (model or "").strip().lstrip("!#")
    if not name:
        return _ok({"ok": False, "error": "model required"})
    files = _l1b_files()
    # fuzzy match
    pick = None
    for p in files:
        if p.stem.lower() == name.lower():
            pick = p
            break
    if not pick:
        for p in files:
            if name.lower() in p.stem.lower():
                pick = p
                break
    if not pick:
        return _ok({"ok": False, "error": f"no seed matching '{model}'", "models": [p.stem for p in files[:30]]})
    text = pick.read_text(encoding="utf-8", errors="replace")
    cap = max(500, min(int(max_chars or 8000), 40000))
    truncated = len(text) > cap
    return _ok({
        "ok": True,
        "model": pick.stem,
        "path": str(pick),
        "bytes": pick.stat().st_size,
        "truncated": truncated,
        "content": text[:cap],
        "note": "Defense research / Bob redteam only. Do not fire against unauthorized targets.",
    })


@mcp.tool()
def sysprompt_list() -> str:
    """List vendors in the system_prompts (leaks) corpus under wallbreaker/library."""
    if not SP_DIR.is_dir():
        return _ok({"ok": False, "error": f"missing {SP_DIR}"})
    vendors = {}
    for p in SP_DIR.rglob("*.md"):
        if p.stem.lower() in {"readme", "license", "contributing"}:
            continue
        rel = p.relative_to(SP_DIR)
        v = rel.parts[0] if len(rel.parts) > 1 else "_root"
        vendors.setdefault(v, 0)
        vendors[v] += 1
    return _ok({"ok": True, "path": str(SP_DIR), "vendors": vendors, "vendor_count": len(vendors)})


@mcp.tool()
def sysprompt_search(query: str, limit: int = 15) -> str:
    """Search system_prompts corpus by path/name/content keyword."""
    q = (query or "").strip().lower()
    if not q:
        return _ok({"ok": False, "error": "query required"})
    if not SP_DIR.is_dir():
        return _ok({"ok": False, "error": f"missing {SP_DIR}"})
    hits = []
    for p in SP_DIR.rglob("*.md"):
        if p.stem.lower() in {"readme", "license", "contributing"}:
            continue
        rel = str(p.relative_to(SP_DIR)).replace("\\", "/")
        score = 0
        if q in rel.lower():
            score += 5
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if q in text.lower():
            score += 1
            snip = next((ln.strip()[:140] for ln in text.splitlines() if q in ln.lower()), "")
            hits.append({"path": rel, "score": score, "snippet": snip, "bytes": p.stat().st_size})
        elif score:
            hits.append({"path": rel, "score": score, "snippet": "", "bytes": p.stat().st_size})
        if len(hits) > 200:
            break
    hits.sort(key=lambda h: h["score"], reverse=True)
    return _ok({"ok": True, "query": query, "hits": hits[: max(1, min(limit, 40))]})


@mcp.tool()
def sysprompt_get(path: str, max_chars: int = 6000) -> str:
    """Get one system_prompt file by relative path under library/system_prompts."""
    if not path or ".." in path:
        return _ok({"ok": False, "error": "relative path required, no .."})
    p = (SP_DIR / path).resolve()
    if not str(p).startswith(str(SP_DIR.resolve())):
        return _ok({"ok": False, "error": "path escapes corpus"})
    if not p.is_file():
        # try with .md
        if not path.endswith(".md"):
            p = (SP_DIR / f"{path}.md").resolve()
        if not p.is_file():
            return _ok({"ok": False, "error": f"not found: {path}"})
    text = p.read_text(encoding="utf-8", errors="replace")
    cap = max(500, min(int(max_chars or 6000), 40000))
    return _ok({
        "ok": True,
        "path": str(p.relative_to(SP_DIR)).replace("\\", "/"),
        "truncated": len(text) > cap,
        "content": text[:cap],
    })


@mcp.tool()
def st3gg_list_tools() -> str:
    """List ST3GG steganography analysis tools (stegg_cli list-tools)."""
    source = ST3GG / "analysis_tools.py"
    if not source.is_file():
        return _ok({"ok": False, "error": f"ST3GG missing at {ST3GG}"})
    text = source.read_text(encoding="utf-8", errors="replace")
    tools = sorted(set(re.findall(r"TOOL_REGISTRY\.register\(['\"]([^'\"]+)", text)))
    return _ok({"ok": bool(tools), "count": len(tools), "tools": tools})


@mcp.tool()
def st3gg_analyze_text(text: str) -> str:
    """Detect unicode / zero-width / whitespace / homoglyph stego in a text string (ST3GG)."""
    if not text:
        return _ok({"ok": False, "error": "text required"})
    zero_width = [ch for ch in text if ord(ch) in (0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF, 0x180E)]
    variation = [ch for ch in text if 0xFE00 <= ord(ch) <= 0xFE0F or 0xE0100 <= ord(ch) <= 0xE01EF]
    trailing = [i + 1 for i, line in enumerate(text.splitlines()) if line.endswith((" ", "\t"))]
    base64_hits = re.findall(r"(?<![A-Za-z0-9+/])[A-Za-z0-9+/]{16,}={0,2}(?![A-Za-z0-9+/])", text)
    hex_hits = re.findall(r"(?<![0-9A-Fa-f])(?:[0-9A-Fa-f]{2}){8,}(?![0-9A-Fa-f])", text)
    findings = {
        "zero_width": len(zero_width),
        "variation_selectors": len(variation),
        "trailing_whitespace_lines": trailing[:100],
        "base64_candidates": base64_hits[:20],
        "hex_candidates": hex_hits[:20],
    }
    return _ok({
        "ok": True,
        "length": len(text),
        "zero_width_count": len(zero_width),
        "suspicious": any((zero_width, variation, trailing, base64_hits, hex_hits)),
        "findings": findings,
    })


@mcp.tool()
def st3gg_analyze_image(image_path: str) -> str:
    """Analyze an image for steganography indicators via ST3GG stegg_cli analyze."""
    p = Path(image_path)
    if not p.is_file():
        return _ok({"ok": False, "error": f"file not found: {image_path}"})
    data = p.read_bytes()
    result: dict[str, Any] = {"ok": True, "path": str(p), "bytes": len(data), "findings": []}
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        result["format"] = "png"
        chunks, pos, end = [], 8, None
        while pos + 12 <= len(data):
            size = struct.unpack(">I", data[pos:pos + 4])[0]
            kind = data[pos + 4:pos + 8].decode("latin1")
            chunks.append({"type": kind, "bytes": size})
            pos += 12 + size
            if kind == "IEND":
                end = pos
                break
        result["chunks"] = chunks
        if end is not None and end < len(data): result["findings"].append(f"{len(data) - end} trailing bytes after IEND")
        for c in chunks:
            if c["type"] in {"tEXt", "zTXt", "iTXt"}: result["findings"].append(f"metadata chunk {c['type']} ({c['bytes']} bytes)")
    elif data.startswith(b"\xff\xd8\xff"):
        result["format"] = "jpeg"
        end = data.rfind(b"\xff\xd9")
        if end >= 0 and end + 2 < len(data): result["findings"].append(f"{len(data) - end - 2} trailing bytes after EOI")
        result["comment_segments"] = data.count(b"\xff\xfe")
    else:
        result["format"] = "unknown"
        result["findings"].append("unsupported image signature")
    result["suspicious"] = bool(result["findings"])
    return _ok(result)


@mcp.tool()
def imagedefender_info() -> str:
    """ImageDefender product/demo info — adversarial watermark demo for cyber stego defense UI."""
    idx = IMAGEDEF / "index.html"
    readme = IMAGEDEF / "README.md"
    return _ok({
        "ok": idx.is_file(),
        "path": str(IMAGEDEF),
        "index": str(idx) if idx.is_file() else None,
        "index_bytes": idx.stat().st_size if idx.is_file() else 0,
        "readme": readme.read_text(encoding="utf-8", errors="replace")[:2000] if readme.is_file() else None,
        "use": "Open index.html for the demo UI patterns; use for cyber ImageDefender product surface, not model unlock.",
    })


@mcp.tool()
def t3mp3st_selftest() -> str:
    """Run T3MP3ST offline self-tests (refusal-frontier + model-fallback). No live target needed."""
    if not T3MP3ST.is_dir():
        return _ok({"ok": False, "error": f"T3MP3ST missing at {T3MP3ST}"})
    results = []
    for script in ("scripts/refusal-frontier.mjs", "scripts/test-model-fallback.mjs"):
        path = T3MP3ST / script
        if not path.is_file():
            results.append({"script": script, "ok": False, "error": "missing"})
            continue
        args = ["node", str(path)]
        if "refusal-frontier" in script:
            args.append("--self-test")
        r = subprocess.run(
            args,
            cwd=str(T3MP3ST),
            capture_output=True,
            text=True,
            timeout=180,
            env={**os.environ, "PATH": os.environ.get("PATH", "")},
        )
        tail = ((r.stdout or "") + (r.stderr or "")).strip().splitlines()[-12:]
        results.append({
            "script": script,
            "ok": r.returncode == 0,
            "exit": r.returncode,
            "tail": tail,
        })
    return _ok({"ok": all(x.get("ok") for x in results), "results": results})


@mcp.tool()
def t3mp3st_doctor() -> str:
    """T3MP3ST doctor summary (file checks + tool availability)."""
    script = T3MP3ST / "scripts" / "doctor.mjs"
    if not script.is_file():
        return _ok({"ok": False, "error": "doctor.mjs missing"})
    r = subprocess.run(
        ["node", str(script)],
        cwd=str(T3MP3ST),
        capture_output=True,
        text=True,
        timeout=120,
    )
    return _ok({
        "ok": r.returncode == 0,
        "exit": r.returncode,
        "output": ((r.stdout or "") + (r.stderr or ""))[-6000:],
    })


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
