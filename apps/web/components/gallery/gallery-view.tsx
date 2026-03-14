"use client";

import { useState, useEffect, useCallback } from "react";
import { Search, SlidersHorizontal, LayoutGrid, List, RefreshCw, ZoomIn, ZoomOut } from "lucide-react";
import { cn } from "@/lib/utils";
import { api, type AssetListItem } from "@/lib/api";
import { AssetCard } from "./asset-card";
import { FilterBar } from "./filter-bar";

// Re-export type for AssetCard
export type { AssetListItem as AssetStub };

type ViewMode = "grid" | "list";

// columns-N class per zoom level (1=most zoomed in, 5=most zoomed out)
const ZOOM_COLS = [
  "columns-1",
  "columns-2",
  "sm:columns-2 md:columns-3",
  "columns-2 sm:columns-3 md:columns-4",
  "columns-2 sm:columns-3 md:columns-4 lg:columns-5",
] as const;
const DEFAULT_ZOOM = 2; // 3 columns on md+

export function GalleryView() {
  const [items, setItems] = useState<AssetListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [viewMode, setViewMode] = useState<ViewMode>("grid");
  const [filterOpen, setFilterOpen] = useState(false);
  const [typeFilter, setTypeFilter] = useState<string | undefined>();
  const [zoom, setZoom] = useState(DEFAULT_ZOOM);
  const [page] = useState(1);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.assets.list({ page, page_size: 96, q: query || undefined, type: typeFilter });
      setItems(res.items);
      setTotal(res.total);
    } catch (e) {
      setError("Could not reach API. Is the server running?");
    } finally {
      setLoading(false);
    }
  }, [page, query, typeFilter]);

  useEffect(() => { load(); }, [load]);

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center gap-3 px-5 py-2.5 border-b border-[hsl(var(--border-subtle))] bg-[hsl(var(--surface))] shrink-0">
        <div className="flex items-center gap-2 flex-1 max-w-sm bg-[hsl(var(--surface-raised))] border border-[hsl(var(--border))] rounded-md px-3 py-1.5">
          <Search size={12} className="text-[hsl(var(--muted))] shrink-0" />
          <input
            type="text"
            placeholder="Search by filename, tag, scene, OCR text…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="flex-1 text-[12px] bg-transparent outline-none placeholder:text-[hsl(var(--muted))] text-[hsl(var(--foreground))]"
          />
        </div>

        <button
          onClick={() => setFilterOpen((v) => !v)}
          className={cn(
            "flex items-center gap-1.5 text-[11px] px-2.5 py-1.5 rounded-md border transition-colors",
            filterOpen
              ? "bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))] border-transparent"
              : "border-[hsl(var(--border))] text-[hsl(var(--muted))] hover:text-[hsl(var(--foreground))] hover:bg-[hsl(var(--surface-raised))]"
          )}
        >
          <SlidersHorizontal size={11} />
          Filters
        </button>

        <div className="flex-1" />

        <button
          onClick={load}
          title="Refresh"
          className="text-[hsl(var(--muted))] hover:text-[hsl(var(--foreground))] transition-colors"
        >
          <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
        </button>

        <span className="text-[11px] text-[hsl(var(--muted))] tabular-nums">
          {total.toLocaleString()} assets
        </span>

        {/* Zoom control */}
        {viewMode === "grid" && (
          <div className="flex items-center gap-1.5">
            <button
              onClick={() => setZoom((z) => Math.max(0, z - 1))}
              disabled={zoom === 0}
              className="text-[hsl(var(--muted))] hover:text-[hsl(var(--foreground))] disabled:opacity-30 transition-colors"
              title="Zoom in"
            >
              <ZoomIn size={13} />
            </button>
            <input
              type="range"
              min={0}
              max={ZOOM_COLS.length - 1}
              value={zoom}
              onChange={(e) => setZoom(Number(e.target.value))}
              className="w-16 accent-[hsl(var(--foreground))] cursor-pointer"
              title="Gallery zoom"
              style={{ direction: "rtl" }}
            />
            <button
              onClick={() => setZoom((z) => Math.min(ZOOM_COLS.length - 1, z + 1))}
              disabled={zoom === ZOOM_COLS.length - 1}
              className="text-[hsl(var(--muted))] hover:text-[hsl(var(--foreground))] disabled:opacity-30 transition-colors"
              title="Zoom out"
            >
              <ZoomOut size={13} />
            </button>
          </div>
        )}

        <div className="flex border border-[hsl(var(--border))] rounded-md overflow-hidden">
          {(["grid", "list"] as ViewMode[]).map((mode) => (
            <button
              key={mode}
              onClick={() => setViewMode(mode)}
              className={cn(
                "p-1.5 transition-colors",
                viewMode === mode
                  ? "bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]"
                  : "text-[hsl(var(--muted))] hover:text-[hsl(var(--foreground))] hover:bg-[hsl(var(--surface-raised))]"
              )}
            >
              {mode === "grid" ? <LayoutGrid size={13} /> : <List size={13} />}
            </button>
          ))}
        </div>
      </div>

      {filterOpen && (
        <FilterBar
          typeFilter={typeFilter}
          onTypeChange={setTypeFilter}
        />
      )}

      <div className="flex-1 overflow-auto p-4">
        {error ? (
          <div className="flex flex-col items-center justify-center h-full gap-3">
            <p className="text-[11px] tracking-[0.15em] uppercase font-medium text-red-500">Connection Error</p>
            <p className="text-[12px] text-[hsl(var(--muted-foreground))] max-w-xs text-center">{error}</p>
            <button onClick={load} className="text-[11px] text-[hsl(var(--muted))] hover:text-[hsl(var(--foreground))] underline">Retry</button>
          </div>
        ) : loading ? (
          <div className="flex items-center justify-center h-full">
            <span className="text-[11px] text-[hsl(var(--muted))]">Loading…</span>
          </div>
        ) : items.length === 0 ? (
          <EmptyGallery />
        ) : viewMode === "grid" ? (
          <div className={cn("gap-2 space-y-2", ZOOM_COLS[zoom])}>
            {items.map((asset) => (
              <AssetCard key={asset.id} asset={asset} compact={zoom >= 3} />
            ))}
          </div>
        ) : (
          <ListView assets={items} />
        )}
      </div>
    </div>
  );
}

function EmptyGallery() {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-4 text-center px-8">
      <p className="text-[11px] tracking-[0.2em] uppercase font-medium text-[hsl(var(--muted))]">No Assets</p>
      <p className="text-[12px] text-[hsl(var(--muted-foreground))] max-w-sm leading-relaxed">
        Configure a source root in <code className="font-mono text-[11px] bg-[hsl(var(--surface-raised))] px-1 py-0.5 rounded">config/local.yaml</code> and start a scan from Settings → Jobs.
      </p>
    </div>
  );
}

function ListView({ assets }: { assets: AssetListItem[] }) {
  return (
    <table className="w-full text-[12px]">
      <thead className="sticky top-0 bg-[hsl(var(--surface))]">
        <tr className="border-b border-[hsl(var(--border-subtle))]">
          {["Filename", "Type", "Date", "Dims", "Flags"].map((h) => (
            <th key={h} className="text-left px-3 py-2 text-[10px] tracking-[0.15em] uppercase font-medium text-[hsl(var(--muted))]">{h}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {assets.map((asset) => (
          <tr key={asset.id} className="border-b border-[hsl(var(--border-subtle))] hover:bg-[hsl(var(--surface-raised))] transition-colors cursor-pointer">
            <td className="px-3 py-2.5 font-mono text-[11px]">{asset.filename}</td>
            <td className="px-3 py-2.5 text-[hsl(var(--muted))] uppercase text-[10px] tracking-wider">{asset.type}</td>
            <td className="px-3 py-2.5 text-[hsl(var(--muted))] font-mono text-[11px]">{asset.date ?? "—"}</td>
            <td className="px-3 py-2.5 text-[hsl(var(--muted))] font-mono text-[11px]">
              {asset.width && asset.height ? `${asset.width}×${asset.height}` : "—"}
            </td>
            <td className="px-3 py-2.5">
              <div className="flex gap-1">
                {asset.has_ocr && <Flag label="OCR" color="blue" />}
                {asset.has_gps && <Flag label="GPS" color="green" />}
                {asset.is_duplicate && <Flag label="DUP" color="amber" />}
                {asset.type === "video" && <Flag label="VID" color="purple" />}
              </div>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function Flag({ label, color }: { label: string; color: "blue" | "green" | "amber" | "purple" }) {
  const styles = {
    blue:   "bg-blue-50 text-blue-600 dark:bg-blue-950 dark:text-blue-400",
    green:  "bg-emerald-50 text-emerald-600 dark:bg-emerald-950 dark:text-emerald-400",
    amber:  "bg-amber-50 text-amber-600 dark:bg-amber-950 dark:text-amber-400",
    purple: "bg-violet-50 text-violet-600 dark:bg-violet-950 dark:text-violet-400",
  };
  return (
    <span className={`text-[9px] font-medium uppercase tracking-wider px-1 py-0.5 rounded ${styles[color]}`}>
      {label}
    </span>
  );
}
