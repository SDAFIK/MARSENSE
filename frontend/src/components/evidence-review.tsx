"use client";
import { useEffect, useState } from "react";
import { ArrowRight, Check, ChevronDown, ShieldAlert, X } from "lucide-react";
import { api, jsonRequest, label } from "@/lib/api";
import type { Evidence, Terrain, Verification } from "@/lib/types";
import EvidenceAncestry from "./evidence-ancestry";
export default function EvidenceReview({
  evidence,
  reviewer,
  onVerified,
  detailed = false,
}: {
  evidence: Evidence;
  reviewer: string;
  onVerified: () => Promise<void>;
  detailed?: boolean;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [note, setNote] = useState(
    evidence.persistence_type === "dynamic"
      ? "Visual inspection confirms the temporary visibility condition."
      : "Visual inspection confirms the terrain shown in the supported footprint.",
  );
  const [humanTerrain, setHumanTerrain] = useState<Terrain>("unknown");
  const [supersedes, setSupersedes] = useState("");
  const pending = ["PROVISIONAL", "NEEDS_MORE_EVIDENCE"].includes(
    evidence.verification_state,
  );
  const weak =
    evidence.persistence_type === "persistent" &&
    ((evidence.model_confidence ?? 0) < 0.5 ||
      evidence.observed_value === "unknown");
  const conflict = evidence.discrepancy === "CONFLICTING_EVIDENCE";
  async function verify(decision: Exclude<Verification, "PROVISIONAL">) {
    setBusy(true);
    setError(null);
    try {
      await api(
        `/evidence/${evidence.id}/verify`,
        jsonRequest({
          decision,
          reviewer,
          note,
          ...(detailed && supersedes.trim() ? { supersedes: supersedes.split(",").map(s => s.trim()).filter(Boolean) } : {}),
          ...(weak && humanTerrain !== "unknown"
            ? { human_terrain: humanTerrain }
            : {}),
        }),
      );
      await onVerified();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Verification failed. Evidence remains provisional.",
      );
    } finally {
      setBusy(false);
    }
  }
  const [clock, setClock] = useState(() => Date.now());
  useEffect(() => {
    const timer = setInterval(() => setClock(Date.now()), 10000);
    return () => clearInterval(timer);
  }, []);
  const stale = Boolean(
    evidence.valid_until && Date.parse(evidence.valid_until) < clock,
  );
  return (
    <section className="panel review-panel" aria-label="Evidence review">
      <div className="panel-heading">
        <h2>
          <ShieldAlert size={17} />
          {pending ? "Review the difference" : "Verified decision"}
        </h2>
        <span
          className={`badge ${evidence.verification_state === "CONFIRMED" ? "green" : "amber"}`}
        >
          {stale ? "STALE" : label(evidence.verification_state)}
        </span>
      </div>
      <div className="panel-body">
        {evidence.consequence.alert && pending && !stale && (
          <div className="alert-banner">
            <ShieldAlert size={18} />
            <div>
              <strong>{evidence.consequence.alert}</strong>
              <span>Route assumption requires your attention</span>
            </div>
          </div>
        )}
        <div className="comparison-pair">
          <div>
            <span className="small-mono">EXPECTED / ORBITAL</span>
            <strong>{label(evidence.expected_value)}</strong>
          </div>
          <ArrowRight size={18} />
          <div>
            <span className="small-mono">OBSERVED / GROUND</span>
            <strong>{label(evidence.observed_value)}</strong>
          </div>
        </div>
        <span
          className={`badge ${evidence.discrepancy === "MATCH" ? "green" : "amber"}`}
        >
          {label(evidence.discrepancy)}
        </span>
        <p className="consequence-copy">{!pending && <span className="small-mono muted">RECORDED CONSEQUENCE · </span>}{evidence.consequence.explanation}</p>
        <div className="review-summary">
          <span>Evidence quality</span>
          <strong>
            {evidence.model_output?.confidence_label ?? "Orbital prior"}
          </strong>
          <span>Persistence</span>
          <strong>
            {evidence.persistence_type === "dynamic"
              ? "Dynamic · 30-minute validity"
              : "Terrain · supported footprint only"}
          </strong>
        </div>
        {pending && (
          <>
            <label className="field-label" htmlFor={`note-${evidence.id}`}>
              Your verification note
            </label>
            <textarea
              id={`note-${evidence.id}`}
              value={note}
              maxLength={500}
              onChange={(e) => setNote(e.target.value)}
              rows={2}
            />
            {weak && (
              <label className="field-label">
                Human terrain identification
                <select
                  aria-label="Human terrain identification"
                  value={humanTerrain}
                  onChange={(e) => setHumanTerrain(e.target.value as Terrain)}
                >
                  <option value="unknown">
                    Unknown · request more evidence
                  </option>
                  {[
                    "soil",
                    "sand",
                    "bedrock",
                    "large rocks",
                    "rough terrain",
                    "obstacle-rich terrain",
                  ].map((v) => (
                    <option key={v}>{v}</option>
                  ))}
                </select>
              </label>
            )}
            {conflict && (
              <p className="small amber-text">
                This conflicts with verified evidence. Another observation is
                required before confirmation.
              </p>
            )}
            <button
              className="button primary full"
              disabled={
                busy ||
                (conflict && !(detailed && supersedes.trim())) ||
                (weak && humanTerrain === "unknown") ||
                note.trim().length < 3 ||
                stale
              }
              onClick={() => verify("CONFIRMED")}
            >
              <Check size={16} />
              {busy ? "Saving decision…" : "Confirm observation"}
            </button>
            <div className="review-actions">
              <button disabled={busy} onClick={() => verify("REJECTED")}>
                <X size={14} /> Reject
              </button>
              <button
                disabled={busy}
                onClick={() => verify("NEEDS_MORE_EVIDENCE")}
              >
                Request more evidence
              </button>
            </div>
            <p className="annotation-note">
              Your decision updates the map. AI alone cannot.
            </p>
          </>
        )}
        {!pending && (
          <div className="decision-record">
            <Check size={17} />
            <span>
              <strong>
                {evidence.verification_state === "CONFIRMED"
                  ? `Confirmed by ${evidence.verified_by}`
                  : "Rejected · prior interpretation retained"}
              </strong>
              <small>{evidence.verification_note}</small>
            </span>
          </div>
        )}
        {detailed && pending && conflict && <label className="source-fields">Explicitly supersede confirmed evidence IDs (comma separated)
          <input value={supersedes} onChange={e => setSupersedes(e.target.value)} />
          <span className="small muted">Replacement must cover each entire footprint. Original decisions remain in history. Explain your reassessment in the review note above.</span>
        </label>}
        {detailed && <EvidenceAncestry evidence={evidence} reviewer={reviewer} onVerified={onVerified} />}
        {error && (
          <p role="alert" className="error-message">
            {error}
          </p>
        )}
        <details open={detailed}>
          <summary>
            Evidence provenance <ChevronDown size={14} />
          </summary>
          <dl className="provenance">
            <dt>Source</dt>
            <dd>{evidence.source}</dd>
            <dt>Inference</dt>
            <dd>
              {evidence.model_output?.engine ?? "NASA orbital source"} /{" "}
              {evidence.model_output?.version ?? "original"}
            </dd>
            <dt>Recorded (UTC)</dt>
            <dd>
              {new Date(evidence.timestamp)
                .toISOString()
                .replace("T", " ")
                .slice(0, 19)}
            </dd>
            <dt>Local location</dt>
            <dd>{evidence.location.join(", ")} m</dd>
            <dt>Evidence ID</dt>
            <dd>{evidence.id}</dd>
          </dl>
          {evidence.model_output?.limitations.map((item) => (
            <p key={item} className="small muted">
              {item}
            </p>
          ))}
        </details>
      </div>
    </section>
  );
}
