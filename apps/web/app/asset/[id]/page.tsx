"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft, MapPin, Clock, FileText, Eye,
  Tag, AlertCircle, FolderOpen
} from "lucide-react";
import { api, type AssetDetail } from "@/lib/api";
import { cn } from "@/lib/utils";

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatBytes(n: number | null): string {
  if (n == null) return "—";
  if (n < 1024) return `${n} B`;
  if (n < 1024 ** 2) return `${(n / 1024).toFixed(1)} KB`;
  if (n < 1024 ** 3) return `${(n / 1024 ** 2).toFixed(1)} MB`;
  return `${(n / 1024 ** 3).toFixed(2)} GB`;
}

function val(v: string | number | null | undefined): string {
  if (v == null || v === "") return "—";
  return String(v);
}

// ── Sub-components ────────────────────────────────────────────────────────────

function PanelLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-[9px] tracking-[0.2em] uppercase font-semibold text-[hsl(var(--muted))] px-4 pt-4 pb-1.5">
      {children}
    </p>
  );
}

function DataRow({ label, value, mono = false }: { label: string; value: React.ReactNode; mono?: boolean }) {
  return (
    <div className="flex items-baseline justify-between px-4 py-1 text-[11px]">
      <span className="text-[hsl(var(--muted-foreground))] shrink-0 min-w-[80px]">{label}</span>
      <span className={cn("text-[hsl(var(--foreground))] text-right break-all ml-2", mono && "font-mono text-[10px]")}>
        {value}
      </span>
    </div>
  );
}

function Chip({ label, dim }: { label: string; dim?: string }) {
  return (
    <div className="flex items-center gap-1 px-2 py-0.5 bg-[hsl(var(--surface-raised))] border border-[hsl(var(--border))] rounded-full text-[10px]">
      <span className="text-[hsl(var(--foreground))] font-medium">{label}</span>
      {dim && <span className="text-[hsl(var(--muted))]">{dim}</span>}
    </div>
  );
}

function Divider() {
  return <div className="border-t border-[hsl(var(--border-subtle))] mt-3" />;
}

// ── Asset Detail Page ─────────────────────────────────────────────────────────

export default function AssetDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [asset, setAsset] = useState<AssetDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [imgError, setImgError] = useState(false);

  useEffect(() => {
    if (!id) return;
    api.assets.detail(id)
      .then(setAsset)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return <div className="flex items-center justify-center h-full text-[11px] text-[hsl(var(--muted))]">Loading…</div>;
  }

  if (error || !asset) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-3">
        <AlertCircle size={20} className="text-red-400" />
        <p className="text-[12px] text-[hsl(var(--muted-foreground))]">{error ?? "Asset not found"}</p>
        <button onClick={() => router.back()} className="text-[11px] underline">Go back</button>
      </div>
    );
  }

  const thumbSrc = asset.large_thumbnail_url ?? asset.thumbnail_url ?? null;

  // Derive folder from path
  const pathParts = (asset.canonical_path ?? "").split("/");
  const folder = pathParts.slice(0, -1).join("/") || "/";

  const hasAI = asset.scene || (asset.objects?.length ?? 0) > 0 || (asset.place_candidates?.length ?? 0) > 0;

  return (
    <div className="h-full flex overflow-hidden">

      {/* ── Left: image ── */}
      <div className="flex-1 min-w-0 flex flex-col bg-[hsl(var(--surface))]">
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 px-4 py-3 border-b border-[hsl(var(--border-subtle))] shrink-0">
          <button
            onClick={() => router.back()}
            className="flex items-center gap-1.5 text-[11px] text-[hsl(var(--muted))] hover:text-[hsl(var(--foreground))] transition-colors"
          >
            <ArrowLeft size={12} /> Gallery
          </button>
          <span className="text-[hsl(var(--border))]">/</span>
          <span className="text-[11px] font-medium truncate">{asset.filename}</span>
        </div>

        {/* Full image viewer */}
        <div className="flex-1 min-h-0 flex items-center justify-center bg-[hsl(var(--surface))] relative overflow-hidden">
          {thumbSrc && !imgError ? (
            <img
              src={thumbSrc}
              alt={asset.filename}
              onError={() => setImgError(true)}
              className="w-full h-full object-contain"
            />
          ) : (
            <div className="flex flex-col items-center gap-3 text-[hsl(var(--muted))]">
              <Eye size={32} strokeWidth={1} />
              <p className="text-[11px]">No preview available</p>
            </div>
          )}
        </div>

        {/* File path bar */}
        <div className="shrink-0 px-4 py-2.5 border-t border-[hsl(var(--border-subtle))] bg-[hsl(var(--surface-raised))] flex items-center gap-2">
          <FolderOpen size={11} className="text-[hsl(var(--muted))] shrink-0" />
          <p
            className="text-[10px] font-mono text-[hsl(var(--muted-foreground))] truncate"
            title={asset.canonical_path}
          >
            {asset.canonical_path}
          </p>
        </div>
      </div>

      {/* ── Right: metadata panel ── */}
      <div className="w-64 shrink-0 border-l border-[hsl(var(--border))] overflow-y-auto bg-[hsl(var(--background))] text-[11px]">

        {/* File info — always visible at top */}
        <div className="px-4 pt-4 pb-3 border-b border-[hsl(var(--border-subtle))]">
          <p className="font-semibold text-[13px] truncate mb-0.5" title={asset.filename}>{asset.filename}</p>
          <p className="text-[10px] text-[hsl(var(--muted-foreground))] truncate" title={folder}>{folder}</p>
          <div className="flex gap-3 mt-2 text-[10px] text-[hsl(var(--muted-foreground))]">
            <span>{formatBytes(asset.file_size_bytes)}</span>
            {asset.media_info?.width && asset.media_info?.height && (
              <span>{asset.media_info.width} × {asset.media_info.height}</span>
            )}
            <span className="capitalize">{asset.type}</span>
          </div>
        </div>

        {/* AI Extraction */}
        {hasAI ? (
          <div className="border-b border-[hsl(var(--border-subtle))]">
            <PanelLabel>AI Extraction</PanelLabel>

            {asset.scene?.description && (
              <div className="px-4 pb-2">
                <p className="text-[11px] leading-relaxed text-[hsl(var(--foreground))] italic opacity-80">
                  "{asset.scene.description}"
                </p>
              </div>
            )}

            {asset.scene && (asset.scene.setting || asset.scene.time_of_day || asset.scene.weather) && (
              <div className="px-4 pb-1 flex flex-wrap gap-1">
                {asset.scene.setting && <Chip label={asset.scene.setting} />}
                {asset.scene.time_of_day && <Chip label={asset.scene.time_of_day} />}
                {asset.scene.weather && <Chip label={asset.scene.weather} />}
              </div>
            )}

            {(asset.objects?.length ?? 0) > 0 && (
              <div className="px-4 pt-2 pb-2">
                <p className="text-[9px] tracking-[0.15em] uppercase text-[hsl(var(--muted))] mb-1.5">Objects</p>
                <div className="flex flex-wrap gap-1">
                  {asset.objects.map((o, i) => (
                    <Chip key={i} label={o.label} dim={o.confidence != null ? `${Math.round(o.confidence * 100)}%` : undefined} />
                  ))}
                </div>
              </div>
            )}

            {(asset.place_candidates?.length ?? 0) > 0 && (
              <div className="px-4 pt-1 pb-2">
                <p className="text-[9px] tracking-[0.15em] uppercase text-[hsl(var(--muted))] mb-1">Places</p>
                {asset.place_candidates.map((p, i) => (
                  <div key={i} className="flex items-center gap-1.5 py-0.5">
                    <MapPin size={9} className="text-[hsl(var(--muted))] shrink-0" />
                    <span className="flex-1 truncate">{p.name ?? "Unknown"}</span>
                    {p.country && <span className="text-[hsl(var(--muted))] text-[10px]">{p.country}</span>}
                    {p.confidence != null && (
                      <span className="text-[9px] text-[hsl(var(--muted))]">{Math.round(p.confidence * 100)}%</span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div className="px-4 py-3 border-b border-[hsl(var(--border-subtle))]">
            <p className="text-[10px] text-[hsl(var(--muted-foreground))] italic">No AI extraction yet — run Jobs → AI extraction.</p>
          </div>
        )}

        {/* OCR */}
        {asset.ocr_text && (
          <div className="border-b border-[hsl(var(--border-subtle))]">
            <PanelLabel>OCR Text</PanelLabel>
            <div className="px-4 pb-3">
              <pre className="text-[10px] font-mono whitespace-pre-wrap break-words leading-relaxed bg-[hsl(var(--surface-raised))] p-2 rounded max-h-32 overflow-y-auto">
                {asset.ocr_text}
              </pre>
            </div>
          </div>
        )}

        {/* Date & Time */}
        <div className="border-b border-[hsl(var(--border-subtle))]">
          <PanelLabel>Date & Time</PanelLabel>
          <DataRow
            label="Captured"
            value={asset.temporal?.best_timestamp
              ? new Date(asset.temporal.best_timestamp).toLocaleString()
              : "—"}
          />
          <DataRow label="Source" value={val(asset.temporal?.source)} />
          {asset.temporal?.has_conflict && (
            <div className="px-4 py-1 flex items-center gap-1.5">
              <AlertCircle size={10} className="text-amber-500" />
              <span className="text-[10px] text-amber-500">Timestamp conflict</span>
            </div>
          )}
          <div className="pb-2" />
        </div>

        {/* Location */}
        {asset.location?.lat != null && (
          <div className="border-b border-[hsl(var(--border-subtle))]">
            <PanelLabel>Location</PanelLabel>
            <DataRow label="Lat" value={asset.location.lat.toFixed(5)} mono />
            <DataRow label="Lon" value={asset.location.lon?.toFixed(5) ?? "—"} mono />
            {asset.location.altitude != null && (
              <DataRow label="Alt" value={`${asset.location.altitude.toFixed(0)} m`} />
            )}
            <div className="px-4 pt-1 pb-3">
              <a
                href={`https://maps.google.com/?q=${asset.location.lat},${asset.location.lon}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-[10px] underline text-[hsl(var(--foreground))]"
              >
                Open in Maps →
              </a>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
