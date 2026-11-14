"use client";
import { useEffect, useRef, useState } from "react";
import { RotateCcw, RotateCw, Play, Pause } from "lucide-react";

export default function MarsGlobe() {
  const canvas = useRef<HTMLCanvasElement>(null);
  const draw = useRef<((angle: number) => void) | null>(null);
  const angle = useRef(0);
  const dragX = useRef<number | null>(null);
  const [playing, setPlaying] = useState(false);
  const [status, setStatus] = useState("Loading planetary texture");
  useEffect(() => {
    const image = new window.Image();
    let active = true;
    image.onload = () => {
      if (!active || !canvas.current) return;
      const ctx = canvas.current.getContext("2d");
      const texture = document.createElement("canvas");
      texture.width = 1024; texture.height = 512;
      const source = texture.getContext("2d");
      if (!ctx || !source) { setStatus("Globe unavailable"); return; }
      source.drawImage(image, 0, 0, 1024, 512);
      const pixels = source.getImageData(0, 0, 1024, 512).data;
      const n = 256, frame = ctx.createImageData(n, n);
      const longitude = new Float32Array(n*n), latitude = new Int16Array(n*n), light = new Float32Array(n*n);
      for (let y=0;y<n;y++) for(let x=0;x<n;x++) {
        const i=y*n+x, px=(x+0.5-n/2)/(n/2-4), py=(n/2-y-0.5)/(n/2-4), r=px*px+py*py;
        if (r>1) continue;
        const z=Math.sqrt(1-r);
        longitude[i]=Math.atan2(px,z)/(2*Math.PI)+0.5;
        latitude[i]=Math.min(511,Math.max(0,Math.floor((0.5-Math.asin(py)/Math.PI)*512)));
        light[i]=Math.max(0.38,0.82*z-0.32*px+0.16*py+0.32);
        frame.data[i*4+3]=255;
      }
      draw.current=(turn)=>{
        for(let i=0;i<n*n;i++) {
          if (!frame.data[i*4+3]) continue;
          const u=((longitude[i]+turn)%1+1)%1, j=(latitude[i]*1024+Math.floor(u*1024))*4;
          for(let c=0;c<3;c++) frame.data[i*4+c]=pixels[j+c]*light[i];
        }
        ctx.putImageData(frame,0,0);
      };
      draw.current(angle.current); setStatus("Planetary context ready");
    };
    image.onerror=()=>{ if(active) setStatus("Texture unavailable"); };
    image.src="/assets/mars-viking.jpg";
    return ()=>{active=false;draw.current=null;};
  },[]);
  useEffect(()=>{
    if(!playing) return;
    let timer=0, previous=0;
    const tick=(now:number)=>{
      if(!document.hidden && previous && now-previous>=32) {
        angle.current=(angle.current+Math.min(now-previous,100)/18000)%1;
        draw.current?.(angle.current); previous=now;
      } else if(!previous || document.hidden) previous=now;
      timer=requestAnimationFrame(tick);
    };
    timer=requestAnimationFrame(tick);
    return ()=>cancelAnimationFrame(timer);
  },[playing]);
  const rotate=(direction:number)=>{angle.current=(angle.current+direction/12+1)%1;draw.current?.(angle.current);};
  return <section className="panel intel-globe"><div className="panel-heading"><h2>Planetary context / Mars</h2><span className="small muted">Viking imagery</span></div><div className="globe-stage"><canvas ref={canvas} width={256} height={256} role="img" aria-label="Mars globe rendered from NASA Viking imagery" onPointerDown={(event) => { if (!event.isPrimary) return; setPlaying(false); dragX.current = event.clientX; event.currentTarget.setPointerCapture(event.pointerId); }} onPointerMove={(event) => { if (dragX.current === null || !event.isPrimary) return; angle.current = (angle.current - (event.clientX - dragX.current) / 420 + 1) % 1; dragX.current = event.clientX; draw.current?.(angle.current); }} onPointerUp={() => { dragX.current = null; }} onPointerCancel={() => { dragX.current = null; }} onLostPointerCapture={() => { dragX.current = null; }}/></div><div className="globe-controls"><button className="button secondary" onClick={()=>rotate(-1)} aria-label="Rotate Mars left"><RotateCcw size={16}/></button><button className="button secondary" onClick={()=>setPlaying(v=>!v)} aria-label={playing?"Pause Mars rotation":"Play Mars rotation"}>{playing?<Pause size={16}/>:<Play size={16}/>}</button><button className="button secondary" onClick={()=>rotate(1)} aria-label="Rotate Mars right"><RotateCw size={16}/></button></div><div className="panel-body"><p className="small muted" role="status">{status}</p><p className="small muted">Drag the globe to explore, or use the rotation controls.</p><p className="small muted">NASA/JPL-Caltech · Viking imagery / USGS. Illustrative globe, not live orbital telemetry.</p><a className="small" href="https://science.nasa.gov/3d-resources/mars/">NASA source ↗</a></div></section>;
}
