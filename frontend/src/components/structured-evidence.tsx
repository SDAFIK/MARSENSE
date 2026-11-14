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
  inference_attempts?: { id: string; timestamp: string; model_output: { engine: string; version: string; confidence_label: string } }[];
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
  function openSection(next: (typeof sections)[number]) {
    setSection(next);
    if (window.matchMedia("(max-width: 1099px)").matches) requestAnimationFrame(() => document.getElementById("evidence-detail")?.scrollIntoView({ block: "start" }));
  }
  const [historyRecord, setHistoryRecord] = useState<{ id: string; value: History } | null>(null);
  const history = historyRecord?.id === selected?.id ? historyRecord?.value : null;
  const [error, setError] = useState("");
  const [observation, setObservation] = useState<{ id: string; metadata_note: string; original_asset_reference: string | null; asset_sha256: string } | null>(null);
  useEffect(() => {
    let active = true;
    if (selected?.observation_id)
      api<{ id: string; metadata_note: string; original_asset_reference: string | null; asset_sha256: string }>(`/observations/${selected.observation_id}`)
        .then((value) => { if (active) setObservation(value); })
        .catch(() => { if (active) setObservation(null); });
    return () => { active = false; };
  }, [selected?.observation_id]);
  const savedObservation = observation?.id === selected?.observation_id ? observation : null;
  useEffect(() => {
    let active = true;
    if (selected)
      api<History>(`/evidence/${selected.id}/history`)
        .then((h) => {
          if (active) {
            setHistoryRecord({ id: selected.id, value: h });
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
    <div className="structured-evidence evidence-studio-v3">
      <aside className="panel">
        <nav aria-label="Evidence hierarchy">
          {sections.map((s) => (
            <button
              key={s}
              className={section === s ? "selected" : ""}
              aria-pressed={section === s}
              onClick={() => openSection(s)}
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
      <section className="evidence-image-stage panel"><div className="studio-intro"><span className="eyebrow">01 / COMPARE THE EVIDENCE</span><h2>Two views. One decision.</h2><p>Preserve the orbital prior and examine what the ground observation changes.</p></div>
        <div className="panel-heading">
          <h2>Expected vs observed · {section}</h2>
        </div>
        <div className="evidence-focus-strip"><div><span className="eyebrow">EVIDENCE STATE</span><strong>{selected ? label(selected.verification_state) : "Awaiting ground observation"}</strong><span className="small muted">{selected ? label(selected.discrepancy) : "NASA orbital prior preserved"}</span></div>{selected && <button className="button primary" onClick={() => openSection("HUMAN DECISION")}>Open human review</button>}</div>
        <div className="evidence-paired"><figure><div className="evidence-pair-image"><Image unoptimized fill sizes="(max-width:720px) 90vw, 420px" src="/api/assets/jezero-hirise.png" alt="Cached NASA orbital terrain"/></div><figcaption>EXPECTED · NASA orbital prior<br/><strong>{label(selected?.expected_value ?? prior?.observed_value ?? "unknown")}</strong></figcaption></figure><figure><div className="evidence-pair-image"><Image unoptimized fill sizes="(max-width:720px) 90vw, 420px" src={selected?.raw_asset_reference ?? "/api/assets/ground-navcam.jpg"} alt="Ground evidence or cached Navcam example"/></div><figcaption>OBSERVED · {selected ? label(selected.source_type) : "Cached example · no observation"}<br/><strong>{selected ? label(selected.observed_value) : "Awaiting observation"}</strong></figcaption></figure></div>
        <details className="studio-original"><summary>Inspect original source image</summary><div className="evidence-source-image">
          <Image
            loading="eager"
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
        </p></details>
      </section>
      <aside className="panel studio-detail" id="evidence-detail" aria-label="Evidence detail">
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
                  {savedObservation && <>
                    <dt>Observation metadata</dt>
                    <dd>{savedObservation.metadata_note}</dd>
                    {savedObservation.original_asset_reference && <>
                      <dt>Original bytes</dt>
                      <dd><a href={savedObservation.original_asset_reference} download>Download original image</a></dd>
                      <dt>Original SHA-256</dt>
                      <dd className="small" style={{ overflowWrap: "anywhere" }}>{savedObservation.asset_sha256}</dd>
                    </>}
                  </>}
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
                {selected?.model_output?.confidence === null && <p>No calibrated numerical confidence is available.</p>}
                {selected?.source_type === "demo_replay" && (
                  <p>Replay annotations are not actual model inference.</p>
                )}
                {selected?.model_output && Object.entries(selected.model_output.features).map(([name, value]) => (
                  <p key={name} className="small muted">{label(name)}: {value} · measured image feature, not terrain probability</p>
                ))}
                {history?.inference_attempts?.map((attempt) => (
                  <p key={attempt.id} className="small muted">Retry · {attempt.timestamp} · {attempt.model_output.engine} · {attempt.model_output.confidence_label}</p>
                ))}
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
                  <summary>Orbital CRISM science context</summary>
                  {snapshot.data_status.manifest.crism?.available ? (
                    <>
                      <p>{snapshot.data_status.manifest.crism.product_id}</p>
                      <p>
                        DERIVED spectral browse ·{" "}
                        {snapshot.data_status.manifest.crism.resolution_m}{" "}
                        m/pixel. No mineral identity inferred.
                      </p>
                      <p>
                        {snapshot.data_status.manifest.crism.channels?.join(
                          " / ",
                        )}
                      </p>
                      {snapshot.data_status.manifest.crism.limitations?.map(
                        (limit) => (
                          <p key={limit}>{limit}</p>
                        ),
                      )}
                      <p>
                        Source SHA-256:{" "}
                        {snapshot.data_status.manifest.crism.source?.sha256 ??
                          "Unavailable"}
                      </p>
                      {snapshot.data_status.manifest.crism.source?.url && (
                        <a
                          href={snapshot.data_status.manifest.crism.source.url}
                          target="_blank"
                          rel="noreferrer"
                        >
                          Official CRISM source
                        </a>
                      )}
                    </>
                  ) : (
                    <p>
                      {snapshot.data_status.manifest.crism?.reason ??
                        "CRISM context unavailable."}
                    </p>
                  )}
                </details>
                {snapshot.data_status.manifest.cameras?.map((camera) => (
                  <details key={camera.product_id}>
                    <summary>
                      Calibrated {camera.instrument.join(" / ")}
                    </summary>
                    <p>
                      {camera.product_id} · version {camera.version_id}
                    </p>
                    <p>
                      Sol {camera.sol} · SCLK {camera.sclk}
                    </p>
                    <p>
                      PLACES interval match:{" "}
                      {camera.clock_interval_matched ? "Yes" : "No"}.
                      Observation clock match:{" "}
                      {camera.observation_clock_matched ? "Yes" : "No"}.
                    </p>
                    <p>
                      Image footprint unavailable. Spatial uncertainty unknown.
                    </p>
                    {camera.limitations.map((limit) => (
                      <p key={limit}>{limit}</p>
                    ))}
                    <p>Source SHA-256: {camera.raw_sha256}</p>
                    <a
                      href={camera.source_url}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Official camera source
                    </a>
                  </details>
                ))}
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
