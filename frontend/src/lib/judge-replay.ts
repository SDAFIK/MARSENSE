/** Browser-only reproduction of the unregistered Jezero teaching scenario.
 * Matches backend/routing.py: 40 m, 31 × 21 cells, eight moves,
 * distance + 15% unknown-terrain cost, confirmed obstacle footprint
 * blocks the whole intersecting edge. No slope or safety claim.
 */
export type Point = [number, number];
export type Traverse = { coordinates: Point[]; distance: number; cost: number };
export const FOOTPRINT = { xmin: 520, ymin: 320, xmax: 680, ymax: 480 };
export const HABITAT: Point = [120, 400];
export const TARGET: Point = [1080, 400];
const CELL = 40, COLS = 31, ROWS = 21;
const moves: Point[] = [[1,0],[0,1],[0,-1],[-1,0],[1,1],[1,-1],[-1,1],[-1,-1]];
const round = (x: number) => Math.round(x * 100) / 100;
const key = (x: number,y: number) => y * COLS + x;
const xy = (id: number): Point => [id % COLS, Math.floor(id / COLS)];

/** Inclusive segment/rectangle clipping prevents diagonal corner cutting. */
export function intersectsFootprint(a: Point,b: Point): boolean {
  let lo=0, hi=1;
  for (const [origin,delta,min,max] of [
    [a[0],b[0]-a[0],FOOTPRINT.xmin,FOOTPRINT.xmax],
    [a[1],b[1]-a[1],FOOTPRINT.ymin,FOOTPRINT.ymax],
  ]) {
    if (delta===0) { if(origin<min || origin>max) return false; continue; }
    const t1=(min-origin)/delta,t2=(max-origin)/delta;
    lo=Math.max(lo,Math.min(t1,t2));hi=Math.min(hi,Math.max(t1,t2));
    if(lo>hi) return false;
  }
  return true;
}

export function calculateTraverse(confirmed: boolean, excluded?: [number,number]): Traverse {
  const source=key(HABITAT[0]/CELL,HABITAT[1]/CELL), target=key(TARGET[0]/CELL,TARGET[1]/CELL);
  const frontier=[{id:source,f:0}], costs=new Map<number,number>([[source,0]]), previous=new Map<number,number>();
  const visited=new Set<number>();
  while(frontier.length) {
    frontier.sort((a,b)=>b.f-a.f || xy(b.id)[0]-xy(a.id)[0] || xy(b.id)[1]-xy(a.id)[1]);
    const current=frontier.pop()!;
    if(visited.has(current.id)) continue;
    visited.add(current.id);
    if(current.id===target) {
      const chain=[target];while(chain[chain.length-1]!==source) chain.push(previous.get(chain[chain.length-1])!);
      const coordinates=chain.reverse().map(id=>xy(id).map(n=>n*CELL) as Point);
      const distance=coordinates.slice(1).reduce((sum,p,i)=>sum+Math.hypot(p[0]-coordinates[i][0],p[1]-coordinates[i][1]),0);
      return {coordinates,distance:round(distance),cost:round(costs.get(target)!)};
    }
    const [x,y]=xy(current.id);
    for(const [dx,dy] of moves) {
      const nx=x+dx,ny=y+dy;
      if(nx<0||nx>=COLS||ny<0||ny>=ROWS) continue;
      const next=key(nx,ny);
      if(excluded && ((excluded[0]===current.id&&excluded[1]===next)||(excluded[1]===current.id&&excluded[0]===next))) continue;
      if(confirmed&&intersectsFootprint([x*CELL,y*CELL],[nx*CELL,ny*CELL])) continue;
      const d=CELL*Math.hypot(dx,dy), candidate=costs.get(current.id)!+d*1.15;
      if(candidate<(costs.get(next)??Infinity)) {
        costs.set(next,candidate);previous.set(next,current.id);
        frontier.push({id:next,f:candidate+CELL*Math.hypot(nx-TARGET[0]/CELL,ny-TARGET[1]/CELL)});
      }
    }
  }
  return {coordinates:[],distance:0,cost:0};
}
export const ALPHA=calculateTraverse(false);
export const BETA=calculateTraverse(true);
export function calculateAlternatives(confirmed:boolean): Traverse[] {
  const primary=calculateTraverse(confirmed);if(!primary.coordinates.length) return [];
  const ids=primary.coordinates.map(([x,y])=>key(x/CELL,y/CELL));
  const indices=new Set(Array.from({length:6},(_,i)=>Math.round(i*(ids.length-2)/5)));
  const seen=new Set([JSON.stringify(primary.coordinates)]), alternatives:Traverse[]=[];
  for(const i of indices) {
    const route=calculateTraverse(confirmed,[ids[i],ids[i+1]]);
    const id=JSON.stringify(route.coordinates);
    if(route.coordinates.length&&!seen.has(id)) {seen.add(id);alternatives.push(route);}
  }
  return [primary,...alternatives.sort((a,b)=>a.cost-b.cost).slice(0,2)];
}
export type Decision = "none" | "pending" | "confirmed" | "rejected" | "more";
export type Replay = { stage: number; decision: Decision };
export type Action = "observe"|"analyze"|"review"|"confirm"|"reject"|"more"|"inherit"|"reset";
export const INITIAL: Replay = {stage:0,decision:"none"};
export function advance(state:Replay,action:Action): Replay {
  if(action==="reset") return INITIAL;
  if(action==="observe"&&state.stage===0) return {stage:1,decision:"none"};
  if(action==="analyze"&&(state.stage===1||state.decision==="more")) return {stage:2,decision:"pending"};
  if(action==="review"&&state.stage===2&&state.decision==="pending") return {stage:3,decision:"pending"};
  if(state.stage===3&&(state.decision==="pending"||state.decision==="more")) {
    if(action==="confirm") return {stage:4,decision:"confirmed"};
    if(action==="reject") return {stage:3,decision:"rejected"};
    if(action==="more") return {stage:3,decision:"more"};
  }
  if(action==="inherit"&&state.stage===4&&state.decision==="confirmed") return {stage:5,decision:"confirmed"};
  return state;
}
const STORAGE_KEY="marsense-browser-judge-v1";
const EMPTY=JSON.stringify(INITIAL);
let memory=EMPTY;
export function readReplay():string {
  if(typeof window==="undefined") return EMPTY;
  try {return sessionStorage.getItem(STORAGE_KEY)??memory;}catch{return memory;}
}
export function serverReplay():string {return EMPTY;}
export function subscribeReplay(callback:()=>void) {
  window.addEventListener("marsense-judge-change",callback);
  window.addEventListener("storage",callback);
  return ()=>{window.removeEventListener("marsense-judge-change",callback);window.removeEventListener("storage",callback);};
}
export function parseReplay(value:string):Replay {
  try {
    const data=JSON.parse(value) as Replay;
    if(data.stage===0&&data.decision==="none"||data.stage===1&&data.decision==="none"||
      data.stage===2&&data.decision==="pending"||data.stage===3&&["pending","more","rejected"].includes(data.decision)||
      (data.stage===4||data.stage===5)&&data.decision==="confirmed") return data;
  }catch{/* reset malformed local data */}
  return INITIAL;
}
export function writeReplay(action:Action) {
  memory=JSON.stringify(advance(parseReplay(readReplay()),action));
  try{sessionStorage.setItem(STORAGE_KEY,memory);}catch{/* private browsing can block storage; keep this tab's memory */}
  window.dispatchEvent(new Event("marsense-judge-change"));
}
