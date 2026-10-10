import { ArrowRight, Route as RouteIcon } from "lucide-react";
import { label } from "@/lib/api";
import type { Snapshot } from "@/lib/types";
export default function RouteSummary({ snapshot }: { snapshot: Snapshot }) {
  const route = snapshot.routes.find(
    (r) => r.id === snapshot.mission.active_route_id,
  )!;
  const alpha = snapshot.routes[0];
  return (
    <section className="panel route-panel">
      <div className="panel-heading">
        <h2>
          <RouteIcon size={17} /> Traverse plan
        </h2>
        <span
          className={`badge ${route.status === "CHALLENGED" || route.status === "NO_ROUTE" ? "amber" : "green"}`}
        >
          {label(route.status)}
        </span>
      </div>
      <div className="panel-body">
        <div className="route-overview">
          <div>
            <span className="small-mono">ACTIVE TRAVERSE</span>
            <h3>{route.name}</h3>
          </div>
          <strong>
            {route.distance_m.toLocaleString(undefined, {
              maximumFractionDigits: 0,
            })}
            <small> m</small>
          </strong>
        </div>
        <div className="waypoints">
          <span>Habitat</span>
          <ArrowRight size={16} />
          <span>{snapshot.target.name}</span>
        </div>
        {route.version > 1 && (
          <div className="route-difference">
            <span>Route Alpha {alpha.distance_m.toFixed(0)} m</span>
            <ArrowRight size={14} />
            <strong>
              {route.name} {route.distance_m.toFixed(0)} m
            </strong>
          </div>
        )}
        <details open={route.version > 1}>
          <summary>Why this route?</summary>
          <p className="small consequence-copy">{route.explanation}</p>
          <dl className="cost-breakdown">
            {Object.entries(route.cost_breakdown).map(([key, value]) => (
              <div key={key}>
                <dt>{label(key)} cost</dt>
                <dd>{value.toFixed(1)}</dd>
              </div>
            ))}
          </dl>
          <p className="annotation-note">
            Model cost units · {snapshot.data_status.slope} · field assessment
            required
          </p>
        </details>
      </div>
    </section>
  );
}
