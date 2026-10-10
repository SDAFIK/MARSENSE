"use client";
import Image from "next/image";
import { useState } from "react";
import { label } from "@/lib/api";
import type { Coordinate, Evidence, Snapshot } from "@/lib/types";
import LivingMap from "./living-map";
import ObservationPanel from "./observation-panel";
import EvidenceReview from "./evidence-review";
import RouteSummary from "./route-summary";

const steps = ["EXPECT", "OBSERVE", "COMPARE", "VERIFY", "LEARN"] as const;
type Step = (typeof steps)[number];
export default function MissionControl({
  snapshot,
  selected,
  busy,
  setBusy,
  observed,
  verified,
  onSelect,
  onFuture,
}: {
  snapshot: Snapshot;
  selected?: Evidence;
  busy: boolean;
  setBusy: (value: boolean) => void;
  observed: (evidence: Evidence) => Promise<void>;
  verified: () => Promise<void>;
  onSelect: (id: string) => void;
  onFuture: () => void;
}) {
  const [step, setStep] = useState<Step>("EXPECT");
  const [eventId, setEventId] = useState<string | null>(null);
  const region =
    snapshot.regions.find((r) => r.name.startsWith("Area 14")) ??
    snapshot.regions[0];
  const prior = snapshot.evidence.find(
    (e) => e.source_type === "orbital" && e.region_id === region?.id,
  );
  const active = snapshot.routes.find(
    (r) => r.id === snapshot.mission.active_route_id,
  );
  const alpha = snapshot.routes.find((r) => r.version === 1);
  const beta = snapshot.routes.find((r) => r.version > 1);
  const alphaChallenged = Boolean(
    selected &&
    alpha &&
    selected.verification_state !== "REJECTED" &&
    !selected.superseded_by?.length &&
    selected.consequence.route_segment_ids.includes(`${alpha.id}-segment-3`),
  );
  const pending =
    selected &&
    ["PROVISIONAL", "NEEDS_MORE_EVIDENCE"].includes(
      selected.verification_state,
    );
  const event = snapshot.events.find((e) => e.id === eventId);
  const focus: Coordinate | undefined = event?.evidence_id
    ? snapshot.evidence.find((e) => e.id === event.evidence_id)?.location
    : undefined;
  async function analyze(e: Evidence) {
    await observed(e);
    setStep(e.consequence.relevant ? "COMPARE" : "OBSERVE");
  }
  async function decide() {
    await verified();
    setStep("LEARN");
  }
  function selectEvent(id: string, evidenceId: string | null) {
    setEventId(id);
    if (evidenceId) {
      onSelect(evidenceId);
      setStep("COMPARE");
    } else setStep("EXPECT");
  }
  return (
    <div className="recovery-control">
      <div
        className="recovery-workflow"
        role="tablist"
        aria-label="Mission workflow"
      >
        {steps.map((s, i) => (
          <button
            key={s}
            id={`workflow-${s}`}
            role="tab"
            aria-selected={step === s}
            aria-controls="mission-context"
            tabIndex={step === s ? 0 : -1}
            onClick={() => setStep(s)}
            onKeyDown={(e) => {
              const next =
                e.key === "ArrowRight"
                  ? (i + 1) % steps.length
                  : e.key === "ArrowLeft"
                    ? (i + steps.length - 1) % steps.length
                    : e.key === "Home"
                      ? 0
                      : e.key === "End"
                        ? steps.length - 1
                        : null;
              if (next !== null) {
                e.preventDefault();
                setStep(steps[next]);
                document.getElementById(`workflow-${steps[next]}`)?.focus();
              }
            }}
          >
            {s}
          </button>
        ))}
        <span>HUMAN DECISION AUTHORITY</span>
      </div>
      <div className="recovery-columns">
        <aside
          className="recovery-left"
          aria-label="Mission trace and evidence"
        >
          <section className="panel">
            <div className="panel-heading">
              <h2>MISSION TRACE</h2>
              <span>{snapshot.mission.eva}</span>
            </div>
            <div className="trace-image">
              <Image
                unoptimized
                fill
                sizes="240px"
                src="/api/assets/ground-navcam.jpg"
                alt="Cached NASA Navcam replay image; illustrative mission association"
              />
            </div>
            <dl className="trace-data">
              <div>
                <dt>Mission</dt>
                <dd>{snapshot.mission.id.toUpperCase()}</dd>
              </div>
              <div>
                <dt>Target</dt>
                <dd>{snapshot.target.name}</dd>
              </div>
              <div>
                <dt>Active route</dt>
                <dd>{active?.name ?? "Unavailable"}</dd>
              </div>
              <div>
                <dt>Region</dt>
                <dd>{region?.name.split(" \u00b7 ")[0]}</dd>
              </div>
              <div>
                <dt>Knowledge</dt>
                <dd
                  className={
                    region?.knowledge_state === "GROUND_OBSERVED"
                      ? "mint-text"
                      : ""
                  }
                >
                  {label(region?.knowledge_state ?? "UNKNOWN")}
                </dd>
              </div>
            </dl>
          </section>
          <section className="panel">
            <div className="panel-heading">
              <h2>EVIDENCE</h2>
            </div>
            <div className="recovery-evidence">
              <button onClick={() => setStep("EXPECT")}>
                <span>NASA PRIOR · PRESERVED</span>
                <strong>
                  {label(
                    prior?.observed_value ??
                      region?.prior_interpretation ??
                      "unknown",
                  )}
                </strong>
                <small>Orbital-only interpretation</small>
              </button>
              <button onClick={() => setStep(selected ? "COMPARE" : "OBSERVE")}>
                <span>GROUND OBSERVATION</span>
                <strong>
                  {selected
                    ? label(selected.observed_value)
                    : "Awaiting observation"}
                </strong>
                <small>
                  {selected
                    ? label(selected.verification_state)
                    : "Human review required"}
                </small>
              </button>
              <button onClick={() => setStep("VERIFY")}>
                <span>HUMAN DECISION</span>
                <strong>
                  {selected
                    ? label(selected.verification_state)
                    : "No decision yet"}
                </strong>
                <small>
                  {selected?.verified_by ?? "AI cannot confirm the map"}
                </small>
              </button>
            </div>
          </section>
          <section className="panel">
            <div className="panel-heading">
              <h2>ROUTE</h2>
            </div>
            <div className="recovery-routes">
              <p>
                <i className="line alpha" />
                Alpha <span>{label(alpha?.status ?? "Unavailable")}</span>
              </p>
              <p>
                <i className="line beta" />
                Beta{" "}
                <span>{beta ? label(beta.status) : "After verification"}</span>
              </p>
              <p className="small muted">
                Off-white · prior / Mint · alternative
                <br />
                Amber dashed · challenged segment
              </p>
              <button
                className="button secondary full"
                onClick={() => setStep("LEARN")}
              >
                WHY THIS ROUTE?
              </button>
            </div>
          </section>
          {pending && (
            <button
              className="button secondary full review-required"
              onClick={() => setStep("VERIFY")}
            >
              REVIEW REQUIRED · CONFIRM / REQUEST / REJECT
            </button>
          )}
          {snapshot.mission.inherited_evidence.length > 0 && (
            <div className="inheritance-label">
              INHERITED FROM EVA-01
              <br />
              {region?.name.split(" \u00b7 ")[0]} ·{" "}
              {label(region?.knowledge_state ?? "UNKNOWN")}
            </div>
          )}
          <p className="recovery-limit">
            Illustrative mission geometry.
            <br />
            Ground footprint requires human review.
          </p>
        </aside>
        <div className="recovery-map">
          <LivingMap
            snapshot={snapshot}
            focusLocation={focus}
            warmPresentation
          />
          <div className="map-knowledge-label">
            <strong>{region?.name.split(" \u00b7 ")[0]}</strong>
            <span>{label(region?.knowledge_state ?? "UNKNOWN")}</span>
            {alphaChallenged && (
              <span className="challenged-text">
                A17 · ALPHA SEGMENT 3 CHALLENGED
              </span>
            )}
          </div>
        </div>
        <aside
          className="recovery-inspector"
          key={step}
          id="mission-context"
          role="tabpanel"
          aria-labelledby={`workflow-${step}`}
          tabIndex={0}
        >
          <div className="context-heading">
            <h2>{step}</h2>
            <span>{region?.name.split(" \u00b7 ")[0]}</span>
          </div>
          {step === "EXPECT" && (
            <section className="context-body">
              <span className="eyebrow">NASA PRIOR</span>
              <h3>Orbital-only expectation</h3>
              <div className="prior-preview">
                <Image
                  unoptimized
                  fill
                  sizes="294px"
                  src="/api/assets/jezero-hirise.png"
                  alt="Original grayscale cached HiRISE terrain crop"
                />
              </div>
              <p>
                {label(region?.prior_interpretation ?? "unknown")} ·
                illustrative terrain interpretation
              </p>
              <h3>MISSION ASSUMPTION</h3>
              <p>{snapshot.assumptions[0]?.statement}</p>
              <span className="badge neutral">
                {label(snapshot.assumptions[0]?.status ?? "UNKNOWN")}
              </span>
              <p className="small muted">
                CTX / HiRISE imagery is cached. The orbital prior remains
                preserved after ground review.
              </p>
              <button
                className="button secondary full"
                onClick={() => setStep("OBSERVE")}
              >
                OBSERVE THE GROUND
              </button>
            </section>
          )}
          {step === "OBSERVE" && (
            <ObservationPanel
              missionId={snapshot.mission.id}
              busy={busy}
              setBusy={setBusy}
              onComplete={analyze}
            />
          )}
          {step === "COMPARE" && (
            <section className="context-body">
              <div className="qualitative-compare">
                <article>
                  <span>EXPECTED · ORBITAL-ONLY</span>
                  <div className="compare-image">
                    <Image
                      unoptimized
                      fill
                      sizes="294px"
                      src="/api/assets/jezero-hirise.png"
                      alt="Original cached orbital imagery supporting the illustrative prior"
                    />
                  </div>
                  <h3>
                    {selected
                      ? selected.expected_value === "soil"
                        ? "Low obstruction"
                        : label(selected.expected_value)
                      : label(region?.prior_interpretation ?? "unknown")}
                  </h3>
                  <p>{snapshot.assumptions[0]?.statement}</p>
                </article>
                <article>
                  <span>OBSERVED · GROUND</span>
                  {selected && (
                    <div className="compare-image">
                      <Image
                        unoptimized
                        fill
                        sizes="294px"
                        src={selected.raw_asset_reference}
                        alt="Ground observation associated with selected evidence"
                      />
                    </div>
                  )}
                  <h3>
                    {selected
                      ? label(selected.observed_value)
                      : "Awaiting observation"}
                  </h3>
                  <p>
                    {selected
                      ? label(selected.verification_state)
                      : "Record a ground observation"}
                  </p>
                </article>
              </div>
              {selected && (
                <>
                  <span className="badge amber">
                    {label(selected.discrepancy)}
                  </span>
                  <h3>MISSION IMPACT</h3>
                  <p>{selected.consequence.explanation}</p>
                  {alphaChallenged && (
                    <p className="challenged-text">
                      A17 challenged
                      <br />
                      Route Alpha Segment 3 affected
                    </p>
                  )}
                  <p className="small muted">
                    {selected.source_type === "demo_replay"
                      ? "Curated replay; simulated footprint. This is not actual model inference."
                      : selected.model_output?.limitations.join(" ")}
                  </p>
                  <button
                    className="button secondary full"
                    onClick={() => setStep("VERIFY")}
                  >
                    HUMAN VERIFICATION
                  </button>
                </>
              )}
            </section>
          )}
          {step === "VERIFY" &&
            (selected ? (
              <>
                <EvidenceReview
                  key={selected.id}
                  evidence={selected}
                  reviewer={snapshot.astronaut.name}
                  onVerified={decide}
                />
                <div className="context-body decision-metadata">
                  <span className="eyebrow">DECISION RECORD</span>
                  <dl>
                    <dt>Reviewer</dt>
                    <dd>{selected.verified_by ?? "Pending human review"}</dd>
                    <dt>Decision time</dt>
                    <dd>
                      {selected.verified_at
                        ? new Date(selected.verified_at).toISOString()
                        : "Not yet recorded"}
                    </dd>
                    <dt>Interpretation / note</dt>
                    <dd>{selected.verification_note ?? "Not yet confirmed"}</dd>
                    <dt>Evidence source</dt>
                    <dd>{selected.source}</dd>
                  </dl>
                </div>
              </>
            ) : (
              <section className="context-body">
                <h3>Human review required</h3>
                <p>
                  Record an observation first. AI cannot confirm map knowledge.
                </p>
                <button
                  className="button secondary full"
                  onClick={() => setStep("OBSERVE")}
                >
                  RECORD OBSERVATION
                </button>
              </section>
            ))}
          {step === "LEARN" && (
            <>
              <RouteSummary snapshot={snapshot} />
              <section className="context-body">
                <h3>DURABLE LOCAL MEMORY</h3>
                <p>
                  Confirmed persistent evidence stays within its supported
                  footprint. Dynamic conditions expire.
                </p>
                {snapshot.mission.id === "eva-01" && (
                  <button className="button secondary full" onClick={onFuture}>
                    OPEN FUTURE EVA
                  </button>
                )}
              </section>
            </>
          )}
        </aside>
      </div>
      <section
        className="recovery-timeline"
        aria-label="Spatial mission timeline"
      >
        <div className="timeline-heading">
          <strong>MISSION MEMORY</strong>
          <span>Select an event to locate its evidence</span>
        </div>
        <div className="timeline-events">
          {[...snapshot.events]
            .sort((a, b) => Date.parse(a.timestamp) - Date.parse(b.timestamp))
            .map((e) => (
              <button
                key={e.id}
                aria-pressed={eventId === e.id}
                onClick={() => selectEvent(e.id, e.evidence_id)}
              >
                <span>
                  {new Date(e.timestamp).toISOString().slice(11, 19)} UTC
                </span>
                <strong>{e.title}</strong>
                <small>
                  {e.evidence_id ? "Locate evidence →" : "Orbital prior →"}
                </small>
              </button>
            ))}
        </div>
      </section>
    </div>
  );
}
