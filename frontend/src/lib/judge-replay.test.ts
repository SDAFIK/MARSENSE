import {describe,expect,it} from "vitest";
import {advance,INITIAL,ALPHA,BETA,calculateAlternatives,intersectsFootprint,parseReplay} from "./judge-replay";
describe("cloud-independent judge simulation",()=>{
  it("matches the backend no-slope route distances and blocks the full supported obstacle",()=>{
    expect(ALPHA.distance).toBe(960);
    expect(BETA.distance).toBeCloseTo(1059.41,1);
    expect(ALPHA.coordinates.some((p,i)=>i>0&&intersectsFootprint(ALPHA.coordinates[i-1],p))).toBe(true);
    expect(BETA.coordinates.some((p,i)=>i>0&&intersectsFootprint(BETA.coordinates[i-1],p))).toBe(false);
    expect(BETA.coordinates[0]).toEqual([120,400]);expect(BETA.coordinates.at(-1)).toEqual([1080,400]);
  });
  it("requires human verification before learning and inheriting",()=>{
    expect(advance(INITIAL,"confirm")).toEqual(INITIAL);
    let state=advance(advance(advance(INITIAL,"observe"),"analyze"),"review");
    expect(state).toEqual({stage:3,decision:"pending"});
    expect(advance(state,"inherit")).toEqual(state);
    expect(advance(state,"reject")).toEqual({stage:3,decision:"rejected"});
    expect(advance(state,"more")).toEqual({stage:3,decision:"more"});
    state=advance(state,"confirm");expect(state).toEqual({stage:4,decision:"confirmed"});
    expect(advance(state,"inherit")).toEqual({stage:5,decision:"confirmed"});
    expect(advance(state,"reset")).toEqual(INITIAL);
  });
  it("calculates distinct alternatives without changing the primary route",()=>{
    const options=calculateAlternatives(true);expect(options.length).toBeGreaterThanOrEqual(2);
    expect(options[0]).toEqual(BETA);expect(new Set(options.map(o=>JSON.stringify(o.coordinates))).size).toBe(options.length);
    expect(options.every(o=>!o.coordinates.some((p,i)=>i>0&&intersectsFootprint(o.coordinates[i-1],p)))).toBe(true);
  });
  it("recovers safely from malformed or impossible browser state",()=>{
    expect(parseReplay("bad")).toEqual(INITIAL);expect(parseReplay('{"stage":5,"decision":"none"}')).toEqual(INITIAL);
  });
});
