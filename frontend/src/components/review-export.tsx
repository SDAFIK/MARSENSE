"use client";
import { useState } from "react";
import { Download } from "lucide-react";
import { api } from "@/lib/api";
import type { Evidence, Snapshot } from "@/lib/types";

export function eligibleReview(e: Evidence) {
  return e.source_type === "ground" && e.verification_state === "CONFIRMED" &&
    e.persistence_type === "persistent" && !e.superseded_by?.length &&
    Boolean(e.observation_id && e.verified_at && e.verified_by) && e.observed_value !== "unknown";
}
export default function ReviewExport({snapshot}:{snapshot:Snapshot}) {
  const records=snapshot.evidence.filter(eligibleReview);
  const [busy,setBusy]=useState(false);
  const [message,setMessage]=useState("");
  async function download() {
    setBusy(true);setMessage("");
    try {
      const entries=await Promise.all(records.map(async e=>{
        const observation=await api<{asset_sha256:string;model_input_sha256:string;original_asset_reference?:string|null}>(`/observations/${e.observation_id}`);
        return {evidence_id:e.id,observation_id:e.observation_id,mission_id:e.mission_id,terrain:e.observed_value,
          verified_at:e.verified_at,footprint:e.spatial_footprint,asset_sha256:observation.asset_sha256,
          model_input_sha256:observation.model_input_sha256};
      }));
      const blob=new Blob([JSON.stringify({schema:"marsense-reviewed-observations-v1",scope:"Private research manifest; image-level human interpretations, not pixel segmentation labels",records:entries},null,2)],{type:"application/json"});
      const url=URL.createObjectURL(blob);
      const a=document.createElement("a");a.href=url;a.download="marsense-reviewed-observations.json";a.click();
      setTimeout(()=>URL.revokeObjectURL(url),1000);
      setMessage("Research manifest downloaded. No data was shared or used for training.");
    } catch(e){setMessage(e instanceof Error?e.message:"Export unavailable");}
    finally{setBusy(false);}
  }
  return <section className="panel v3-review-export"><div className="panel-body"><h3>Reviewed research evidence</h3><p className="small muted">{records.length} eligible real ground records. Export only confirmed, persistent, non-superseded human interpretations. Replay data and image bytes are excluded. No automatic training or external sharing.</p>
  <button className="button secondary" disabled={busy||!records.length} onClick={download}><Download size={16}/> {busy?"Preparing manifest…":"Download reviewed evidence"}</button>{message&&<p role="status">{message}</p>}</div></section>;
}
