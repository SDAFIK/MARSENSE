"use client";
import Image from "next/image";

import { useRef, useState } from "react";
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
  const [scenario, setScenario] = useState("obstacles");
  const [error, setError] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [bounds, setBounds] = useState({
    x: 520,
    y: 320,
    width: 160,
    height: 160,
  });
  const fileInput = useRef<HTMLInputElement>(null);
  async function analyze() {
    setBusy(true);
    setError(null);
    try {
      let evidence: Evidence;
      if (file) {
        const { x, y, width, height } = bounds;
        const body = new FormData();
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
          src="/api/assets/ground-navcam.jpg"
          alt="NASA Perseverance Navcam mosaic showing the Snowdrift Peak boulder field"
        />
        <span>PERSEVERANCE NAVCAM · SOL 866</span>
      </div>
      <div className="panel-body">
        <p className="small muted">A closer look can change the way forward.</p>
        <label className="field-label" htmlFor="scenario">
          Demonstration observation
        </label>
        <select
          id="scenario"
          value={scenario}
          onChange={(e) => {
            setScenario(e.target.value);
            setFile(null);
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
            if (next && next.size > 8 * 1024 * 1024) {
              setError("Image exceeds 8 MB. Choose a smaller image.");
              return;
            }
            setFile(next ?? null);
            setError(null);
          }}
        />
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
            <button className="text-button" onClick={() => setFile(null)}>
              Use cached observation instead
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
          disabled={busy}
        >
          <ScanLine size={16} />
          {busy ? "Analyzing observation…" : "Analyze terrain"}
          <ArrowRight size={16} />
        </button>
        <p className="annotation-note">
          {file
            ? "Local image analysis · human review required"
            : "Curated demo replay · simulated footprint"}
        </p>
      </div>
    </section>
  );
}
