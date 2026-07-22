// wb-node-mcp.mjs — Wallbreaker transforms as MCP (newline-delimited JSON-RPC, same style as kodon_mcp.mjs).
// Neutral tool names so agent hosts attach them. Engine: p4rs3lt0ngv3 via venv python.
import cp from "child_process";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const WB = path.resolve(__dirname, "..");
const PY = path.join(WB, ".venv", "Scripts", "python.exe");
const VERSION = "1.0.0";

function runTool(name, args) {
  const payload = JSON.stringify({ tool: name, args: args || {} });
  const code = `
import json, sys, os
os.chdir(${JSON.stringify(WB)})
sys.path.insert(0, ${JSON.stringify(WB)})
from p4rs3lt0ngv3_mcp.agent_server import (
  wb_guide, wb_list, wb_search, wb_inspect, wb_apply, wb_chain, wb_decode
)
req = json.loads(sys.stdin.read())
n, a = req.get("tool"), req.get("args") or {}
fns = {
  "wb_guide": lambda: wb_guide(),
  "wb_list": lambda: wb_list(a.get("category") or ""),
  "wb_search": lambda: wb_search(a.get("query") or ""),
  "wb_inspect": lambda: wb_inspect(a.get("transform") or ""),
  "wb_apply": lambda: wb_apply(
    a.get("transform") or "", a.get("text") or "",
    a.get("action") or "encode", a.get("options")),
  "wb_chain": lambda: wb_chain(a.get("text") or "", a.get("steps") or [], bool(a.get("decode"))),
  "wb_decode": lambda: wb_decode(a.get("text") or ""),
}
if n not in fns:
  print(f"[wb error] unknown tool {n!r}", end="")
  raise SystemExit(2)
print(fns[n](), end="")
`;
  try {
    return cp.execFileSync(PY, ["-c", code], {
      encoding: "utf8",
      timeout: 60000,
      cwd: WB,
      env: {
        ...process.env,
        PYTHONPATH: WB,
        PYTHONIOENCODING: "utf-8",
        PYTHONUTF8: "1",
      },
      input: payload,
      maxBuffer: 8 * 1024 * 1024,
    });
  } catch (e) {
    return (((e.stdout || "") + (e.stderr || "")).toString().trim()) || ("[wb error] " + e.message);
  }
}

const TOOLS = [
  {
    name: "wb_guide",
    description:
      "How to use the text transform catalog. Call once before encoding/decoding work. Returns tools, categories, and workflow.",
    inputSchema: { type: "object", properties: {}, required: [] },
    run: () => runTool("wb_guide", {}),
  },
  {
    name: "wb_list",
    description:
      "List text transforms. Optional category: encoding, cipher, unicode, format, case, symbol, technical, visual, concealment, signwriting, special.",
    inputSchema: {
      type: "object",
      properties: { category: { type: "string", description: "category filter or empty for all" } },
      required: [],
    },
    run: (a) => runTool("wb_list", a),
  },
  {
    name: "wb_search",
    description: "Search transforms by keyword (e.g. base64, morse, reverse, hex, rot, emoji).",
    inputSchema: {
      type: "object",
      properties: { query: { type: "string", description: "search query" } },
      required: ["query"],
    },
    run: (a) => runTool("wb_search", a),
  },
  {
    name: "wb_inspect",
    description: "Inspect one transform: options and whether decode is supported.",
    inputSchema: {
      type: "object",
      properties: { transform: { type: "string", description: "transform key or name" } },
      required: ["transform"],
    },
    run: (a) => runTool("wb_inspect", a),
  },
  {
    name: "wb_apply",
    description:
      "Apply one transform to text. action=encode|decode|preview. options from wb_inspect (e.g. shift for caesar).",
    inputSchema: {
      type: "object",
      properties: {
        transform: { type: "string" },
        text: { type: "string" },
        action: { type: "string", description: "encode|decode|preview" },
        options: { type: "object" },
      },
      required: ["transform", "text"],
    },
    run: (a) => runTool("wb_apply", a),
  },
  {
    name: "wb_chain",
    description:
      "Apply ordered chain of transforms. steps=[{transform, options?}]. decode=true reverses the chain.",
    inputSchema: {
      type: "object",
      properties: {
        text: { type: "string" },
        steps: { type: "array", items: { type: "object" } },
        decode: { type: "boolean" },
      },
      required: ["text", "steps"],
    },
    run: (a) => runTool("wb_chain", a),
  },
  {
    name: "wb_decode",
    description: "Auto-detect encoding of text and decode it.",
    inputSchema: {
      type: "object",
      properties: { text: { type: "string" } },
      required: ["text"],
    },
    run: (a) => runTool("wb_decode", a),
  },
];

function send(obj) {
  process.stdout.write(JSON.stringify(obj) + "\n");
}

function handle(line) {
  let msg;
  try {
    msg = JSON.parse(line);
  } catch {
    return;
  }
  const { id, method, params } = msg;
  if (method === "initialize") {
    send({
      jsonrpc: "2.0",
      id,
      result: {
        protocolVersion: "2025-06-18",
        capabilities: { tools: {} },
        serverInfo: { name: "wb", version: VERSION },
      },
    });
    return;
  }
  if (method === "notifications/initialized" || method === "initialized") return;
  if (method === "tools/list") {
    send({
      jsonrpc: "2.0",
      id,
      result: {
        tools: TOOLS.map(({ name, description, inputSchema }) => ({ name, description, inputSchema })),
      },
    });
    return;
  }
  if (method === "tools/call") {
    const name = params?.name;
    const args = params?.arguments || {};
    const tool = TOOLS.find((t) => t.name === name);
    const text = tool ? tool.run(args) : `[wb error] unknown tool ${name}`;
    send({
      jsonrpc: "2.0",
      id,
      result: { content: [{ type: "text", text: String(text) }], isError: !tool || String(text).startsWith("[wb error]") },
    });
    return;
  }
  if (method === "ping") {
    send({ jsonrpc: "2.0", id, result: {} });
    return;
  }
  if (id !== undefined) {
    send({ jsonrpc: "2.0", id, error: { code: -32601, message: `Method not found: ${method}` } });
  }
}

let buf = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (chunk) => {
  buf += chunk;
  let i;
  while ((i = buf.indexOf("\n")) >= 0) {
    const line = buf.slice(0, i).trim();
    buf = buf.slice(i + 1);
    if (line) handle(line);
  }
});
process.stdin.on("end", () => process.exit(0));
