import Image from "next/image";
import type { ModelOutput } from "@/lib/types";

const classes = [
  ["soil", "#b98656"],
  ["bedrock", "#60abd7"],
  ["sand", "#f4cd7e"],
  ["large rocks", "#cf6b71"],
] as const;

export default function TerrainAnalysis({ output, replay = false }: { output: ModelOutput | null; replay?: boolean }) {
  const mask = output?.mask_reference;
  const safeMask = !replay && typeof mask === "string" && mask.length <= 140000 &&
    /^data:image\/png;base64,[A-Za-z0-9+/=]+$/.test(mask) ? mask : null;
  return <section className="terrain-analysis" aria-label="Terrain intelligence result">
    <div className="terrain-analysis-heading"><span className="eyebrow">TERRAIN INTELLIGENCE</span><h3>What the image supports</h3><p>Pixel predictions and human interpretation remain separate.</p></div>
    {safeMask ? <>
      <figure className="terrain-mask"><Image src={safeMask} width={256} height={256} unoptimized alt="Experimental terrain segmentation mask; gray pixels withheld by score"/><figcaption>Model-space mask · uncalibrated research evidence</figcaption></figure>
      <div className="terrain-class-legend" aria-label="Segmentation class colors">
        {classes.map(([name,color]) => <div key={name}><i style={{background:color}}/><span>{name}</span><strong>{typeof output?.class_fractions[name] === "number" ? (output.class_fractions[name] * 100).toFixed(1)+"%" : "—"}</strong></div>)}
        <div><i style={{background:"#5f6e7e"}}/><span>Withheld by score</span><strong>{typeof output?.features.pixel_abstention_fraction === "number" ? (output.features.pixel_abstention_fraction * 100).toFixed(1)+"%" : "—"}</strong></div>
      </div>
      <p className="small muted">Class fractions describe all raw predicted pixels; the gray mask shows a separate abstention screen. Neither is a calibrated probability of a hazard.</p>
    </> : <div className="terrain-analysis-empty"><strong>{replay ? "Curated demonstration — no segmentation" : "No reliable segmentation mask available"}</strong><p>{replay ? "This replay exercises the evidence and routing engine, not a live neural-network prediction." : "The recorded image remains available. Review the available image features and identify terrain manually if the model is unavailable or unvalidated."}</p></div>}
    <p className="terrain-review-note">Human review required. Image predictions cannot directly update map knowledge.</p>
  </section>;
}
