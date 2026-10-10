import React from "react";
import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import EvidenceReview from "@/components/evidence-review";
import type { Evidence } from "@/lib/types";
vi.mock("@/lib/api", () => ({
  api: vi.fn(),
  jsonRequest: vi.fn(),
  label: (v: string) => v.toLowerCase().replaceAll("_", " "),
}));
const evidence: Evidence = {
  id: "ev-1",
  region_id: "corridor",
  observation_id: "obs-1",
  mission_id: "eva-01",
  source: "NASA replay",
  source_type: "demo_replay",
  timestamp: "2026-10-10T00:00:00Z",
  location: [600, 400],
  spatial_footprint: {
    type: "Polygon",
    coordinates: [
      [
        [520, 320],
        [680, 320],
        [680, 480],
        [520, 480],
        [520, 320],
      ],
    ],
  },
  observation_type: "terrain",
  observed_value: "rough terrain",
  expected_value: "soil",
  model_output: {
    terrain: "rough terrain",
    confidence: 0.3,
    confidence_label: "low",
    engine: "cv-fallback",
    version: "1",
    class_fractions: {},
    features: {},
    limitations: ["Human review required"],
  },
  model_confidence: 0.3,
  verification_state: "PROVISIONAL",
  persistence_type: "persistent",
  valid_until: null,
  raw_asset_reference: "/api/assets/ground-navcam.jpg",
  discrepancy: "INSUFFICIENT_EVIDENCE",
  consequence: {
    relevant: true,
    safety_critical: true,
    alert: "PROVISIONAL SAFETY ALERT",
    assumption_ids: [],
    route_segment_ids: [],
    target_ids: [],
    explanation: "Intersects route",
  },
  verified_by: null,
  verified_at: null,
  verification_note: null,
};
describe("human verification guard", () => {
  it("weak inference alerts but cannot be confirmed without human identification", () => {
    render(
      <EvidenceReview
        evidence={evidence}
        reviewer="Astronaut"
        onVerified={async () => {}}
      />,
    );
    expect(
      screen.getByRole("button", { name: "Confirm observation" }),
    ).toBeDisabled();
    expect(screen.getByText("PROVISIONAL SAFETY ALERT")).toBeInTheDocument();
    expect(
      screen.getByLabelText("Human terrain identification"),
    ).toBeInTheDocument();
  });
  it("strong replay annotation is still provisional until human confirmation", () => {
    render(
      <EvidenceReview
        evidence={{ ...evidence, model_confidence: 0.9 }}
        reviewer="Astronaut"
        onVerified={async () => {}}
      />,
    );
    expect(
      screen.getByRole("button", { name: "Confirm observation" }),
    ).toBeEnabled();
  });
  it("final evidence shows reviewer and removes confirmation action", () => {
    render(
      <EvidenceReview
        evidence={{
          ...evidence,
          verification_state: "CONFIRMED",
          verified_by: "A. Rahman",
        }}
        reviewer="Astronaut"
        onVerified={async () => {}}
      />,
    );
    expect(
      screen.queryByRole("button", { name: "Confirm observation" }),
    ).not.toBeInTheDocument();
    expect(screen.getByText("Confirmed by A. Rahman")).toBeInTheDocument();
  });
});
