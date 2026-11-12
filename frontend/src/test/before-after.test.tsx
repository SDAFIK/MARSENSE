import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import BeforeAfter from "@/components/before-after";
import type { Snapshot } from "@/lib/types";
vi.mock("@/components/living-map", () => ({
  default: ({
    before,
    locked,
    snapshot,
  }: {
    before?: boolean;
    locked: boolean;
    snapshot: Snapshot;
  }) => (
    <div
      data-testid={before ? "prior-map" : "after-map"}
      data-locked={String(locked)}
      data-mission={snapshot.mission.id}
    />
  ),
}));
vi.mock("@/components/route-summary", () => ({ default: () => null }));
const snapshot = {
  mission: { id: "eva-01", active_route_id: "eva-01-alpha" },
  evidence: [],
  routes: [{ id:"eva-01-alpha", mission_id:"eva-01", name:"Route Alpha", version:1, status:"ACTIVE", coordinates:[[120,400],[1080,400]], distance_m:960, cost:1104, cost_breakdown:{distance:960,uncertainty:144}, evidence_ids:[], explanation:"Illustrative orbital prior" }],
} as unknown as Snapshot;
describe("spatial before/after controls", () => {
  it("uses the same mission and locked extent for both map states", () => {
    render(<BeforeAfter snapshot={snapshot} />);
    expect(screen.getByRole("heading", { name: "Route Alpha" })).toBeVisible();
    expect(screen.getByText("Awaiting confirmed evidence")).toBeVisible();
    for (const name of ["prior-map", "after-map"]) {
      expect(screen.getByTestId(name)).toHaveAttribute("data-locked", "true");
      expect(screen.getByTestId(name)).toHaveAttribute(
        "data-mission",
        "eva-01",
      );
    }
  });
  it("provides accessible whole-state toggles and an adjustable split", () => {
    const { container } = render(<BeforeAfter snapshot={snapshot} />);
    const after = container.querySelector(".after-map") as HTMLElement;
    fireEvent.click(screen.getByRole("button", { name: "Before" }));
    expect(after.style.clipPath).toBe("inset(0 0 0 100%)");
    fireEvent.click(screen.getByRole("button", { name: "After" }));
    expect(after.style.clipPath).toBe("inset(0 0 0 0%)");
    fireEvent.change(
      screen.getByRole("slider", { name: "Before / After map slider" }),
      { target: { value: "35" } },
    );
    expect(after.style.clipPath).toBe("inset(0 0 0 35%)");
  });
});
