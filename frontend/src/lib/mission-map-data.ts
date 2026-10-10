import type { Coordinate, Snapshot } from "./types";
import type { FeatureCollection } from "geojson";

export function toMars([x, y]: Coordinate): Coordinate {
  return [
    77.45 +
      ((x / (3396190 * Math.cos((18.44 * Math.PI) / 180))) * 180) / Math.PI,
    18.44 + ((y / 3396190) * 180) / Math.PI,
  ];
}
// Frozen demonstration segment 3 bounds, from backend/seed.py. Presentation only;
// consequences and route calculation remain authoritative on the backend.
export function challengedAlpha(
  snapshot: Snapshot,
  clock: number,
): Coordinate[] {
  const alpha = snapshot.routes.find((r) => r.version === 1);
  if (
    !alpha ||
    !snapshot.evidence.some(
      (e) =>
        e.consequence.route_segment_ids.includes(`${alpha.id}-segment-3`) &&
        e.verification_state !== "REJECTED" &&
        !e.superseded_by?.length &&
        (!e.valid_until || Date.parse(e.valid_until) > clock),
    )
  )
    return [];
  return alpha.coordinates.filter(([x]) => x >= 440 && x <= 760);
}
export function missionFeatures(
  snapshot: Snapshot,
  before: boolean,
  clock = Date.now(),
  betaProgress = 1,
): FeatureCollection {
  const result: FeatureCollection = { type: "FeatureCollection", features: [] };
  for (const r of snapshot.routes.filter((r) => !before || r.version === 1)) {
    if (r.coordinates.length < 2) continue;
    const coordinates =
      r.version > 1
        ? r.coordinates.slice(
            0,
            Math.max(2, Math.ceil(r.coordinates.length * betaProgress)),
          )
        : r.coordinates;
    result.features.push({
      type: "Feature",
      properties: {
        kind: "route",
        color: r.version === 1 ? "#f1eee6" : "#8ad8bc",
        old: false,
      },
      geometry: { type: "LineString", coordinates: coordinates.map(toMars) },
    });
  }
  if (!before) {
    const challenged = challengedAlpha(snapshot, clock);
    if (challenged.length >= 2)
      result.features.push({
        type: "Feature",
        properties: { kind: "challenge", color: "#efb482" },
        geometry: { type: "LineString", coordinates: challenged.map(toMars) },
      });
    for (const e of snapshot.evidence.filter(
      (e) =>
        e.source_type !== "orbital" &&
        !e.superseded_by?.length &&
        e.verification_state !== "REJECTED" &&
        (!e.valid_until || Date.parse(e.valid_until) > clock),
    ))
      result.features.push({
        type: "Feature",
        properties: {
          kind: "footprint",
          color: e.verification_state === "CONFIRMED" ? "#8ad8bc" : "#eba66f",
        },
        geometry: {
          type: "Polygon",
          coordinates: e.spatial_footprint.coordinates.map((ring) =>
            ring.map(toMars),
          ),
        },
      });
  }
  return result;
}
