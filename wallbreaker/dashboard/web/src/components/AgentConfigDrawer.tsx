import type { AgentConfig } from "../api";

export const DEFAULT_AGENT_CONFIG: AgentConfig = {
  max_rounds: 8,
  max_tokens: 8192,
};

function clampNumber(value: number, fallback: number, lo: number, hi: number): number {
  if (!Number.isFinite(value)) return fallback;
  return Math.max(lo, Math.min(hi, Math.trunc(value)));
}

export function normalizeAgentConfig(value?: Partial<AgentConfig> | null): AgentConfig {
  return {
    max_rounds: clampNumber(Number(value?.max_rounds), DEFAULT_AGENT_CONFIG.max_rounds, 1, 50),
    max_tokens: clampNumber(Number(value?.max_tokens), DEFAULT_AGENT_CONFIG.max_tokens, 256, 32000),
  };
}

export function AgentConfigDrawer({
  value,
  onChange,
  disabled = false,
  onSave,
  saveLabel = "Save defaults",
  saving = false,
  status = "",
}: {
  value: AgentConfig;
  onChange: (value: AgentConfig) => void;
  disabled?: boolean;
  onSave?: () => void;
  saveLabel?: string;
  saving?: boolean;
  status?: string;
}) {
  const setField = (key: keyof AgentConfig, raw: string) => {
    const next = normalizeAgentConfig({ ...value, [key]: Number.parseInt(raw || "0", 10) });
    onChange(next);
  };

  return (
    <details className="config-drawer">
      <summary>
        <span>Agent configuration</span>
        <span className="mono muted">{value.max_rounds} rounds | {value.max_tokens} tokens</span>
      </summary>
      <div className="config-drawer-body">
        <label className="fld">Max rounds</label>
        <input
          type="number"
          min={1}
          max={50}
          step={1}
          value={value.max_rounds}
          onChange={(event) => setField("max_rounds", event.target.value)}
          disabled={disabled}
        />
        <label className="fld">Max tokens per response</label>
        <input
          type="number"
          min={256}
          max={32000}
          step={256}
          value={value.max_tokens}
          onChange={(event) => setField("max_tokens", event.target.value)}
          disabled={disabled}
        />
        {(onSave || status) && (
          <div className="config-drawer-actions">
            {onSave && (
              <button type="button" className="mini-btn" disabled={disabled || saving} onClick={onSave}>
                {saving ? "Saving..." : saveLabel}
              </button>
            )}
            {status && <span className="mono muted">{status}</span>}
          </div>
        )}
      </div>
    </details>
  );
}
