import type { AdvancedSettings, RuntimeAdvancedSettings, TypicalConfiguration } from "../api";

const DEFAULT_RUNTIME: RuntimeAdvancedSettings = {
  auto: false, rounds: 12, no_tools: false, exit_on_finish: true,
  log: true, judge: false, resume: "",
};
export const DEFAULT_ADVANCED_SETTINGS: AdvancedSettings = { runtime: DEFAULT_RUNTIME };

export function normalizeAdvancedSettings(value?: Partial<AdvancedSettings> | null): AdvancedSettings {
  const runtime = value?.runtime || DEFAULT_RUNTIME;
  return { runtime: {
    auto: !!runtime.auto,
    rounds: Math.max(1, Math.min(50, Number(runtime.rounds) || 12)),
    no_tools: !!runtime.no_tools,
    exit_on_finish: runtime.exit_on_finish ?? true,
    log: runtime.log ?? true,
    judge: !!runtime.judge,
    resume: String(runtime.resume || ""),
  } };
}

export function mergeAdvancedSettings(base: AdvancedSettings, patch?: Partial<AdvancedSettings> | null): AdvancedSettings {
  return normalizeAdvancedSettings({ runtime: { ...base.runtime, ...(patch?.runtime || {}) } });
}

export function AdvancedSettingsDrawer({ value, presets, onChange, onSave, onApplyPreset, saving=false, status="" }: {
  value: AdvancedSettings; presets: TypicalConfiguration[]; onChange: (value: AdvancedSettings) => void;
  onSave: () => void; onApplyPreset: (preset: TypicalConfiguration) => void; saving?: boolean; status?: string;
  profileDetails?: unknown; defaultProfile?: string;
}) {
  const set = <K extends keyof RuntimeAdvancedSettings>(key: K, next: RuntimeAdvancedSettings[K]) =>
    onChange(normalizeAdvancedSettings({ runtime: { ...value.runtime, [key]: next } }));
  return <div className="advanced-page">
    <div className="advanced-presets">{presets.map((preset) => <button type="button" key={preset.id} className="preset-btn" disabled={saving} onClick={() => onApplyPreset(preset)}><b>{preset.name}</b><span>{preset.description}</span></button>)}</div>
    <div className="card"><h3>Runtime</h3><div className="advanced-grid">
      <label className="advanced-field"><span>Rounds</span><input type="number" min={1} max={50} value={value.runtime.rounds} onChange={(e) => set("rounds", Number(e.target.value))} /></label>
      <label className="advanced-field"><span>Resume path</span><input value={value.runtime.resume} onChange={(e) => set("resume", e.target.value)} /></label>
      {(["auto","no_tools","exit_on_finish","log","judge"] as const).map((key) => <label className="advanced-toggle" key={key}><input type="checkbox" checked={value.runtime[key]} onChange={(e) => set(key, e.target.checked)} /><span>{key.replace(/_/g, " ")}</span></label>)}
    </div><div className="config-drawer-actions"><button type="button" className="mini-btn" disabled={saving} onClick={onSave}>{saving ? "Saving..." : "Save advanced settings"}</button>{status && <span className="mono muted">{status}</span>}</div></div>
  </div>;
}
