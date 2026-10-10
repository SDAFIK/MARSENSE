"use client";
import Link from "next/link";
import {
  ArrowUpRight,
  Columns2,
  Footprints,
  History,
  Map,
  Orbit,
  Radio,
  ScanLine,
} from "lucide-react";
import type { View } from "@/lib/types";
import AuthPanel from "./auth-panel";
const links = [
  { view: "mission", label: "Mission Control", icon: Map },
  { view: "astronaut", label: "Astronaut View", icon: Footprints },
  { view: "evidence", label: "Evidence Inspector", icon: ScanLine },
  { view: "memory", label: "Exploration Memory", icon: History },
  { view: "comparison", label: "Before & After", icon: Columns2 },
] as const;
export default function MissionShell({
  view,
  missionId,
  setMissionId,
  children,
}: {
  view: View;
  missionId: string;
  setMissionId: (id: string) => void;
  children: React.ReactNode;
}) {
  return (
    <div className={`app-shell view-${view}`}>
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>
      <header className="app-header">
        <Link className="wordmark" href="/">
          <Orbit size={24} />
          MARSENSE
          <span className="brand-divider" />
          <span className="small-mono">MISSION CONTROL</span>
        </Link>
        <div className="header-right">
          <label className="eva-select">
            <span className="small-mono">ACTIVE MISSION</span>
            <select
              aria-label="Active mission"
              value={missionId}
              onChange={(event) => {
                setMissionId(event.target.value);
                sessionStorage.setItem("marsense-mission", event.target.value);
              }}
            >
              <option value="eva-01">EVA 01 · A. Rahman</option>
              <option value="eva-02">EVA 02 · S. Chen · Future EVA</option>
            </select>
          </label>

          <span className="cache-indicator">
            <span className="status-dot" /> LOCAL DATA CACHE
          </span>
          <AuthPanel compact />
        </div>
      </header>
      <aside className="sidebar">
        <div className="sidebar-project">
          <span className="eyebrow">EXPLORATION WORKSPACE</span>
          <strong>Jezero reconnaissance</strong>
          <span className="small muted">Mars · 18.44° N, 77.45° E</span>
        </div>
        <nav aria-label="Main navigation">
          {links.map(({ view: v, label, icon: Icon }) => (
            <Link
              key={v}
              href={`/${v}`}
              className={`nav-link ${view === v ? "active" : ""}`}
              aria-current={view === v ? "page" : undefined}
            >
              <Icon size={18} />
              <span className="nav-label">{label}</span>
              {view === v && <span className="nav-active-dot" />}
            </Link>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <Radio size={20} />
          <strong>Every EVA leaves a trace.</strong>
          <p>
            Verified evidence stays with the map, ready for the next explorer.
          </p>
          <Link href="/memory">
            Explore mission memory <ArrowUpRight size={14} />
          </Link>
          <div className="small-mono">MARSENSE / v1.0</div>
        </div>
      </aside>
      <main id="main-content" className="workspace">
        {view !== "mission" && (
          <div className="workspace-heading">
            <div>
              <p className="eyebrow">JEZERO CRATER / SURFACE OPERATIONS</p>
              <h1>{links.find((l) => l.view === view)?.label}</h1>
              <p className="muted">
                {view === "memory"
                  ? "What one explorer discovers, the next explorer inherits."
                  : view === "comparison"
                    ? "See exactly how ground evidence changes the mission."
                    : view === "evidence"
                      ? "Inspect the observation, interpretation, and decision separately."
                      : "Your observation. Your judgment. A better map for the next EVA."}
              </p>
            </div>
            {
              <Link href="/mission" className="button secondary">
                <Map size={16} /> Open living map
              </Link>
            }
          </div>
        )}
        {children}
        <footer className="workspace-footer">
          <span>NASA-derived imagery · Illustrative mission geometry</span>
          <span>Decision support · Field assessment required</span>
        </footer>
      </main>
    </div>
  );
}
