import { describe, expect, it } from "vitest";
import { centeredPlacement, defaultPlacement, placementRegion } from "@/components/footprint-picker";
import type { Region } from "@/lib/types";
const regions = [
  {id:"west", geometry:{coordinates:[[[0,0],[440,0],[440,800],[0,800],[0,0]]]}},
  {id:"middle", geometry:{coordinates:[[[440,0],[760,0],[760,800],[440,800],[440,0]]]}},
] as Region[];
describe("Manual footprint preview",()=>{
  it("centers and clamps the rectangle inside the selected region",()=>{
    const next=centeredPlacement(regions,[450,20],defaultPlacement)!;
    expect(next).toEqual({x:440,y:0,width:160,height:160});
    expect(placementRegion(regions,next)?.id).toBe("middle");
  });
  it("rejects crossings, invalid dimensions and outside clicks",()=>{
    expect(placementRegion(regions,{x:400,y:10,width:100,height:100})).toBeUndefined();
    expect(placementRegion(regions,{...defaultPlacement,width:NaN})).toBeUndefined();
    expect(centeredPlacement(regions,[1300,50],defaultPlacement)).toBeNull();
  });
});
