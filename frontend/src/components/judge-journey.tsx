"use client";
import Link from "next/link";
import { ArrowRight, CheckCircle2, Compass } from "lucide-react";
import type { Evidence, Snapshot } from "@/lib/types";

type Step = "EXPECT" | "OBSERVE" | "COMPARE" | "VERIFY" | "LEARN";
export default function JudgeJourney({snapshot, selected, step, busy, onStep, onFuture}: {
  snapshot: Snapshot; selected?: Evidence; step: Step; busy: boolean;
  onStep: (step: Step) => void; onFuture: () => void;
}) {
  const inherited = snapshot.mission.id === "eva-02" && snapshot.mission.inherited_evidence.length > 0;
  const confirmed = selected?.verification_state === "CONFIRMED" && selected.persistence_type === "persistent";
  const pending = selected && ["PROVISIONAL", "NEEDS_MORE_EVIDENCE"].includes(selected.verification_state);
  const next = inherited ? 6 : confirmed ? 5 : pending ? (step === "VERIFY" ? 4 : 3) : (step === "OBSERVE" ? 2 : 1);
  const title = inherited ? "The next explorer has your knowledge." : confirmed ? "Your verified evidence is now part of the map." :
    pending ? "Review what the observation means." : "Start with one ground observation.";
  const detail = inherited ? "Open the memory archive to inspect the inherited record." :
    confirmed ? "Inspect the modeled route, then see how the next EVA starts with this evidence." :
    pending ? "Compare the prior and the new evidence. A human makes the final decision." :
    "Explore the orbital prior, then record a ground observation to discover what changes.";
  function advance() {
    if (confirmed) { if (step === "LEARN" && snapshot.mission.id === "eva-01") onFuture(); else onStep("LEARN"); }
    else if (pending) onStep(step === "VERIFY" ? "VERIFY" : step === "COMPARE" ? "VERIFY" : "COMPARE");
    else onStep("OBSERVE");
  }
  return <section className="v3-journey" aria-label="Guided mission">
    <div className="v3-journey-icon">{inherited ? <CheckCircle2/> : <Compass/>}</div>
    <div className="v3-journey-copy"><span className="eyebrow">GUIDED MISSION · {next} / 6</span><h2>{title}</h2><p>{detail}</p>
      <div className="v3-journey-progress" aria-label={`Journey stage ${next} of 6`}>{Array.from({length:6},(_,i)=><i key={i} data-current={i+1<=next}/>)}</div>
    </div>
    {inherited ? <Link className="button primary" href="/memory">Explore inherited memory <ArrowRight size={16}/></Link> :
      <button className="button primary" disabled={busy} onClick={advance}>{confirmed ? step === "LEARN" && snapshot.mission.id === "eva-01" ? "Continue to next EVA" : "Explore route result" : pending ? step === "COMPARE" || step === "VERIFY" ? "Open human review" : "Compare evidence" : "Go to observation"} <ArrowRight size={16}/></button>}
  </section>;
}
