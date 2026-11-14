"use client";
import { useState } from "react";
import { Route } from "lucide-react";
import { api } from "@/lib/api";
import type { Coordinate, Snapshot } from "@/lib/types";
type Option = {coordinates: Coordinate[]; distance_m: number; cost: number; cost_breakdown: Record<string, number>};
export default function RouteOptions({snapshot}:{snapshot:Snapshot}) {
  const [options,setOptions]=useState<Option[]|null>(null);
  const [error,setError]=useState("");
  const [loading,setLoading]=useState(false);
  async function search() {
    setLoading(true); setError(""); setOptions(null);
    try {
      const result=await api<{active_route_id:string;options:Option[]}>(`/missions/${snapshot.mission.id}/alternatives`);
      if(result.active_route_id!==snapshot.mission.active_route_id) throw new Error("Mission changed. Refresh before comparing routes.");
      setOptions(result.options);
    } catch(e) {setError(e instanceof Error?e.message:"Route search unavailable");}
    finally {setLoading(false);}
  }
  return <section className="panel v3-route-options" aria-label="Modeled route options"><div className="panel-heading"><h2><Route size={17}/> Explore route options</h2><span className="eyebrow">READ-ONLY SEARCH</span></div>
    <div className="panel-body"><p>Compare distinct candidate traverses under the current confirmed terrain costs. This does not change the active route.</p>
      <button className="button secondary" disabled={loading} onClick={search}>{loading?"Calculating options…":"Calculate route options"}</button>
      {error&&<p role="alert">{error}</p>}
      {options&&<div className="v3-option-grid" role="status">{options.length===0?<p>No traversable path in the modeled grid.</p>:options.map((option,i)=><article key={i}><span className="eyebrow">{i===0?"Lowest modeled cost":`Alternative ${i}`}</span><h3>{option.distance_m.toFixed(0)} m</h3><svg viewBox="0 0 1200 800" aria-label="Local route schematic" role="img"><rect width="1200" height="800" fill="#13252b"/><polyline fill="none" stroke="#8ad8bc" strokeWidth="12" points={option.coordinates.map(([x,y])=>`${x},${800-y}`).join(" ")}/></svg><p>Modeled cost {option.cost.toFixed(1)}</p></article>)}</div>}
      <p className="small muted">Bounded search; candidates are not guaranteed globally ranked alternatives or certified safe routes.</p>
    </div></section>;
}
