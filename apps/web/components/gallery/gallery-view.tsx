"use client";

import Link from "next/link";
import { startTransition, useCallback, useDeferredValue, useEffect, useState } from "react";
import { ArrowLeft, FolderTree, LayoutGrid, List, RefreshCw, Search, SlidersHorizontal, ZoomIn, ZoomOut } from "lucide-react";
import { cn } from "@/lib/utils";
import { api, type AssetListItem, type FolderItem } from "@/lib/api";
import { AssetCard } from "./asset-card";
import { FilterBar } from "./filter-bar";

export type { AssetListItem as AssetStub };

type ViewMode = "grid" | "list";

const ZOOM_COLS = [
  "columns-1",
  "columns-2",
  "sm:columns-2 md:columns-3",
  "columns-2 sm:columns-3 md:columns-4",
  "columns-2 sm:columns-3 md:columns-4 lg:columns-5",
] as const;

const DEFAULT_ZOOM = 2;

export function GalleryView() {
  const [items, setItems] = useState<AssetListItem[]>([]);
  const [folders, setFolders] = useState<FolderItem[]>([]);
  const [allFolders, setAllFolders] = useState<FolderItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const deferredQuery = useDeferredValue(query);
  const [aiTextFilter, setAiTextFilter] = useState("");
  const deferredAiTextFilter = useDeferredValue(aiTextFilter);
  const [sceneFilter, setSceneFilter] = useState("");
  const [placeFilter, setPlaceFilter] = useState("");
  const [objectFilter, setObjectFilter] = useState("");
  const [viewMode, setViewMode] = useState<ViewMode>("grid");
  const [filterOpen, setFilterOpen] = useState(true);
  const [typeFilter, setTypeFilter] = useState<string | undefined>();
  const [hasOcr, setHasOcr] = useState(false);
  const [hasGps, setHasGps] = useState(false);
  const [hasAi, setHasAi] = useState(false);
  const [reviewBucket, setReviewBucket] = useState<string | undefined>();
  const [folderFilter, setFolderFilter] = useState<string | undefined>();
  const [zoom, setZoom] = useState(DEFAULT_ZOOM);

  const load = useCallback(async (mode: "initial" | "refresh" = "initial") => {
    if (mode === "refresh") {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError(null);
    try {
      const [assetRes, folderRes, allFolderRes] = await Promise.all([
        api.assets.list({
          page: 1,
          page_size: 96,
          q: deferredQuery || undefined,
          ai_text: deferredAiTextFilter || undefined,
          scene: sceneFilter || undefined,
          place: placeFilter || undefined,
          object: objectFilter || undefined,
          type: typeFilter,
          folder: folderFilter,
          has_ocr: hasOcr || undefined,
          has_gps: hasGps || undefined,
          has_ai: hasAi || undefined,
          review_bucket: reviewBucket,
        }),
        api.assets.folders({
          q: deferredQuery || undefined,
          ai_text: deferredAiTextFilter || undefined,
          scene: sceneFilter || undefined,
          place: placeFilter || undefined,
          object: objectFilter || undefined,
          type: typeFilter,
          folder: folderFilter,
          has_ocr: hasOcr || undefined,
          has_gps: hasGps || undefined,
          has_ai: hasAi || undefined,
          review_bucket: reviewBucket,
        }),
        api.assets.folders({
          type: typeFilter,
        }),
      ]);
      setItems(assetRes.items);
      setTotal(assetRes.total);
      setFolders(folderRes.items);
      setAllFolders(allFolderRes.items);
    } catch {
      setError("Could not reach the local API. Start the app stack and try again.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [deferredAiTextFilter, deferredQuery, hasAi, hasGps, hasOcr, objectFilter, placeFilter, reviewBucket, sceneFilter, typeFilter, folderFilter]);

  function resetFilters() {
    setQuery("");
    setAiTextFilter("");
    setSceneFilter("");
    setPlaceFilter("");
    setObjectFilter("");
    setTypeFilter(undefined);
    setHasOcr(false);
    setHasGps(false);
    setHasAi(false);
    setReviewBucket(undefined);
    setFolderFilter(undefined);
  }

  useEffect(() => {
    load();
  }, [load]);

  const topTags = findTopTags(items);
  const activeFilterCount = [
    query,
    aiTextFilter,
    sceneFilter,
    placeFilter,
    objectFilter,
    typeFilter,
    hasOcr ? "ocr" : "",
    hasGps ? "gps" : "",
    hasAi ? "ai" : "",
    reviewBucket,
    folderFilter,
  ].filter(Boolean).length;

  return (
    <div className="flex h-full flex-col">
      <section className="border-b border-[hsl(var(--border-subtle))] bg-[linear-gradient(135deg,rgba(103,77,41,0.08),transparent_45%),linear-gradient(180deg,rgba(255,248,238,0.9),rgba(255,255,255,0.72))] px-5 py-3 dark:bg-[linear-gradient(135deg,rgba(214,171,91,0.09),transparent_45%),linear-gradient(180deg,rgba(25,22,18,0.94),rgba(15,15,13,0.96))]">
        <div className="grid gap-3 xl:grid-cols-[minmax(0,1fr)_minmax(270px,420px)]">
          <div className="space-y-2">
            <p className="text-[10px] uppercase tracking-[0.34em] text-[hsl(var(--muted))]">Archive gallery</p>
            <h2 className="max-w-4xl font-display text-[2.35rem] leading-[0.96] sm:text-[2.9rem]">
              Search your archive by what is in the image, where it was taken, and where it lives.
            </h2>
            <p className="max-w-2xl text-[12px] leading-relaxed text-[hsl(var(--muted-foreground))]">
              Use the main search, the structured fields, and the folder browser together. Cards now show summary text,
              tags, and folder location so it is easier to move around large nested archives.
            </p>
          </div>
          <div className="grid gap-2 sm:grid-cols-3">
            <StatCard label="Results" value={total.toLocaleString()} hint="items matching current filters" />
            <StatCard label="Visible folders" value={String(folders.length)} hint="subfolders in this view" />
            <StatCard label="Top tags" value={String(topTags.length)} hint={topTags.slice(0, 3).join(", ") || "none yet"} />
          </div>
        </div>

        <div className="mt-2 grid gap-2 xl:grid-cols-[minmax(0,1fr)_auto]">
          <div className="flex items-center gap-3 rounded-[1.25rem] border border-[hsl(var(--border))] bg-[hsl(var(--surface))]/90 px-4 py-2.5 shadow-[0_24px_80px_-60px_rgba(0,0,0,0.4)] backdrop-blur-sm">
            <Search size={16} className="shrink-0 text-[hsl(var(--muted))]" />
            <input
              type="text"
              placeholder="Search filename, text in image, place, scene, subject..."
              value={query}
              onChange={(event) => startTransition(() => setQuery(event.target.value))}
              className="w-full bg-transparent text-[13px] outline-none placeholder:text-[hsl(var(--muted))]"
            />
            <button
              onClick={() => setFilterOpen((value) => !value)}
              className={cn(
                "inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-[10px] uppercase tracking-[0.18em] transition-colors",
                filterOpen
                  ? "border-transparent bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]"
                  : "border-[hsl(var(--border))] text-[hsl(var(--muted))] hover:text-[hsl(var(--foreground))]"
              )}
            >
              <SlidersHorizontal size={12} />
              Filters{activeFilterCount ? ` ${activeFilterCount}` : ""}
            </button>
            <button
              onClick={resetFilters}
              className="inline-flex items-center gap-2 rounded-full border border-[hsl(var(--border))] px-3 py-1.5 text-[10px] uppercase tracking-[0.18em] text-[hsl(var(--muted))] transition-colors hover:text-[hsl(var(--foreground))]"
            >
              Reset filters
            </button>
          </div>

          <div className="flex items-center justify-between gap-2 rounded-[1.2rem] border border-[hsl(var(--border))] bg-[hsl(var(--surface))]/90 px-3 py-1.5 shadow-[0_24px_80px_-60px_rgba(0,0,0,0.4)] backdrop-blur-sm">
            <button
              onClick={() => load("refresh")}
              title="Refresh"
              className="inline-flex items-center gap-2 rounded-full px-2 py-1 text-[11px] text-[hsl(var(--muted))] transition-colors hover:text-[hsl(var(--foreground))]"
            >
              <RefreshCw size={13} className={refreshing ? "animate-spin" : ""} />
              Refresh
            </button>

            {viewMode === "grid" && (
              <div className="flex items-center gap-1.5">
                <button onClick={() => setZoom((value) => Math.max(0, value - 1))} disabled={zoom === 0} className="text-[hsl(var(--muted))] disabled:opacity-30">
                  <ZoomIn size={13} />
                </button>
                <input
                  type="range"
                  min={0}
                  max={ZOOM_COLS.length - 1}
                  value={zoom}
                  onChange={(event) => setZoom(Number(event.target.value))}
                  className="w-16 cursor-pointer accent-[hsl(var(--accent-strong))]"
                  style={{ direction: "rtl" }}
                />
                <button onClick={() => setZoom((value) => Math.min(ZOOM_COLS.length - 1, value + 1))} disabled={zoom === ZOOM_COLS.length - 1} className="text-[hsl(var(--muted))] disabled:opacity-30">
                  <ZoomOut size={13} />
                </button>
              </div>
            )}

            <div className="flex overflow-hidden rounded-full border border-[hsl(var(--border))]">
              {(["grid", "list"] as ViewMode[]).map((mode) => (
                <button
                  key={mode}
                  onClick={() => setViewMode(mode)}
                  className={cn(
                    "p-2 transition-colors",
                    viewMode === mode
                      ? "bg-[hsl(var(--accent-strong))] text-[hsl(var(--accent-foreground))]"
                      : "text-[hsl(var(--muted))] hover:bg-[hsl(var(--surface-raised))] hover:text-[hsl(var(--foreground))]"
                  )}
                >
                  {mode === "grid" ? <LayoutGrid size={13} /> : <List size={13} />}
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      {filterOpen && (
        <FilterBar
          typeFilter={typeFilter}
          aiTextFilter={aiTextFilter}
          sceneFilter={sceneFilter}
          placeFilter={placeFilter}
          objectFilter={objectFilter}
          hasOcr={hasOcr}
          hasGps={hasGps}
          hasAi={hasAi}
          reviewBucket={reviewBucket}
          onTypeChange={setTypeFilter}
          onAiTextChange={setAiTextFilter}
          onSceneChange={setSceneFilter}
          onPlaceChange={setPlaceFilter}
          onObjectChange={setObjectFilter}
          onHasOcrChange={setHasOcr}
          onHasGpsChange={setHasGps}
          onHasAiChange={setHasAi}
          onReviewBucketChange={setReviewBucket}
        />
      )}

      <div className="flex-1 overflow-auto px-5 pb-6 pt-4">
        {error ? (
          <div className="flex h-full flex-col items-center justify-center gap-3">
            <p className="text-[11px] uppercase tracking-[0.18em] text-red-500">Connection error</p>
            <p className="max-w-xs text-center text-[12px] text-[hsl(var(--muted-foreground))]">{error}</p>
          </div>
        ) : loading ? (
          <div className="flex h-full items-center justify-center">
            <span className="text-[11px] text-[hsl(var(--muted))]">Loading gallery...</span>
          </div>
        ) : items.length === 0 ? (
          <EmptyGallery />
        ) : (
          <div className="grid gap-5 lg:grid-cols-[360px_minmax(0,1fr)]">
            <aside className="space-y-4">
              <FolderPanel folders={allFolders} folderFilter={folderFilter} onFolderChange={setFolderFilter} />
              <TagPanel tags={topTags} onTagClick={(tag) => setQuery(tag)} />
            </aside>

            <div className="space-y-4">
              {folderFilter && (
                <div className="flex items-center gap-2 rounded-[1.2rem] border border-[hsl(var(--border))] bg-[hsl(var(--surface))] px-4 py-3 text-[12px]">
                  <button onClick={() => setFolderFilter(undefined)} className="inline-flex items-center gap-2 text-[hsl(var(--muted))]">
                    <ArrowLeft size={12} />
                    All folders
                  </button>
                  <span className="text-[hsl(var(--muted))]">/</span>
                  <span className="font-mono">{folderFilter}</span>
                </div>
              )}

              {viewMode === "grid" ? (
                <div className={cn("gap-3 space-y-3", ZOOM_COLS[zoom])}>
                  {items.map((asset) => (
                    <AssetCard key={asset.id} asset={asset} compact={zoom >= 3} />
                  ))}
                </div>
              ) : (
                <ListView assets={items} />
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({ label, value, hint }: { label: string; value: string; hint: string }) {
  return (
    <div className="rounded-[1.1rem] border border-[hsl(var(--border))] bg-[hsl(var(--surface))]/85 p-3 shadow-[0_30px_90px_-70px_rgba(0,0,0,0.55)] backdrop-blur-sm">
      <p className="text-[10px] uppercase tracking-[0.22em] text-[hsl(var(--muted))]">{label}</p>
      <p className="mt-1.5 font-display text-2xl leading-none">{value}</p>
      <p className="mt-1.5 text-[10px] text-[hsl(var(--muted-foreground))]">{hint}</p>
    </div>
  );
}

function FolderPanel({
  folders,
  folderFilter,
  onFolderChange,
}: {
  folders: FolderItem[];
  folderFilter?: string;
  onFolderChange: (value: string | undefined) => void;
}) {
  const visibleFolders = folders.filter((folder) => folder.path !== "/");
  return (
    <div className="rounded-[1.5rem] border border-[hsl(var(--border))] bg-[hsl(var(--surface))] p-4 shadow-[0_24px_80px_-66px_rgba(0,0,0,0.5)]">
      <div className="mb-3 flex items-center gap-2 text-[10px] uppercase tracking-[0.22em] text-[hsl(var(--muted))]">
        <FolderTree size={14} />
        Folders
      </div>
      <div className="space-y-1.5">
        <button
          onClick={() => onFolderChange(undefined)}
          className={cn(
            "w-full rounded-[1rem] px-3 py-2 text-left text-[12px] transition-colors",
            !folderFilter ? "bg-[hsl(var(--accent-strong))] text-[hsl(var(--accent-foreground))]" : "hover:bg-[hsl(var(--surface-raised))]"
          )}
        >
          All folders
        </button>
        <div className="max-h-[18rem] overflow-auto pr-1">
          <div className="space-y-1.5">
            {visibleFolders.map((folder) => (
              <button
                key={folder.path}
                onClick={() => onFolderChange(folder.path)}
                className={cn(
                  "flex w-full items-center justify-between gap-3 rounded-[1rem] px-3 py-2 text-left text-[12px] transition-colors hover:bg-[hsl(var(--surface-raised))]",
                  folderFilter === folder.path && "bg-[hsl(var(--accent-strong))] text-[hsl(var(--accent-foreground))]"
                )}
              >
                <span className="truncate font-mono">{folder.path}</span>
                <span className="text-[10px] opacity-70">{folder.count}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function TagPanel({ tags, onTagClick }: { tags: string[]; onTagClick: (tag: string) => void }) {
  return (
    <div className="rounded-[1.5rem] border border-[hsl(var(--border))] bg-[hsl(var(--surface))] p-4 shadow-[0_24px_80px_-66px_rgba(0,0,0,0.5)]">
      <div className="mb-3 text-[10px] uppercase tracking-[0.22em] text-[hsl(var(--muted))]">Popular tags</div>
      <div className="flex flex-wrap gap-2">
        {tags.length > 0 ? tags.map((tag) => (
          <button
            key={tag}
            onClick={() => onTagClick(tag)}
            className="rounded-full border border-[hsl(var(--border))] bg-[hsl(var(--surface-raised))] px-3 py-1 text-[11px]"
          >
            {tag}
          </button>
        )) : <p className="text-[12px] text-[hsl(var(--muted-foreground))]">Run AI on more photos to build tag suggestions.</p>}
      </div>
    </div>
  );
}

function EmptyGallery() {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-4 px-8 text-center">
      <p className="text-[11px] uppercase tracking-[0.26em] text-[hsl(var(--muted))]">No items</p>
      <p className="max-w-md text-[13px] leading-relaxed text-[hsl(var(--muted-foreground))]">
        Add a source folder, run scan and thumbnail jobs, and the gallery will populate here.
      </p>
      <Link href="/settings" className="inline-flex items-center gap-2 rounded-full border border-[hsl(var(--border))] px-4 py-2 text-[11px] uppercase tracking-[0.18em]">
        Open settings
      </Link>
    </div>
  );
}

function ListView({ assets }: { assets: AssetListItem[] }) {
  return (
    <div className="overflow-hidden rounded-[1.5rem] border border-[hsl(var(--border))] bg-[hsl(var(--surface))] shadow-[0_24px_80px_-66px_rgba(0,0,0,0.5)]">
      <table className="w-full text-[12px]">
        <thead className="bg-[hsl(var(--surface))]">
          <tr className="border-b border-[hsl(var(--border-subtle))]">
            {["Asset", "Folder", "Summary", "Tags"].map((heading) => (
              <th key={heading} className="px-4 py-3 text-left text-[10px] uppercase tracking-[0.18em] text-[hsl(var(--muted))]">
                {heading}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {assets.map((asset) => (
            <tr key={asset.id} className="border-b border-[hsl(var(--border-subtle))] last:border-b-0">
              <td className="px-4 py-4">
                <Link href={`/asset/${asset.id}`} className="block">
                  <p className="font-medium">{asset.filename}</p>
                  <p className="mt-1 text-[11px] text-[hsl(var(--muted-foreground))]">
                    {asset.captured_at ? new Date(asset.captured_at).toLocaleString() : "No date"}
                  </p>
                </Link>
              </td>
              <td className="px-4 py-4 font-mono text-[11px] text-[hsl(var(--muted-foreground))]">{asset.folder_path ?? "/"}</td>
              <td className="px-4 py-4 text-[hsl(var(--muted-foreground))]">{asset.summary ?? asset.scene_label ?? "—"}</td>
              <td className="px-4 py-4">
                <div className="flex flex-wrap gap-1.5">
                  {asset.tags.slice(0, 5).map((tag) => (
                    <span key={tag} className="rounded-full border border-[hsl(var(--border))] px-2 py-0.5 text-[10px]">
                      {tag}
                    </span>
                  ))}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function findTopTags(items: AssetListItem[]) {
  const counts = new Map<string, number>();
  for (const item of items) {
    for (const tag of item.tags) {
      counts.set(tag, (counts.get(tag) ?? 0) + 1);
    }
  }
  return [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 20).map(([tag]) => tag);
}
