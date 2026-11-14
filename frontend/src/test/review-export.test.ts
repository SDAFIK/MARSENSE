import { describe, expect, it } from "vitest";
import { eligibleReview } from "@/components/review-export";
import type { Evidence } from "@/lib/types";
const verified={source_type:"ground",verification_state:"CONFIRMED",persistence_type:"persistent",
  observation_id:"obs",verified_at:"2026-11-14",verified_by:"Reviewer",observed_value:"soil"} as Evidence;
describe("Research export eligibility",()=>{
  it("accepts only reviewed current real observations",()=>{
    expect(eligibleReview(verified)).toBe(true);
    expect(eligibleReview({...verified,source_type:"demo_replay"})).toBe(false);
    expect(eligibleReview({...verified,verification_state:"PROVISIONAL"})).toBe(false);
    expect(eligibleReview({...verified,persistence_type:"dynamic"})).toBe(false);
    expect(eligibleReview({...verified,superseded_by:["next"]})).toBe(false);
  });
});
