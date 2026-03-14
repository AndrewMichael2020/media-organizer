const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
export const API_BASE_URL = API_BASE;

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) throw new Error(`API ${path} → ${res.status}`);
  return res.json() as Promise<T>;
}

// ── Types ──────────────────────────────────────────────────────────────────

export interface AssetListItem {
  id: string;
  filename: string;
  type: "photo" | "video";
  date: string | null;
  has_ocr: boolean;
  has_gps: boolean;
  is_duplicate: boolean;
  thumbnail_url: string | null;
  width: number | null;
  height: number | null;
}

export interface AssetListResponse {
  items: AssetListItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface MediaInfo {
  width: number | null;
  height: number | null;
  duration_seconds: number | null;
  codec: string | null;
  color_space: string | null;
  camera_make: string | null;
  camera_model: string | null;
  lens_model: string | null;
  aperture: number | null;
  shutter_speed: string | null;
  iso: number | null;
  focal_length: number | null;
  flash: string | null;
  orientation: number | null;
  raw_exif: Record<string, unknown> | null;
}

export interface AssetDetail {
  id: string;
  filename: string;
  canonical_path: string;
  type: "photo" | "video";
  file_size_bytes: number | null;
  thumbnail_url: string | null;
  large_thumbnail_url: string | null;
  keyframe_urls: string[];
  temporal: { best_timestamp: string | null; source: string | null; has_conflict: boolean } | null;
  location: { lat: number | null; lon: number | null; altitude: number | null } | null;
  media_info: MediaInfo | null;
  ocr_text: string | null;
  scene: { setting: string | null; time_of_day: string | null; weather: string | null; description: string | null } | null;
  objects: { label: string; confidence: number | null; count: number | null }[];
  place_candidates: { name: string | null; country: string | null; region: string | null; place_type: string | null; confidence: number | null }[];
  extraction_status: string | null;
}

export interface JobOut {
  id: string;
  type: string;
  status: "queued" | "running" | "done" | "failed";
  started_at: string;
  finished_at: string | null;
  message: string | null;
  progress_current: number;
  progress_total: number;
}

export interface SourceRootInfo {
  path: string;
  exists: boolean;
  readable: boolean;
  file_count_estimate: number | null;
}

export interface ConfigSnapshot {
  source_roots: SourceRootInfo[];
  derivative_cache_root: string;
  model_provider: string;
  model_name: string;
  api_version: string;
}

export interface CostStats {
  total_runs: number;
  total_tokens_in: number;
  total_tokens_out: number;
  total_cost_usd: number;
  avg_cost_per_run_usd: number;
}



export const api = {
  assets: {
    list: (params?: { page?: number; page_size?: number; type?: string; q?: string }) => {
      const qs = new URLSearchParams();
      if (params?.page) qs.set("page", String(params.page));
      if (params?.page_size) qs.set("page_size", String(params.page_size));
      if (params?.type) qs.set("type", params.type);
      if (params?.q) qs.set("q", params.q);
      return apiFetch<AssetListResponse>(`/assets?${qs}`);
    },
    get: (id: string) => apiFetch<AssetListItem>(`/assets/${id}`),
    detail: (id: string) => apiFetch<AssetDetail>(`/assets/${id}/detail`),
  },

  jobs: {
    list: () => apiFetch<JobOut[]>("/jobs"),
    get: (id: string) => apiFetch<JobOut>(`/jobs/${id}`),
    startIngest: (body: { type: string; source_root?: string }) =>
      apiFetch<JobOut>("/jobs/ingest", { method: "POST", body: JSON.stringify(body) }),
    costStats: () => apiFetch<CostStats>("/jobs/extraction/cost-stats"),
  },

  config: {
    get: () => apiFetch<ConfigSnapshot>("/config"),
    validate: (path: string) =>
      apiFetch<SourceRootInfo>("/config/source-roots/validate", {
        method: "POST",
        body: JSON.stringify({ path }),
      }),
    pickFolder: () =>
      apiFetch<SourceRootInfo>("/config/pick-folder", { method: "POST", body: "{}" }),
    scan: (path: string) =>
      apiFetch<{ job_id: string; status: string; source_root: string }>(
        "/config/source-roots/scan",
        { method: "POST", body: JSON.stringify({ path }) }
      ),
  },

  health: () => apiFetch<{ status: string; db: string; version: string }>("/health"),
};
