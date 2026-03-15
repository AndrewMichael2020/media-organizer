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
  captured_at: string | null;
  folder_path: string | null;
  lat: number | null;
  lon: number | null;
  has_ocr: boolean;
  has_gps: boolean;
  is_duplicate: boolean;
  thumbnail_url: string | null;
  width: number | null;
  height: number | null;
  scene_label: string | null;
  place_label: string | null;
  object_labels: string[];
  tags: string[];
  summary: string | null;
  extraction_status: string | null;
  confidence_label: string | null;
  review_bucket: string | null;
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
  temporal: {
    best_timestamp: string | null;
    source: string | null;
    confidence: string | null;
    has_conflict: boolean;
    exif_datetime: string | null;
    gps_datetime: string | null;
    filesystem_mtime: string | null;
    video_creation_time: string | null;
  } | null;
  location: { lat: number | null; lon: number | null; altitude: number | null } | null;
  media_info: MediaInfo | null;
  ocr_text: string | null;
  scene: { setting: string | null; time_of_day: string | null; weather: string | null; description: string | null; confidence: number | null } | null;
  objects: { label: string; confidence: number | null; count: number | null; color: string | null; details: string[] }[];
  place_candidates: { name: string | null; country: string | null; region: string | null; place_type: string | null; confidence: number | null; source: string | null }[];
  summary: string | null;
  tags: string[];
  tag_details: { label: string; confidence: number | null }[];
  artistic_notes: {
    summary: string | null;
    composition: string | null;
    lighting: string | null;
    detail: string | null;
    resolution: string | null;
  } | null;
  extraction_notes: string | null;
  analysis: Record<string, unknown> | null;
  user_context: {
    place: string | null;
    gps_coords: string | null;
    comments: string | null;
  } | null;
  location_meta: {
    place_name_candidate: string | null;
    nearest_city_candidate: string | null;
    province_or_state_candidate: string | null;
    country_candidate: string | null;
    location_source: string;
    location_precision: string;
    location_confidence: string;
    location_evidence: string[];
  } | null;
  series: {
    label: string;
    count: number;
    items: { id: string; filename: string; captured_at: string | null }[];
  } | null;
  extraction_status: string | null;
  extraction_run: {
    id: string;
    model_provider: string | null;
    model_name: string | null;
    prompt_version: string | null;
    schema_version: string | null;
    status: string;
    started_at: string | null;
    finished_at: string | null;
    tokens_in: number | null;
    tokens_out: number | null;
    cost_usd: number | null;
    error_message: string | null;
    debug_stage: string | null;
    debug_excerpt: string | null;
  } | null;
}

export interface JobOut {
  id: string;
  type: string;
  status: "queued" | "running" | "done" | "failed" | "cancelled";
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
  lmstudio_base_url: string;
  default_model_profile_key: string;
  model_profiles: {
    key: string;
    label: string;
    provider: string;
    model_name: string;
    kind: string;
    execution_mode: "standard" | "batch";
    image_max_px: number | null;
  }[];
  api_version: string;
}

export interface PurgeMetadataResponse {
  status: string;
  tables_reset: boolean;
  cache_root: string;
  cache_cleared: boolean;
  debug_cleared: boolean;
}

export interface CostStats {
  total_runs: number;
  total_tokens_in: number;
  total_tokens_out: number;
  total_cost_usd: number;
  avg_cost_per_run_usd: number;
}

export interface ReviewQueue {
  name: string;
  label: string;
  description: string;
  count: number;
  items: AssetListItem[];
}

export interface ReviewQueueResponse {
  queues: ReviewQueue[];
}

export interface FolderItem {
  path: string;
  count: number;
}

export interface FolderResponse {
  items: FolderItem[];
}



export const api = {
  assets: {
    list: (params?: {
      page?: number;
      page_size?: number;
      type?: string;
      q?: string;
      ai_text?: string;
      scene?: string;
      place?: string;
      object?: string;
      match?: "any" | "all";
      folder?: string;
      has_ocr?: boolean;
      has_gps?: boolean;
      has_ai?: boolean;
      review_bucket?: string;
    }) => {
      const qs = new URLSearchParams();
      if (params?.page) qs.set("page", String(params.page));
      if (params?.page_size) qs.set("page_size", String(params.page_size));
      if (params?.type) qs.set("type", params.type);
      if (params?.q) qs.set("q", params.q);
      if (params?.ai_text) qs.set("ai_text", params.ai_text);
      if (params?.scene) qs.set("scene", params.scene);
      if (params?.place) qs.set("place", params.place);
      if (params?.object) qs.set("object", params.object);
      if (params?.match) qs.set("match", params.match);
      if (params?.folder) qs.set("folder", params.folder);
      if (params?.has_ocr) qs.set("has_ocr", "true");
      if (params?.has_gps) qs.set("has_gps", "true");
      if (params?.has_ai) qs.set("has_ai", "true");
      if (params?.review_bucket) qs.set("review_bucket", params.review_bucket);
      return apiFetch<AssetListResponse>(`/assets?${qs}`);
    },
    get: (id: string) => apiFetch<AssetListItem>(`/assets/${id}`),
    detail: (id: string) => apiFetch<AssetDetail>(`/assets/${id}/detail`),
    updateUserContext: (id: string, body: { place?: string | null; gps_coords?: string | null; comments?: string | null }) =>
      apiFetch<{ place: string | null; gps_coords: string | null; comments: string | null }>(`/assets/${id}/user-context`, {
        method: "POST",
        body: JSON.stringify(body),
      }),
    reviewQueues: () => apiFetch<ReviewQueueResponse>("/assets/review/queues"),
    resetMetadata: (folder_path: string) =>
      apiFetch<{ folder_path: string; asset_count: number }>("/assets/reset-metadata", {
        method: "POST",
        body: JSON.stringify({ folder_path }),
      }),
    folders: (params?: {
      type?: string;
      q?: string;
      ai_text?: string;
      scene?: string;
      place?: string;
      object?: string;
      match?: "any" | "all";
      folder?: string;
      has_ocr?: boolean;
      has_gps?: boolean;
      has_ai?: boolean;
      review_bucket?: string;
    }) => {
      const qs = new URLSearchParams();
      if (params?.type) qs.set("type", params.type);
      if (params?.q) qs.set("q", params.q);
      if (params?.ai_text) qs.set("ai_text", params.ai_text);
      if (params?.scene) qs.set("scene", params.scene);
      if (params?.place) qs.set("place", params.place);
      if (params?.object) qs.set("object", params.object);
      if (params?.match) qs.set("match", params.match);
      if (params?.folder) qs.set("folder", params.folder);
      if (params?.has_ocr) qs.set("has_ocr", "true");
      if (params?.has_gps) qs.set("has_gps", "true");
      if (params?.has_ai) qs.set("has_ai", "true");
      if (params?.review_bucket) qs.set("review_bucket", params.review_bucket);
      return apiFetch<FolderResponse>(`/assets/folders?${qs}`);
    },
  },

  jobs: {
    list: () => apiFetch<JobOut[]>("/jobs"),
    get: (id: string) => apiFetch<JobOut>(`/jobs/${id}`),
    startIngest: (body: { type: string; source_root?: string; asset_ids?: string[]; model_provider?: string; model_name?: string; execution_mode?: "standard" | "batch" }) =>
      apiFetch<JobOut>("/jobs/ingest", { method: "POST", body: JSON.stringify(body) }),
    stop: (id: string) => apiFetch<JobOut>(`/jobs/${id}/stop`, { method: "POST" }),
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
    purgeMetadata: (confirm_text: string) =>
      apiFetch<PurgeMetadataResponse>("/config/purge-metadata", {
        method: "POST",
        body: JSON.stringify({ confirm_text }),
      }),
  },

  health: () => apiFetch<{ status: string; db: string; version: string }>("/health"),
};
