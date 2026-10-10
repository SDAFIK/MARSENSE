"use client";
import Image from "next/image";
import { useEffect, useState } from "react";
import { api, label } from "@/lib/api";
import type { Evidence, Snapshot } from "@/lib/types";
import EvidenceReview from "./evidence-review";
const sections = [
  "NASA PRIOR",
  "GROUND OBSERVATION",
  "MODEL INFERENCE",
  "HUMAN INTERPRETATION",
  "HUMAN DECISION",
  "MISSION CONSEQUENCE",
  "PROVENANCE",
  "HISTORY",
] as const;
type History = {
  decisions: {
    id: string;
    reviewer: string;
    decision: string;
    timestamp: string;
    note: string;
    human_terrain: string | null;
  }[];
  interpretations: { terrain: string; timestamp: string }[];
  legacy_decision: boolean;
};
export default function StructuredEvidence({
  snapshot,
  selected,
  onSelect,
  verified,
}: {
  snapshot: Snapshot;
  selected?: Evidence;
  onSelect: (id: string) => void;
  verified: () => Promise<void>;
}) {
  const [section, setSection] =
    useState<(typeof sections)[number]>("GROUND OBSERVATION");
  const [history, setHistory] = useState<History | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    if (selected)
      api<History>(`/evidence/${selected.id}/history`)
        .then((h) => {
          if (active) {
            setHistory(h);
            setError("");
          }
        })
        .catch((e) => {
          if (active) setError(String(e));
        });
    return () => {
      active = false;
    };
  }, [selected]);
  const prior = snapshot.evidence.find(
    (e) =>
      e.source_type === "orbital" &&
      (!selected || e.region_id === selected.region_id),
  );
  return (
    <div className="structured-evidence">
      <aside className="panel">
        <nav aria-label="Evidence hierarchy">
          {sections.map((s) => (
            <button
              key={s}
              className={section === s ? "selected" : ""}
              aria-pressed={section === s}
              onClick={() => setSection(s)}
            >
              {s}
            </button>
          ))}
        </nav>
        <div className="panel-heading">
          <h2>EVIDENCE RECORDS</h2>
        </div>
        <div className="evidence-records">
          {snapshot.evidence
            .filter((e) => e.source_type !== "orbital")
            .map((e) => (
              <button
                key={e.id}
                aria-pressed={selected?.id === e.id}
                onClick={() => onSelect(e.id)}
              >
                <strong>{label(e.observed_value)}</strong>
                <small>
                  {label(e.verification_state)} · {e.mission_id.toUpperCase()}
                </small>
              </button>
            ))}
        </div>
      </aside>
      <section className="evidence-image-stage panel">
        <div className="panel-heading">
          <h2>{section}</h2>
        </div>
        <div className="evidence-source-image">
          <Image
            unoptimized
            fill
            sizes="(max-width: 720px) 100vw, 850px"
            src={
              section === "NASA PRIOR"
                ? "/api/assets/jezero-hirise.png"
                : (selected?.raw_asset_reference ??
                  "/api/assets/ground-navcam.jpg")
            }
            alt={
              section === "NASA PRIOR"
                ? "Original cached NASA orbital imagery"
                : "Original ground observation associated with selected evidence"
            }
          />
        </div>
        <p className="small muted">
          {section === "NASA PRIOR"
            ? "NASA-derived orbital pixels; terrain interpretation is illustrative."
            : (selected?.source ??
              "Cached Navcam replay; no ground evidence recorded yet.")}
        </p>
      </section>
      <aside className="panel">
        <div className="panel-heading">
          <h2>{section}</h2>
        </div>
        {section === "HUMAN DECISION" && selected ? (
          <EvidenceReview
            key={selected.id}
            evidence={selected}
            reviewer={snapshot.astronaut.name}
            onVerified={verified}
            detailed
          />
        ) : (
          <div className="panel-body">
            {section === "NASA PRIOR" && (
              <>
                <h3>{label(prior?.observed_value ?? "unknown")}</h3>
                <p>ORBITAL-ONLY · original prior retained.</p>
                <p>{snapshot.assumptions[0]?.statement}</p>
              </>
            )}
            {section === "GROUND OBSERVATION" && (
              <>
                <h3>
                  {selected
                    ? label(selected.observed_value)
                    : "Awaiting observation"}
                </h3>
                <dl>
                  <dt>Recorded</dt>
                  <dd>{selected?.timestamp ?? "—"}</dd>
                  <dt>State</dt>
                  <dd>
                    {selected
                      ? label(selected.verification_state)
                      : "No decision"}
                  </dd>
                  <dt>Source</dt>
                  <dd>{selected?.source ?? "Cached replay"}</dd>
                  <dt>Supported footprint</dt>
                  <dd>
                    {selected
                      ? `${selected.location.join(", ")} local meters · illustrative/manual placement`
                      : "Unavailable"}
                  </dd>
                </dl>
              </>
            )}
            {section === "MODEL INFERENCE" && (
              <>
                <h3>
                  {selected?.source_type === "demo_replay"
                    ? "CURATED REPLAY"
                    : "EXPERIMENTAL / UNCALIBRATED"}
                </h3>
                <p>
                  {selected?.model_output?.engine ?? "No inference"} ·{" "}
                  {selected?.model_output?.version}
                </p>
                <p>
                  {selected?.model_output?.confidence_label ??
                    "Unknown quality"}
                </p>
                {selected?.source_type === "demo_replay" && (
                  <p>Replay annotations are not actual model inference.</p>
                )}
                {selected?.model_output?.limitations.map((l) => (
                  <p key={l} className="small muted">
                    {l}
                  </p>
                ))}
              </>
            )}
            {section === "HUMAN INTERPRETATION" && (
              <>
                <h3>Human interpretation</h3>
                {history?.interpretations.length ? (
                  history.interpretations.map((i, n) => (
                    <p key={n}>
                      {label(i.terrain)}
                      <br />
                      {i.timestamp}
                    </p>
                  ))
                ) : (
                  <p>No human terrain interpretation recorded.</p>
                )}
                <p className="small muted">
                  Actual model output remains separate from the reviewer’s
                  interpretation.
                </p>
              </>
            )}
            {section === "MISSION CONSEQUENCE" && (
              <>
                <h3>{selected?.consequence.alert ?? "No active challenge"}</h3>
                <p>{selected?.consequence.explanation}</p>
                <p>{selected?.consequence.route_segment_ids.join(", ")}</p>
                <p>{snapshot.assumptions[0]?.statement}</p>
              </>
            )}
            {section === "PROVENANCE" && (
              <>
                <h3>Source provenance</h3>
                <p>{selected?.source ?? prior?.source}</p>
                <p className="small">
                  {selected?.raw_asset_reference ?? prior?.raw_asset_reference}
                </p>
                <p>
                  Camera footprint / georegistration unresolved; replay
                  footprints are illustrative.
                </p>
                <details>
                  <summary>NASA source manifest</summary>
                  <pre>
                    {JSON.stringify(snapshot.data_status.manifest, null, 2)}
                  </pre>
                </details>
              </>
            )}
            {section === "HISTORY" && (
              <>
                <h3>Preserved decisions</h3>
                {history?.decisions.map((d) => (
                  <article key={d.id}>
                    <strong>
                      {label(d.decision)} · {d.reviewer}
                    </strong>
                    <p>{d.timestamp}</p>
                    <p>{d.note}</p>
                  </article>
                ))}
                {history?.legacy_decision && (
                  <p>Legacy decision: {selected?.verification_note}</p>
                )}
                <p className="small muted">
                  Prior evidence and final human decisions remain in history.
                </p>
              </>
            )}
            {error && <p role="alert">{error}</p>}
            {!selected && section !== "NASA PRIOR" && (
              <p>
                Record an observation in Mission Control to inspect its
                evidence.
              </p>
            )}
          </div>
        )}
      </aside>
    </div>
  );
}
