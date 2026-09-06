import { useEffect, useState } from "react";
import { Button } from "../atoms/Button";
import { ModalFrame } from "../atoms/ModalFrame";
import { PanelMessage } from "../atoms/PanelMessage";
import { SelectInput } from "../atoms/SelectInput";
import { SurfacePanel } from "../atoms/SurfacePanel";
import { TextInput } from "../atoms/TextInput";

const EMPTY_SETTINGS = { guildName: "", serverSlug: "", serverRegion: "US" };

export function SettingsModal({ discovery, onClose }) {
  const [draft, setDraft] = useState(discovery.settings || EMPTY_SETTINGS);
  const [saveError, setSaveError] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    setDraft(discovery.settings || EMPTY_SETTINGS);
  }, [discovery.settings]);

  const update = (field, value) => {
    setSaved(false);
    setSaveError("");
    setDraft((current) => ({ ...current, [field]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSaveError("");
    try {
      await discovery.saveSettings(draft);
      setSaved(true);
    } catch (err) {
      setSaveError(err.message || "Unable to save guild settings.");
    }
  };

  const titleId = "application-settings-title";
  return (
    <ModalFrame titleId={titleId} onClose={onClose} closeLabel="Close settings">
      <SurfacePanel className="mx-auto w-full max-w-xl p-5 sm:p-6">
        <div className="flex items-start justify-between gap-4 border-b border-white/10 pb-4">
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-emerald-300">Application</p>
            <h2 id={titleId} className="mt-2 text-2xl font-semibold text-white">Settings</h2>
            <p className="mt-1.5 text-sm text-slate-400">Preferences are stored only in this browser.</p>
          </div>
          <button type="button" onClick={onClose} aria-label="Close settings" className="rounded-lg p-2 text-slate-400 transition hover:bg-white/5 hover:text-white">
            <span aria-hidden className="text-xl">&times;</span>
          </button>
        </div>

        <form className="mt-5 space-y-4" onSubmit={handleSubmit}>
          <div>
            <h3 className="text-sm font-semibold text-slate-100">Guild report discovery</h3>
            <p className="mt-1 text-xs leading-5 text-slate-500">Show the latest public reports uploaded to your Warcraft Logs guild.</p>
          </div>
          <div>
            <label htmlFor="settings-guild-name" className="text-sm font-medium text-slate-200">Guild name</label>
            <TextInput id="settings-guild-name" value={draft.guildName} onChange={(event) => update("guildName", event.target.value)} placeholder="Guild name" required />
          </div>
          <div className="grid gap-4 sm:grid-cols-[1fr_8rem]">
            <div>
              <label htmlFor="settings-server-slug" className="text-sm font-medium text-slate-200">Realm slug</label>
              <TextInput id="settings-server-slug" value={draft.serverSlug} onChange={(event) => update("serverSlug", event.target.value)} placeholder="area-52" required />
              <p className="mt-1.5 text-xs text-slate-500">Use the realm portion from the Warcraft Logs guild URL.</p>
            </div>
            <div>
              <label htmlFor="settings-server-region" className="text-sm font-medium text-slate-200">Region</label>
              <SelectInput id="settings-server-region" value={draft.serverRegion} onChange={(event) => update("serverRegion", event.target.value)}>
                {['US', 'EU', 'KR', 'TW', 'CN'].map((region) => <option key={region} value={region}>{region}</option>)}
              </SelectInput>
            </div>
          </div>

          {saveError || discovery.error ? <PanelMessage tone="danger">{saveError || discovery.error}</PanelMessage> : null}
          {saved && discovery.guild ? (
            <PanelMessage tone="success">Saved {discovery.guild.name} — {discovery.guild.server_name}. Found {discovery.reports.length} recent reports.</PanelMessage>
          ) : null}

          <div className="flex flex-wrap justify-between gap-3 border-t border-white/10 pt-4">
            <Button type="button" variant="secondary" size="sm" onClick={() => { discovery.clearSettings(); setDraft(EMPTY_SETTINGS); setSaved(false); }} disabled={!discovery.settings || discovery.isLoading}>Clear saved guild</Button>
            <div className="flex gap-3">
              <Button type="button" variant="secondary" size="sm" onClick={onClose}>Close</Button>
              <Button type="submit" variant="primary" size="sm" disabled={discovery.isLoading || !draft.guildName.trim() || !draft.serverSlug.trim()}>{discovery.isLoading ? "Checking..." : "Save guild"}</Button>
            </div>
          </div>
        </form>
      </SurfacePanel>
    </ModalFrame>
  );
}
