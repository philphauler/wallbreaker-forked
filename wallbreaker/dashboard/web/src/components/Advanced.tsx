import { useEffect, useState } from "react";
import { api, type AdvancedSettings, type AgentConfig, type TypicalConfiguration } from "../api";
import { AdvancedSettingsDrawer, DEFAULT_ADVANCED_SETTINGS, mergeAdvancedSettings, normalizeAdvancedSettings } from "./AdvancedSettingsDrawer";
import { AgentConfigDrawer, DEFAULT_AGENT_CONFIG, normalizeAgentConfig } from "./AgentConfigDrawer";

export function Advanced() {
  const [agent, setAgent] = useState<AgentConfig>(DEFAULT_AGENT_CONFIG);
  const [advanced, setAdvanced] = useState<AdvancedSettings>(DEFAULT_ADVANCED_SETTINGS);
  const [presets, setPresets] = useState<TypicalConfiguration[]>([]);
  const [status, setStatus] = useState(""); const [busy, setBusy] = useState(false);
  useEffect(() => { api.settings().then((value) => { setAgent(normalizeAgentConfig(value.agent)); setAdvanced(normalizeAdvancedSettings(value.advanced)); setPresets(value.typical_configurations || []); }); }, []);
  const save = async (body: Record<string, unknown>, message="saved") => { setBusy(true); setStatus(""); try { const value = await api.saveSettings(body); setAgent(normalizeAgentConfig(value.agent)); setAdvanced(normalizeAdvancedSettings(value.advanced)); setStatus(message); } catch (error) { setStatus((error as Error).message); } finally { setBusy(false); } };
  const apply = (preset: TypicalConfiguration) => { const next = mergeAdvancedSettings(advanced, preset.advanced); setAdvanced(next); setAgent(normalizeAgentConfig(preset.agent)); void save({ typical_configuration: preset.id, agent: preset.agent, advanced: next }, `${preset.name} saved`); };
  return <div className="grid">
    <div className="card"><h3>Agent runtime</h3><AgentConfigDrawer value={agent} onChange={setAgent} disabled={busy} onSave={() => void save({ agent })} saving={busy} status={status} /></div>
    <AdvancedSettingsDrawer value={advanced} presets={presets} onChange={setAdvanced} onSave={() => void save({ advanced })} onApplyPreset={apply} saving={busy} status={status} />
  </div>;
}
