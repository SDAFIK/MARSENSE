import { describe, expect, it } from "vitest";
import {
  challengedAlpha,
  missionFeatures,
  toMars,
} from "@/lib/mission-map-data";
import type { Snapshot } from "@/lib/types";
const snapshot = {
  routes: [
    {
      id: "eva-01-alpha",
      version: 1,
      status: "CHALLENGED",
      coordinates: [
        [120, 400],
        [440, 400],
        [600, 400],
        [760, 400],
        [1080, 400],
      ],
    },
    {
      id: "beta",
      version: 2,
      status: "ACTIVE",
      coordinates: [
        [120, 400],
        [440, 240],
        [760, 240],
        [1080, 400],
      ],
    },
  ],
  evidence: [
    {
      source_type: "demo_replay",
      verification_state: "PROVISIONAL",
      valid_until: null,
      spatial_footprint: {
        coordinates: [
          [
            [520, 320],
            [680, 320],
            [680, 480],
            [520, 320],
          ],
        ],
      },
      consequence: { route_segment_ids: ["eva-01-alpha-segment-3"] },
    },
  ],
} as unknown as Snapshot;
describe("Mission map presentation", () => {
  it("retains complete solid off-white Alpha and challenges only frozen segment 3", () => {
    const f = missionFeatures(snapshot, false, 0);
    expect(f.features[0].properties?.color).toBe("#f1eee6");
    expect(f.features[0].geometry).toEqual({
      type: "LineString",
      coordinates: snapshot.routes[0].coordinates.map(toMars),
    });
    expect(challengedAlpha(snapshot, 0)).toEqual([
      [440, 400],
      [600, 400],
      [760, 400],
    ]);
    expect(
      f.features.find((f) => f.properties?.kind === "challenge")?.geometry,
    ).toEqual({
      type: "LineString",
      coordinates: [
        [440, 400],
        [600, 400],
        [760, 400],
      ].map((p) => toMars(p as [number, number])),
    });
  });
  it("does not challenge from rejected, expired or superseded evidence", () => {
    for (const change of [
      { verification_state: "REJECTED" },
      { valid_until: "2020-01-01T00:00:00Z" },
      { superseded_by: ["replacement"] },
    ]) {
      expect(
        challengedAlpha(
          {
            ...snapshot,
            evidence: [{ ...snapshot.evidence[0], ...change }],
          } as Snapshot,
          Date.now(),
        ),
      ).toEqual([]);
    }
  });
  it("prior state excludes ground footprints, challenges and Beta", () => {
    const f = missionFeatures(snapshot, true, 0);
    expect(f.features).toHaveLength(1);
    expect(f.features[0].properties?.color).toBe("#f1eee6");
  });
  it("reveals only Beta progressively without truncating Alpha", () => {
    const early = missionFeatures(snapshot, false, 0, 0.25);
    expect(early.features[0].geometry).toEqual(
      missionFeatures(snapshot, false, 0).features[0].geometry,
    );
    expect(early.features[1].geometry).toEqual({
      type: "LineString",
      coordinates: snapshot.routes[1].coordinates.slice(0, 2).map(toMars),
    });
    expect(early.features[1].properties?.color).toBe("#8ad8bc");
  });
});
