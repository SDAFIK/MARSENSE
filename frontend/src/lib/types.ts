export type Coordinate = [number, number];
export type Terrain =
  | "soil"
  | "sand"
  | "bedrock"
  | "large rocks"
  | "rough terrain"
  | "obstacle-rich terrain"
  | "unknown";
export type Verification =
  "PROVISIONAL" | "CONFIRMED" | "REJECTED" | "NEEDS_MORE_EVIDENCE";
export type Footprint = { type: "Polygon"; coordinates: Coordinate[][] };
export type ModelOutput = {
  terrain: Terrain;
  confidence: number;
  confidence_label: string;
  engine: string;
  version: string;
  class_fractions: Record<string, number>;
  features: Record<string, number>;
  limitations: string[];
};
export type Evidence = {
  superseded_by?: string[];
  id: string;
  region_id: string;
  observation_id: string | null;
  mission_id: string;
  source: string;
  source_type: "orbital" | "ground" | "demo_replay";
  timestamp: string;
  location: Coordinate;
  spatial_footprint: Footprint;
  observation_type: string;
  observed_value: Terrain;
  expected_value: Terrain;
  model_output: ModelOutput | null;
  model_confidence: number | null;
  verification_state: Verification;
  persistence_type: "persistent" | "dynamic";
  valid_until: string | null;
  raw_asset_reference: string;
  discrepancy: string;
  consequence: {
    relevant: boolean;
    safety_critical: boolean;
    alert: string | null;
    assumption_ids: string[];
    route_segment_ids: string[];
    target_ids: string[];
    explanation: string;
  };
  verified_by: string | null;
  verified_at: string | null;
  verification_note: string | null;
};
export type Region = {
  id: string;
  name: string;
  geometry: Footprint;
  prior_interpretation: Terrain;
  current_interpretation: string;
  knowledge_state: string;
  evidence_history: string[];
  updated_at: string;
};
export type Route = {
  id: string;
  mission_id: string;
  name: string;
  version: number;
  status: "ACTIVE" | "CHALLENGED" | "SUPERSEDED" | "NO_ROUTE";
  coordinates: Coordinate[];
  distance_m: number;
  cost: number;
  cost_breakdown: Record<string, number>;
  evidence_ids: string[];
  explanation: string;
};
export type Snapshot = {
  mission: {
    id: string;
    name: string;
    eva: string;
    astronaut_id: string;
    habitat: Coordinate;
    target_id: string;
    active_route_id: string;
    inherited_evidence: string[];
  };
  astronaut: {
    id: string;
    name: string;
    location: Coordinate;
    authority: string;
  };
  target: {
    id: string;
    name: string;
    location: Coordinate;
    objective: string;
    source_note: string;
  };
  regions: Region[];
  evidence: Evidence[];
  routes: Route[];
  assumptions: {
    id: string;
    statement: string;
    status: string;
    supporting_evidence: string[];
    challenging_evidence: string[];
  }[];
  events: {
    id: string;
    timestamp: string;
    kind: string;
    title: string;
    detail: string;
    evidence_id: string | null;
  }[];
  data_status: {
    mode: string;
    terrain_prior: string;
    slope: string;
    model: string;
    manifest: {
      crism?: {
        available: boolean; reason?: string; product_id?: string; resolution_m?: number;
        preview?: string; limitations?: string[]; channels?: string[];
        source?: {url: string; sha256: string};
        target?: {valid_pixel: boolean; source_pixel: number[]; mineral_identity: null};
      } | null;
      cameras?: {
        product_id: string; version_id: string; instrument: string[];
        sol: number; sclk: string; preview: string; source_url: string;
        raw_sha256: string; limitations: string[]; clock_interval_matched: boolean;
        observation_clock_matched: boolean; region_overlap: boolean;
      }[];
      ctx?: { render_corners: Coordinate[]; layer: string; sha256: string };
      hirise?: { render_corners: Coordinate[]; layer: string; sha256: string };
      ground?: {
        product: string;
        source_page: string;
        credit: string;
        processing: string;
        registration: string;
      };
      cached_at?: string;
    };
  };
};
export type View =
  "mission" | "astronaut" | "evidence" | "memory" | "comparison";
