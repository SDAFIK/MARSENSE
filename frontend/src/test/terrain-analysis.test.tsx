import React from "react";
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import TerrainAnalysis from "@/components/terrain-analysis";
import type { ModelOutput } from "@/lib/types";

const output: ModelOutput = {
  terrain: "unknown", confidence: 0.25, confidence_label: "low",
  engine: "torchscript-ai4mars", version: "fixture",
  class_fractions: {soil: 1, bedrock: 0, sand: 0, "large rocks": 0},
  features: {pixel_abstention_fraction: 1}, limitations: ["Research only"],
  mask_reference: "data:image/png;base64,iVBORw0KGgo=",
};
describe("Terrain intelligence display", () => {
  it("discloses uncertain segmentation and human authority", () => {
    render(<TerrainAnalysis output={output}/>);
    expect(screen.getByRole("img", {name:/Experimental terrain segmentation mask/})).toBeInTheDocument();
    expect(screen.getByText("Withheld by score")).toBeInTheDocument();
    expect(screen.getByText(/Human review required/)).toBeInTheDocument();
  });
  it("never presents a replay or arbitrary URL as actual segmentation", () => {
    const {rerender}=render(<TerrainAnalysis output={output} replay/>);
    expect(screen.getByText("Curated demonstration — no segmentation")).toBeInTheDocument();
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
    rerender(<TerrainAnalysis output={{...output,mask_reference:"https://invalid.example/mask.png"}}/>);
    expect(screen.getByText("No reliable segmentation mask available")).toBeInTheDocument();
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });
});
