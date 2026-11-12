"use client";
import Link from "next/link";
import { useState, useSyncExternalStore } from "react";
import { Database, RefreshCw } from "lucide-react";
import type { Evidence, View } from "@/lib/types";
import { useMission } from "@/lib/use-mission";
import MissionShell from "./mission-shell";
import MissionControl from "./mission-control";
import BeforeAfter from "./before-after";
import AstronautWorkspace from "./astronaut-workspace";
import StructuredEvidence from "./structured-evidence";
import SpatialMemory from "./spatial-memory";
function subscribeMission(callback: () => void) {
  window.addEventListener("storage", callback);
  window.addEventListener("marsense-mission-change", callback);
  return () => {
    window.removeEventListener("storage", callback);
    window.removeEventListener("marsense-mission-change", callback);
  };
}
function savedMission() {
  return sessionStorage.getItem("marsense-mission") === "eva-02"
    ? "eva-02"
    : "eva-01";
}
export default function MissionWorkspace({ view }: { view: View }) {
  const missionId = useSyncExternalStore(
    subscribeMission,
    savedMission,
    () => "eva-01",
  );
  const { snapshot, error, loading, refresh } = useMission(missionId);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const ground =
    snapshot?.evidence.filter((e) => e.source_type !== "orbital") ?? [];
  const selected =
    ground.find((e) => e.id === selectedId) ??
    ground.find((e) => e.mission_id === missionId) ??
    ground[0];
  async function observed(e: Evidence) {
    setSelectedId(e.id);
    const refreshed = await refresh();
    setNotice(
      !refreshed ? "Observation recorded. Reconnect to inspect the saved mission state." : e.consequence.relevant
        ? "Analysis recorded. Human review required."
        : "Evidence stored; no active mission dependency challenged.",
    );
  }
  async function verified() {
    const refreshed = await refresh();
    setNotice(
      refreshed ? "Review recorded. Check the mission state for its effect on knowledge and routing." : "Review recorded. Reconnect to inspect the saved decision.",
    );
  }
  function switchEva(id: string) {
    sessionStorage.setItem("marsense-mission", id);
    window.dispatchEvent(new Event("marsense-mission-change"));
    setSelectedId(null);
    setNotice("");
  }
  return (
    <MissionShell view={view} missionId={missionId} setMissionId={switchEva}>
      {error === "Authentication required" && !snapshot ? (
        <section className="panel access-gate" role="status">
          <p className="eyebrow">MISSION ACCESS</p><h1>Sign in to the living map</h1>
          <p>Mission records and observation controls require an authorized account. The public overview and NASA imagery remain available.</p>
          <Link href="/login" className="button primary">Open mission sign in</Link>
          <Link href="/" className="button secondary">Return to overview</Link>
        </section>
      ) : error && (
        <div role="alert" className="service-error">
          <div>
            <strong>
              {snapshot
                ? "Connection interrupted · last loaded state"
                : "Mission service unavailable"}
            </strong>
            <p>{error}</p>
          </div>
          <button className="button secondary" onClick={refresh}>
            <RefreshCw size={15} />
            Retry connection
          </button>
        </div>
      )}
      {!snapshot && error !== "Authentication required" && (
        <div className="loading-panel" role="status">
          <Database size={25} />
          <h2>
            {loading ? "Loading the living map…" : "Mission state unavailable"}
          </h2>
          <p>
            {loading
              ? "Reading mission state and the local NASA cache."
              : "Reconnect to load saved evidence. Its current state cannot be verified while disconnected."}
          </p>
        </div>
      )}
      {notice && (
        <div className="notice" role="status">
          {notice}
        </div>
      )}
      {snapshot && (
        <>
          {view === "mission" && (
            <MissionControl
              key={missionId}
              snapshot={snapshot}
              selected={selected}
              busy={busy || Boolean(error)}
              setBusy={setBusy}
              observed={observed}
              verified={verified}
              onSelect={setSelectedId}
              onFuture={() => switchEva("eva-02")}
            />
          )}
          {view === "astronaut" && (
            <AstronautWorkspace
              snapshot={snapshot}
              selected={selected}
              missionId={missionId}
              busy={busy || Boolean(error)}
              setBusy={setBusy}
              observed={observed}
              verified={verified}
            />
          )}
          {view === "evidence" && (
            <StructuredEvidence
              snapshot={snapshot}
              selected={selected}
              onSelect={setSelectedId}
              verified={verified}
            />
          )}
          {view === "memory" && (
            <SpatialMemory
              key={missionId}
              snapshot={snapshot}
              onFuture={() => switchEva("eva-02")}
            />
          )}
          {view === "comparison" && <BeforeAfter snapshot={snapshot} />}
        </>
      )}
    </MissionShell>
  );
}
