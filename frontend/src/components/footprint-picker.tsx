"use client";
import type { PointerEvent } from "react";
import type { Coordinate, Region, Snapshot } from "@/lib/types";
import { MapPin } from "lucide-react";

export type Placement = { x: number; y: number; width: number; height: number };
export const defaultPlacement: Placement = {x:520,y:320,width:160,height:160};

function extent(region: Region) {
  const ring = region.geometry.coordinates[0];
  return {left: Math.min(...ring.map(p=>p[0])), right: Math.max(...ring.map(p=>p[0])),
    bottom: Math.min(...ring.map(p=>p[1])), top: Math.max(...ring.map(p=>p[1]))};
}
export function placementRegion(regions: Region[], box: Placement) {
  if (!Object.values(box).every(Number.isFinite) || box.width <= 0 || box.height <= 0) return undefined;
  return regions.find(region=>{
    const r=extent(region);
    return box.x>=r.left && box.y>=r.bottom && box.x+box.width<=r.right && box.y+box.height<=r.top;
  });
}
export function centeredPlacement(regions: Region[], [x,y]: Coordinate, size: Placement): Placement | null {
  const region=regions.find(item=>{const r=extent(item);return x>=r.left&&x<=r.right&&y>=r.bottom&&y<=r.top;});
  if(!region) return null;
  const r=extent(region);
  const width=Math.max(1,Math.min(Number.isFinite(size.width)&&size.width>0?size.width:160,r.right-r.left));
  const height=Math.max(1,Math.min(Number.isFinite(size.height)&&size.height>0?size.height:160,r.top-r.bottom));
  return {width,height,x:Math.round(Math.max(r.left,Math.min(r.right-width,x-width/2))),
    y:Math.round(Math.max(r.bottom,Math.min(r.top-height,y-height/2)))};
}
export default function FootprintPicker({ snapshot, value, onChange, disabled }: {
  snapshot: Snapshot; value: Placement; onChange: (value: Placement)=>void; disabled: boolean;
}) {
  const region=placementRegion(snapshot.regions,value);
  const route=snapshot.routes.find(r=>r.id===snapshot.mission.active_route_id);
  const points=(coords:Coordinate[])=>coords.map(([x,y])=>x+","+ (800-y)).join(" ");
  function choose(event:PointerEvent<SVGSVGElement>) {
    if(disabled || !event.isPrimary) return;
    const transform=event.currentTarget.getScreenCTM();
    if(!transform) return;
    const point=new DOMPoint(event.clientX,event.clientY).matrixTransform(transform.inverse());
    const next=centeredPlacement(snapshot.regions,[point.x,800-point.y],value);
    if(next) onChange(next);
  }
  return <div className="footprint-picker">
    <div className="footprint-picker-heading"><MapPin size={18}/><div><strong>Place the observation</strong><p>Tap the local map or adjust the dimensions below.</p></div></div>
    <svg viewBox="0 0 1200 800" role="img" aria-label="Mission-local placement schematic with regions and active route" onPointerDown={choose} className="footprint-schematic">
      <rect width="1200" height="800" fill="#101e2a"/>
      {snapshot.regions.map(r=><polygon key={r.id} points={points(r.geometry.coordinates[0])} fill={r.id===region?.id?"#223e49":"#1a2c3b"} stroke="#66808b" strokeWidth="3"/>)}
      {Array.from({length:13},(_,i)=><path key={"x"+i} d={"M"+i*100+" 0 V800"} stroke="#385164" strokeWidth="1" opacity=".55"/>)}
      {Array.from({length:9},(_,i)=><path key={"y"+i} d={"M0 "+i*100+" H1200"} stroke="#385164" strokeWidth="1" opacity=".55"/>)}
      {route&&<polyline points={points(route.coordinates)} stroke="#e8eee9" strokeWidth="7" fill="none" strokeLinejoin="round"/>}
      <circle cx={snapshot.mission.habitat[0]} cy={800-snapshot.mission.habitat[1]} r="12" fill="#f4e9d2"/>
      <circle cx={snapshot.target.location[0]} cy={800-snapshot.target.location[1]} r="12" fill="#8fe5c9"/>
      {snapshot.regions.map(r=>{const b=extent(r);return <text key={r.id} x={(b.left+b.right)/2} y="65" textAnchor="middle" fontSize="31" fill="#d3e2ea">{r.name.split(" · ")[0]}</text>;})}
      {region&&<rect x={value.x} y={800-value.y-value.height} width={value.width} height={value.height} fill="#ffb275" fillOpacity=".3" stroke="#ffb275" strokeWidth="5" strokeDasharray="12 7"/>}
      <text x="30" y="755" fill="#c3d1db" fontSize="27">0–1,200 m east / 0–800 m north</text>
    </svg>
    <p className="small muted">Schematic uses the current mission geometry, not automatic image geolocation. The dashed box is your proposed supported footprint.</p>
    <div className="footprint-fields">{Object.entries(value).map(([key,number])=><label key={key}>{({x:"West offset (x)",y:"South offset (y)",width:"Width",height:"Height"} as Record<string,string>)[key]} · m<input type="number" min={key==="width"||key==="height"?1:0} max={key==="y"||key==="height"?800:1200} step="1" value={Number.isFinite(number)?number:""} disabled={disabled} onChange={e=>onChange({...value,[key]:e.target.value===""?NaN:Number(e.target.value)})}/></label>)}</div>
    <p className="placement-status" role="status">{region?region.name+" · proposed "+(value.width*value.height).toLocaleString()+" m²":"Choose a nonempty footprint within one mapped region."}</p>
  </div>;
}
