"use client";
import Image from "next/image";

import { useEffect, useRef, useState } from "react";
import { ArrowRight, Camera, ScanLine, Upload } from "lucide-react";
import { api, jsonRequest } from "@/lib/api";
import type { Evidence } from "@/lib/types";
export default function ObservationPanel({
  missionId,
  onComplete,
  busy,
  setBusy,
}: {
  missionId: string;
  onComplete: (e: Evidence) => Promise<void>;
  busy: boolean;
  setBusy: (busy: boolean) => void;
}) {
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<"demo" | "production" | "showcase" | null>(null);
  const [canReplay, setCanReplay] = useState(false);
  const [canUpload, setCanUpload] = useState(false);
  useEffect(() => {
    api<{ environment: "demo" | "production" | "showcase"; read_only: boolean; replay_enabled: boolean }>("/auth/session")
      .then((session) => {
        setMode(session.environment);
        setCanReplay(session.replay_enabled);
        setCanUpload(!session.read_only && session.environment !== "showcase");
      })
      .catch(() => setError("Unable to determine workspace permissions. Retry after reconnecting."));
  }, []);
  const [scenario, setScenario] = useState("obstacles");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [details, setDetails] = useState("");
  useEffect(() => () => {
    if (preview) URL.revokeObjectURL(preview);
  }, [preview]);
  const [bounds, setBounds] = useState({
    x: 520,
    y: 320,
    width: 160,
    height: 160,
  });
  const fileInput = useRef<HTMLInputElement>(null);
  function clearFile() {
    setFile(null);
    setPreview(null);
    if (fileInput.current) fileInput.current.value = "";
  }
  async function analyze() {
    if (file ? !canUpload : !canReplay) return;
    setBusy(true);
    setError(null);
    try {
      let evidence: Evidence;
      if (file) {
        const { x, y, width, height } = bounds;
        if (!Number.isFinite(x + y + width + height) || x < 0 || y < 0 ||
            width <= 0 || height <= 0 || x + width > 1200 || y + height > 800) {
          throw new Error("Enter a nonempty footprint within the 1,200 × 800 m mission area.");
        }
        const body = new FormData();
        body.append("details", details);
        body.append("file", file);
        body.append("mission_id", missionId);
        body.append(
          "footprint",
          JSON.stringify({
            type: "Polygon",
            coordinates: [
              [
                [x, y],
                [x + width, y],
                [x + width, y + height],
                [x, y + height],
                [x, y],
              ],
            ],
          }),
        );
        evidence = await api<Evidence>("/observations/upload", {
          method: "POST",
          body,
        });
      } else
        evidence = await api<Evidence>(
          "/observations/demo",
          jsonRequest({ mission_id: missionId, scenario }),
        );
      await onComplete(evidence);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Analysis failed. Your prior map is still available.",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="panel observation-panel">
      <div className="panel-heading">
        <h2>
          <Camera size={17} /> Ground observation
        </h2>
        <span className="small-mono">01 / OBSERVE</span>
      </div>
      <div className="observation-image">
        <Image
          unoptimized
          loading="eager"
          fill
          sizes="(max-width: 720px) 100vw, 800px"
          src={preview ?? "/api/assets/ground-navcam.jpg"}
          alt={preview ? "Selected ground image before submission" : "NASA Perseverance Navcam mosaic showing the Snowdrift Peak boulder field"}
        />
        <span>{preview ? "SELECTED IMAGE · NOT YET SAVED" : "PERSEVERANCE NAVCAM · SOL 866"}</span>
      </div>
      <div className="panel-body">
        <p className="small muted">A closer look can change the way forward.</p>
        {canReplay && <>
        <label className="field-label" htmlFor="scenario">
          Demonstration observation
        </label>
        <select
          id="scenario"
          value={scenario}
          onChange={(e) => {
            setScenario(e.target.value);
            clearFile();
          }}
          disabled={busy}
        >
          <option value="obstacles">Boulder field · on Route Alpha</option>
          <option value="match">Matching soil · no alert</option>
          <option value="minor">Minor difference · off route</option>
          <option value="weak">Uncertain roughness · review required</option>
          <option value="failure">Model unavailable · manual review</option>
          <option value="dynamic">Visibility · expires after 30 minutes</option>
        </select>
        </>}
        {mode === "production" && <p className="small muted">Production observations require a ground image. Curated replay is available in the isolated showcase.</p>}
        {canUpload && <>
        <button
          className="upload-button"
          disabled={busy}
          onClick={() => fileInput.current?.click()}
        >
          <Upload size={15} />
          {file ? file.name : "Or upload a ground image"}
          <span>JPG / PNG · 8 MB</span>
        </button>
        <input
          ref={fileInput}
          className="visually-hidden"
          type="file"
          accept="image/jpeg,image/png"
          aria-label="Upload ground image"
          onChange={(e) => {
            const next = e.target.files?.[0];
            if (next && (next.size > 8 * 1024 * 1024 || !["image/jpeg", "image/png"].includes(next.type))) {
              clearFile();
              setError("Choose a JPEG or PNG image no larger than 8 MB.");
              return;
            }
            setFile(next ?? null);
            setPreview(next ? URL.createObjectURL(next) : null);
            setError(null);
          }}
        />
        </>}
        {file && (
          <>
            <p className="small muted">
              Manually locate the supported footprint in local meters. Uploads
              are not automatically geolocated.
            </p>
            <div className="footprint-fields">
              {Object.entries(bounds).map(([key, value]) => (
                <label key={key}>
                  {key}
                  <input
                    type="number"
                    disabled={busy}
                    min="0"
                    max={key === "y" || key === "height" ? 800 : 1200}
                    value={value}
                    onChange={(e) =>
                      setBounds({ ...bounds, [key]: Number(e.target.value) })
                    }
                  />
                </label>
              ))}
            </div>
            <label className="field-label">
              Observation details (optional)
              <textarea rows={3} maxLength={500} value={details} disabled={busy}
                onChange={(e) => setDetails(e.target.value)}
                placeholder="Describe the conditions you actually observed." />
            </label>
            <button className="text-button" disabled={busy} onClick={clearFile}>
              {mode === "production" ? "Remove selected image" : "Use cached observation instead"}
            </button>
          </>
        )}
        {error && (
          <p role="alert" className="error-message">
            {error}
          </p>
        )}
        <button
          className="button primary full"
          onClick={analyze}
          disabled={busy || (file ? !canUpload : !canReplay)}
        >
          <ScanLine size={16} />
          {busy ? "Analyzing observation…" : "Analyze terrain"}
          <ArrowRight size={16} />
        </button>
        {busy && <div role="status" aria-live="polite"><div className="observation-progress" aria-hidden="true"><i/></div><p className="small muted">Submitting image or replay and recording analysis. Keep this page open.</p></div>}
        <p className="annotation-note">
          {file
            ? "Local image analysis · human review required"
            : mode === "production" ? "Upload an image to begin" : "Curated demo replay · simulated footprint"}
        </p>
      </div>
    </section>
  );
}
