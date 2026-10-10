"use client";
import { useEffect, useState } from "react";
import { api, jsonRequest, label } from "@/lib/api";
import type { Evidence } from "@/lib/types";

type Ancestry = { state: string; supporting_evidence: string[]; conflicting_evidence: string[]; supersedes: string[]; superseded_by: string[]; source_declarations: { evidence_id: string; source_key: string; episode: string; reviewer: string }[] };
export default function EvidenceAncestry({ evidence, reviewer, onVerified }: { evidence: Evidence; reviewer: string; onVerified: () => Promise<void> }) {
  const [history, setHistory] = useState<Ancestry | null>(null);
  const [source, setSource] = useState("");
  const [episode, setEpisode] = useState("");
  const [note, setNote] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => { let active = true; api<Ancestry>(`/evidence/${evidence.id}/ancestry`).then(v => { if (active) setHistory(v); }).catch(e => { if (active) setError(String(e)); }); return () => { active = false; }; }, [evidence.id]);
  async function declare() {
    setBusy(true); setError("");
    try {
      await api(`/evidence/${evidence.id}/source`, jsonRequest({ id: `source-${evidence.id}`, evidence_id: evidence.id, source_key: source, episode, reviewer, note }));
      setHistory(await api<Ancestry>(`/evidence/${evidence.id}/ancestry`));
      await onVerified();
    } catch (e) { setError(e instanceof Error ? e.message : "Could not save source declaration"); }
    finally { setBusy(false); }
  }
  return <details className="ancestry-panel"><summary>Evidence ancestry & independent support</summary>
    {history && <><p><strong>{label(history.state)}</strong> · applies only to supported footprints.</p>
      <p className="small">Supporting evidence: {history.supporting_evidence.join(", ")}</p>
      {history.conflicting_evidence.length > 0 && <p className="amber-text small">Conflicting evidence: {history.conflicting_evidence.join(", ")}</p>}
      {history.supersedes.length > 0 && <p className="small">Supersedes: {history.supersedes.join(", ")}</p>}
      {history.superseded_by.length > 0 && <p className="small">Superseded by: {history.superseded_by.join(", ")}. Original decision retained.</p>}
      {history.source_declarations.filter(d => history.supporting_evidence.includes(d.evidence_id)).map(d => <p className="small" key={d.evidence_id}>{d.source_key} / episode {d.episode} · declared by {d.reviewer}</p>)}
      {!history.source_declarations.some(d => d.evidence_id === evidence.id) && <div className="source-fields">
        <p className="small muted">Record the actual acquisition episode. Repeated frames or duplicate image bytes do not count as independent support. Declarations are permanent; confidence is not increased numerically.</p>
        <label>Instrument / source<input value={source} maxLength={100} onChange={e => setSource(e.target.value)} /></label>
        <label>Acquisition episode<input value={episode} maxLength={100} onChange={e => setEpisode(e.target.value)} /></label>
        <label>Independence rationale<textarea value={note} maxLength={500} onChange={e => setNote(e.target.value)} /></label>
        <button className="button secondary" disabled={busy || source.trim().length < 2 || episode.trim().length < 2 || note.trim().length < 3} onClick={declare}>Record source declaration</button>
      </div>}
    </>}
    {error && <p role="alert">{error}</p>}
  </details>;
}
