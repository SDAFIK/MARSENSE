"use client";
import { useEffect, useRef, useState } from "react";
import maplibregl, { type GeoJSONSource } from "maplibre-gl";
import {
  toMars,
  missionFeatures as features,
  challengedAlpha,
} from "@/lib/mission-map-data";
import {
  Crosshair,
  Layers,
  Maximize2,
  Minimize2,
  Minus,
  Plus,
} from "lucide-react";
import type { Coordinate, Snapshot } from "@/lib/types";

function missionExtent(
  snapshot: Snapshot,
  warm: boolean,
): [Coordinate, Coordinate] {
  if (!warm) return [toMars([0, 0]), toMars([1200, 800])];
  const points = [
    snapshot.mission.habitat,
    snapshot.target.location,
    ...snapshot.routes.flatMap((r) => r.coordinates),
    ...snapshot.evidence
      .filter((e) => e.source_type !== "orbital")
      .flatMap((e) => e.spatial_footprint.coordinates.flat()),
  ];
  return [
    toMars([
      Math.min(...points.map((p) => p[0])),
      Math.min(...points.map((p) => p[1])) - 80,
    ]),
    toMars([
      Math.max(...points.map((p) => p[0])),
      Math.max(...points.map((p) => p[1])) + 80,
    ]),
  ];
}
async function orbitalDisplay(url: string, warm: boolean): Promise<string> {
  if (!warm) return url;
  const image = new window.Image();
  image.src = url;
  await image.decode();
  const canvas = document.createElement("canvas");
  canvas.width = image.naturalWidth;
  canvas.height = image.naturalHeight;
  const context = canvas.getContext("2d");
  if (!context) return url;
  // Display-only tint of genuine pixels; not a false-color scientific product.
  context.filter = "sepia(.9) saturate(2) hue-rotate(-15deg) brightness(1.12)";
  context.drawImage(image, 0, 0);
  return canvas.toDataURL("image/png");
}
function Fallback({
  snapshot,
  before,
  clock,
}: {
  snapshot: Snapshot;
  before: boolean;
  clock: number;
}) {
  return (
    <svg
      className="fallback-map"
      viewBox="0 0 1200 800"
      role="img"
      aria-label="Local metric mission map with habitat, science target, route and ground evidence footprints"
    >
      <image
        href="/api/assets/jezero-hirise.png"
        x="0"
        y="0"
        width="1200"
        height="800"
        opacity=".7"
      />
      {Array.from({ length: 13 }, (_, i) => (
        <line
          key={`x${i}`}
          x1={i * 100}
          x2={i * 100}
          y1={0}
          y2={800}
          stroke="#d1c2a4"
          opacity=".12"
        />
      ))}
      {Array.from({ length: 9 }, (_, i) => (
        <line
          key={`y${i}`}
          x1={0}
          x2={1200}
          y1={i * 100}
          y2={i * 100}
          stroke="#d1c2a4"
          opacity=".12"
        />
      ))}
      {!before &&
        snapshot.evidence
          .filter(
            (e) =>
              e.source_type !== "orbital" &&
              !e.superseded_by?.length &&
              e.verification_state !== "REJECTED" &&
              (!e.valid_until || Date.parse(e.valid_until) > clock),
          )
          .map((e) => (
            <polygon
              key={e.id}
              points={e.spatial_footprint.coordinates[0]
                .map(([x, y]) => `${x},${800 - y}`)
                .join(" ")}
              fill={
                e.verification_state === "CONFIRMED" ? "#8ad8bc33" : "#eba66f33"
              }
              stroke={
                e.verification_state === "CONFIRMED" ? "#8ad8bc" : "#eba66f"
              }
              strokeWidth="2"
            />
          ))}
      {snapshot.routes
        .filter((r) => !before || r.version === 1)
        .map((r) => (
          <polyline
            key={r.id}
            points={r.coordinates.map(([x, y]) => `${x},${800 - y}`).join(" ")}
            fill="none"
            stroke={r.version === 1 ? "#f1eee6" : "#8ad8bc"}
            strokeWidth="5"
          />
        ))}
      {!before && (
        <polyline
          points={challengedAlpha(snapshot, clock)
            .map(([x, y]) => `${x},${800 - y}`)
            .join(" ")}
          fill="none"
          stroke="#efb482"
          strokeWidth="6"
          strokeDasharray="10 8"
        />
      )}
      <circle cx="120" cy="400" r="10" fill="#e5ded3" />
      <text x="120" y="365" fill="white" textAnchor="middle" fontSize="22">
        Habitat
      </text>
      <rect x="1072" y="392" width="16" height="16" fill="#8ad8bc" />
      <text x="1060" y="365" fill="white" textAnchor="middle" fontSize="22">
        Delta outcrop
      </text>
    </svg>
  );
}
export default function LivingMap({
  snapshot,
  before = false,
  compact = false,
  focusLocation,
  warmPresentation = false,
  locked = false,
}: {
  snapshot: Snapshot;
  before?: boolean;
  compact?: boolean;
  focusLocation?: Coordinate;
  warmPresentation?: boolean;
  locked?: boolean;
}) {
  const container = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const [fallback, setFallback] = useState(false);
  const [layer, setLayer] = useState("hirise");
  const [ready, setReady] = useState(false);
  const [clock, setClock] = useState(() => Date.now());
  useEffect(() => {
    const timer = setInterval(() => setClock(Date.now()), 10000);
    return () => clearInterval(timer);
  }, []);
  const [expanded, setExpanded] = useState(false);
  const [showRoutes, setShowRoutes] = useState(true);
  const [showEvidence, setShowEvidence] = useState(true);
  const expandButton = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    if (!ready) return;
    const frame = requestAnimationFrame(() => {
      map.current?.resize();
      map.current?.fitBounds(missionExtent(snapshot, warmPresentation), {
        padding:
          compact && !expanded
            ? 30
            : { top: 90, bottom: 100, left: 35, right: 45 },
        duration: 0,
      });
    });
    return () => cancelAnimationFrame(frame);
  }, [expanded, ready, compact, snapshot, warmPresentation]);
  useEffect(() => {
    if (!expanded) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    function close(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setExpanded(false);
        expandButton.current?.focus();
      }
    }
    window.addEventListener("keydown", close);
    return () => {
      document.body.style.overflow = previous;
      window.removeEventListener("keydown", close);
    };
  }, [expanded]);
  useEffect(() => {
    if (!ready) return;
    for (const id of ["prior-route", "active-route", "challenged-segment"])
      map.current?.setLayoutProperty(
        id,
        "visibility",
        showRoutes ? "visible" : "none",
      );
    for (const id of ["footprints", "footprint-border"])
      map.current?.setLayoutProperty(
        id,
        "visibility",
        showEvidence ? "visible" : "none",
      );
  }, [ready, showRoutes, showEvidence]);
  const initial = useRef({ snapshot, before });
  useEffect(() => {
    initial.current = { snapshot, before };
  }, [snapshot, before]);
  useEffect(() => {
    if (!container.current) return;
    let instance: maplibregl.Map;
    try {
      const corners = initial.current.snapshot.data_status.manifest.hirise
        ?.render_corners as
        [Coordinate, Coordinate, Coordinate, Coordinate] | undefined;
      if (!corners) throw new Error("Cached imagery metadata is unavailable");
      instance = new maplibregl.Map({
        container: container.current,
        style: {
          version: 8,
          sources: {
            orbital: {
              type: "image",
              url: "/api/assets/jezero-hirise.png",
              coordinates: corners,
            },
            mission: {
              type: "geojson",
              data: features(initial.current.snapshot, initial.current.before),
            },
          },
          layers: [
            {
              id: "background",
              type: "background",
              paint: { "background-color": "#201f1c" },
            },
            {
              id: "orbital",
              type: "raster",
              source: "orbital",
              paint: {
                "raster-opacity": 1,
                "raster-saturation": 0,
                "raster-brightness-max": 1,
              },
            },
            {
              id: "footprints",
              type: "fill",
              source: "mission",
              filter: ["==", "kind", "footprint"],
              paint: { "fill-color": ["get", "color"], "fill-opacity": 0.2 },
            },
            {
              id: "footprint-border",
              type: "line",
              source: "mission",
              filter: ["==", "kind", "footprint"],
              paint: { "line-color": ["get", "color"], "line-width": 1.5 },
            },
            {
              id: "prior-route",
              type: "line",
              source: "mission",
              filter: ["all", ["==", "kind", "route"], ["==", "old", true]],
              paint: {
                "line-color": "#d8b084",
                "line-width": 2,
                "line-dasharray": [3, 3],
                "line-opacity": 0.7,
              },
            },
            {
              id: "active-route",
              type: "line",
              source: "mission",
              filter: ["all", ["==", "kind", "route"], ["==", "old", false]],
              paint: { "line-color": ["get", "color"], "line-width": 3 },
            },
            {
              id: "challenged-segment",
              type: "line",
              source: "mission",
              filter: ["==", "kind", "challenge"],
              paint: {
                "line-color": "#efb482",
                "line-width": 5,
                "line-dasharray": [2, 2],
              },
            },
          ],
        },
        center: toMars([600, 400]),
        zoom: 15,
        maxZoom: 20,
        minZoom: 13,
        attributionControl: false,
        interactive: !locked,
      });
      map.current = instance;
      instance.on("load", () => {
        instance.fitBounds(
          missionExtent(initial.current.snapshot, warmPresentation),
          {
            padding: compact ? 30 : 45,
            duration: 0,
          },
        );
        if (warmPresentation)
          void orbitalDisplay("/api/assets/jezero-hirise.png", true)
            .then((url) => {
              if (map.current === instance)
                (
                  instance.getSource("orbital") as maplibregl.ImageSource
                ).updateImage({ url, coordinates: corners });
            })
            .catch(() => {});
        setReady(true);
      });
      for (const [location, text, className] of [
        [initial.current.snapshot.mission.habitat, "Habitat", "habitat"],
        [initial.current.snapshot.target.location, "Delta outcrop", "target"],
        [
          initial.current.snapshot.astronaut.location,
          initial.current.snapshot.astronaut.name,
          "astronaut",
        ],
      ] as const) {
        const marker = document.createElement("div");
        marker.className = `map-marker ${className}`;
        const dot = document.createElement("span");
        const title = document.createElement("span");
        title.textContent = text;
        marker.setAttribute("aria-label", text);
        marker.append(dot, title);
        new maplibregl.Marker({
          element: marker,
          anchor: "top",
          offset: [0, -5.5],
        })
          .setLngLat(toMars(location))
          .addTo(instance);
      }
      const area = initial.current.snapshot.regions.find((r) =>
        r.name.startsWith("Area 14"),
      );
      if (area) {
        const ring = area.geometry.coordinates[0].slice(0, -1);
        const center: Coordinate = [
          ring.reduce((n, p) => n + p[0], 0) / ring.length,
          ring.reduce((n, p) => n + p[1], 0) / ring.length,
        ];
        const marker = document.createElement("div");
        marker.className = "map-marker area";
        const dot = document.createElement("span");
        const title = document.createElement("span");
        title.textContent = "Area 14";
        marker.setAttribute("aria-label", area.name);
        marker.append(dot, title);
        new maplibregl.Marker({
          element: marker,
          anchor: "top",
          offset: [0, -5.5],
        })
          .setLngLat(toMars(center))
          .addTo(instance);
      }
      instance.on("error", () => {
        setFallback(true);
      });
      const observer = new ResizeObserver(() => {
        instance.resize();
        instance.fitBounds(
          missionExtent(initial.current.snapshot, warmPresentation),
          {
            padding: compact
              ? 30
              : { top: 90, bottom: 100, left: 35, right: 45 },
            duration: 0,
          },
        );
      });
      observer.observe(container.current);
      return () => {
        observer.disconnect();
        instance.remove();
        map.current = null;
      };
    } catch {
      setFallback(true);
    }
  }, [compact, warmPresentation, locked, snapshot.mission.id]);
  const betaKey = snapshot.routes
    .filter((r) => r.version > 1)
    .map((r) => r.id)
    .join(",");
  const animatedBeta = useRef("");
  useEffect(() => {
    if (!ready) return;
    const source = map.current?.getSource("mission") as
      GeoJSONSource | undefined;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)");
    if (
      !betaKey ||
      before ||
      animatedBeta.current === betaKey ||
      reduced.matches
    ) {
      source?.setData(features(snapshot, before, clock));
      animatedBeta.current = betaKey;
      return;
    }
    animatedBeta.current = betaKey;
    let frame = 0;
    const started = performance.now();
    function reveal(now: number) {
      const progress = reduced.matches
        ? 1
        : Math.min(1, (now - started) / 1200);
      source?.setData(features(snapshot, before, clock, progress));
      if (progress < 1) frame = requestAnimationFrame(reveal);
    }
    frame = requestAnimationFrame(reveal);
    return () => cancelAnimationFrame(frame);
  }, [snapshot, before, ready, clock, betaKey]);
  useEffect(() => {
    if (!ready || !focusLocation || !map.current) return;
    const element = document.createElement("div");
    element.className = "map-marker event-location";
    element.setAttribute("aria-label", "Selected evidence location");
    const dot = document.createElement("span");
    const title = document.createElement("span");
    title.textContent = "Selected evidence";
    element.append(dot, title);
    const marker = new maplibregl.Marker({
      element,
      anchor: "top",
      offset: [0, -10],
    })
      .setLngLat(toMars(focusLocation))
      .addTo(map.current);
    return () => {
      marker.remove();
    };
  }, [ready, focusLocation]);
  async function changeLayer(value: string) {
    setLayer(value);
    const source = map.current?.getSource("orbital") as
      maplibregl.ImageSource | undefined;
    const metadata = snapshot.data_status.manifest[value as "ctx" | "hirise"];
    if (!metadata || metadata.render_corners.length !== 4) {
      setFallback(true);
      return;
    }
    source?.updateImage({
      url: await orbitalDisplay(
        `/api/assets/jezero-${value}.png`,
        warmPresentation,
      ),
      coordinates: metadata.render_corners as [
        Coordinate,
        Coordinate,
        Coordinate,
        Coordinate,
      ],
    });
  }
  return (
    <section
      className={`map-panel ${compact ? "compact" : ""} ${expanded ? "map-expanded" : ""}`}
      aria-label="Living Mars map"
    >
      <div className="map-toolbar">
        <span>
          <span className="status-dot" />
          {before ? "ORBITAL PRIOR" : "LIVING MAP"}
        </span>
        {!locked && (
          <button
            ref={expandButton}
            className="map-expand-button"
            aria-expanded={expanded}
            onClick={() => setExpanded(!expanded)}
          >
            {expanded ? <Minimize2 size={15} /> : <Maximize2 size={15} />}
            {expanded ? "Close full map" : "Open full map"}
          </button>
        )}
      </div>
      <div
        ref={container}
        className="map-canvas"
        role="region"
        aria-label="Interactive Jezero map"
      />
      {fallback && (
        <Fallback
          clock={clock}
          snapshot={{
            ...snapshot,
            routes: showRoutes ? snapshot.routes : [],
            evidence: showEvidence ? snapshot.evidence : [],
          }}
          before={before}
        />
      )}
      <div className="map-location">
        <span className="eyebrow">JEZERO OPERATIONAL AREA</span>
        <span>
          {before
            ? "Before EVA · NASA prior"
            : "Cached NASA imagery · illustrative mission"}
        </span>
      </div>
      {!fallback && !locked && (
        <div className="map-controls">
          <button
            aria-label="Zoom in"
            onClick={() =>
              map.current?.zoomIn({
                duration: window.matchMedia("(prefers-reduced-motion: reduce)")
                  .matches
                  ? 0
                  : 300,
              })
            }
          >
            <Plus size={18} />
          </button>
          <button
            aria-label="Zoom out"
            onClick={() =>
              map.current?.zoomOut({
                duration: window.matchMedia("(prefers-reduced-motion: reduce)")
                  .matches
                  ? 0
                  : 300,
              })
            }
          >
            <Minus size={18} />
          </button>
          <button
            aria-label="Fit mission extent"
            onClick={() =>
              map.current?.fitBounds(
                missionExtent(snapshot, warmPresentation),
                {
                  padding: 45,
                  duration: window.matchMedia(
                    "(prefers-reduced-motion: reduce)",
                  ).matches
                    ? 0
                    : 300,
                },
              )
            }
          >
            <Crosshair size={18} />
          </button>
        </div>
      )}
      {!locked && (
        <div className="map-layer">
          <Layers size={15} />
          <select
            aria-label="Orbital imagery layer"
            disabled={fallback}
            value={layer}
            onChange={(e) => changeLayer(e.target.value)}
          >
            <option value="hirise">HiRISE · controlled mosaic</option>
            <option value="ctx">CTX · local context crop</option>
          </select>
        </div>
      )}
      {!fallback && !locked && (
        <div className="map-overlay-switches" aria-label="Map overlays">
          <label>
            <input
              type="checkbox"
              checked={showRoutes}
              onChange={(e) => setShowRoutes(e.target.checked)}
            />{" "}
            Routes
          </label>
          {!before && (
            <label>
              <input
                type="checkbox"
                checked={showEvidence}
                onChange={(e) => setShowEvidence(e.target.checked)}
              />{" "}
              Evidence
            </label>
          )}
        </div>
      )}
      <div className="map-legend">
        <span>
          <i className="line alpha" /> Route Alpha
        </span>
        {!before && snapshot.routes.length > 1 && (
          <span>
            <i className="line beta" /> Route Beta
          </span>
        )}
        <span>
          <i className="square provisional" /> Provisional
        </span>
        <span>
          <i className="square verified" /> Ground observed
        </span>
      </div>
      <div className="map-attribution">
        NASA/JPL/Caltech · Mars Trek
        {warmPresentation ? " · warm display tint" : ""}
        {fallback ? " · WebGL unavailable; local metric diagram" : ""}
      </div>
    </section>
  );
}
