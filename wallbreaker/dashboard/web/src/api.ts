export interface ConfigInfo {
  has_target: boolean;
  target: string | null;
  target_modality?: string;
  profile: string | null;
  judge: string | null;
}

export interface Scorecard {
  asr?: number;
  total?: number;
  hits?: number;
  grade?: string;
  by_technique?: Record<string, { hits: number; total: number }>;
  by_category?: Record<string, { hits: number; total: number }>;
  [k: string]: unknown;
}

export interface Overview {
  config: ConfigInfo;
  scorecard: Scorecard;
  findings_count: number;
  runs_count: number;
  latest_run: string | null;
}

export interface Finding {
  label: string;
  technique?: string;
  payload?: string;
  reason?: string;
  response?: string;
  category?: string;
}

export interface RunSummary {
  name: string;
  size: number;
  records: number;
  hits: number;
}

export interface Preset { name: string; description: string }
export interface Transform { name: string; description: string; lossy: boolean; reversible: boolean }
export interface Tool { name: string; description: string }

export interface FireResult {
  prompt: string;
  content: string;
  is_error: boolean;
  verdict: string;
}

async function j<T>(url: string, init?: RequestInit): Promise<T> {
  const r = await fetch(url, init);
  if (!r.ok) {
    let detail = r.statusText;
    try {
      const body = await r.json();
      detail = body.detail || detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return r.json() as Promise<T>;
}

export const api = {
  overview: () => j<Overview>("/api/overview"),
  config: () => j<ConfigInfo>("/api/config"),
  findings: () => j<Finding[]>("/api/findings"),
  runs: () => j<RunSummary[]>("/api/runs"),
  run: (name: string) => j<{ name: string; total: number; records: Record<string, unknown>[] }>(`/api/runs/${encodeURIComponent(name)}`),
  presets: () => j<Preset[]>("/api/presets"),
  transforms: () => j<Transform[]>("/api/transforms"),
  tools: () => j<Tool[]>("/api/tools"),
  fire: (body: Record<string, unknown>) =>
    j<FireResult>("/api/fire", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
};

export function verdictKind(label: string | undefined): "bypass" | "partial" | "held" | "neutral" {
  const v = (label || "").toUpperCase();
  if (v === "COMPLIED") return "bypass";
  if (v === "PARTIAL") return "partial";
  if (v === "REFUSED") return "held";
  return "neutral";
}
