"use client";

import Link from "next/link";
import { startTransition, useCallback, useDeferredValue, useEffect, useMemo, useState } from "react";
import { ExternalLink, MapPin, RefreshCw, Search, SlidersHorizontal } from "lucide-react";
import { api, type AssetListItem } from "@/lib/api";
import { PlacesMap } from "@/components/maps/places-map";
import { cn } from "@/lib/utils";

function openStreetMapUrl(lat: number, lon: number) {
  return `https://www.openstreetmap.org/?mlat=${lat}&mlon=${lon}#map=13/${lat}/${lon}`;
}

export default function PlacesPage() {
  const [items, setItems] = useState<AssetListItem[]>([]);
  const [folders, setFolders] = useState<string[]>([]);
  const [locationFilter, setLocationFilter] = useState<string>("all");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filterOpen, setFilterOpen] = useState(true);
  const [query, setQuery] = useState("");
  const [aiText, setAiText] = useState("");
  const [placeFilter, setPlaceFilter] = useState("");
  const [folderFilter, setFolderFilter] = useState("");
  const deferredQuery = useDeferredValue(query);
  const deferredAiText = useDeferredValue(aiText);
  const deferredPlace = useDeferredValue(placeFilter);
  const deferredFolder = useDeferredValue(folderFilter);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [hasLoadedOnce, setHasLoadedOnce] = useState(false);
  const [mapScope, setMapScope] = useState<"selected" | "all" | "folder">("all");
  const [mapFolder, setMapFolder] = useState<string>("all");

  const load = useCallback(async (mode: "initial" | "refresh" = "initial") => {
    if (mode === "refresh") {
      setRefreshing(true);
    } else if (!hasLoadedOnce) {
      setLoading(true);
    }
    try {
      const [res, folderRes] = await Promise.all([
        api.assets.list({
          has_gps: true,
          page_size: 200,
          q: deferredQuery || undefined,
          ai_text: deferredAiText || undefined,
          place: deferredPlace || undefined,
          folder: deferredFolder || undefined,
        }),
        api.assets.folders({
          has_gps: true,
          q: deferredQuery || undefined,
          ai_text: deferredAiText || undefined,
          place: deferredPlace || undefined,
          folder: deferredFolder || undefined,
        }),
      ]);
      setItems(res.items);
      setFolders(folderRes.items.map((item) => item.path).filter((path) => path !== "/"));
      setSelectedId((current) => current && res.items.some((item) => item.id === current) ? current : res.items[0]?.id ?? null);
      setHasLoadedOnce(true);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [deferredAiText, deferredFolder, deferredPlace, deferredQuery, hasLoadedOnce]);

  useEffect(() => {
    load();
  }, [load]);

  const scopedItems = useMemo(() => {
    if (mapScope === "folder" && mapFolder !== "all") {
      return items.filter((item) => item.folder_path === mapFolder);
    }
    return items;
  }, [items, mapFolder, mapScope]);

  const locationOptions = useMemo(() => {
    const labels = new Set<string>();
    for (const item of scopedItems) {
      if (item.place_label?.trim()) {
        labels.add(item.place_label.trim());
      }
    }
    return [...labels].sort((a, b) => a.localeCompare(b));
  }, [scopedItems]);

  const visibleItems = useMemo(() => {
    if (locationFilter === "all") return scopedItems;
    return scopedItems.filter((item) => item.place_label === locationFilter);
  }, [locationFilter, scopedItems]);

  useEffect(() => {
    if (locationFilter !== "all" && !locationOptions.includes(locationFilter)) {
      setLocationFilter("all");
    }
  }, [locationFilter, locationOptions]);

  useEffect(() => {
    if (!visibleItems.some((item) => item.id === selectedId)) {
      setSelectedId(visibleItems[0]?.id ?? null);
    }
  }, [visibleItems, selectedId]);

  const selected = useMemo(
    () => visibleItems.find((item) => item.id === selectedId) ?? visibleItems[0] ?? null,
    [visibleItems, selectedId]
  );

  const mapItems = useMemo(() => {
    if (mapScope === "selected") {
      return selected ? [selected] : [];
    }
    return visibleItems;
  }, [mapScope, visibleItems, selected]);

  function resetFilters() {
    setQuery("");
    setAiText("");
    setPlaceFilter("");
    setFolderFilter("");
    setLocationFilter("all");
    setMapScope("all");
    setMapFolder("all");
  }

  if (loading) {
    return <div className="flex h-full items-center justify-center text-[12px] text-[hsl(var(--muted))]">Loading places...</div>;
  }

  return (
    <div className="flex h-full flex-col">
      <section className="border-b border-[hsl(var(--border-subtle))] bg-[linear-gradient(135deg,rgba(103,77,41,0.08),transparent_45%),linear-gradient(180deg,rgba(255,248,238,0.9),rgba(255,255,255,0.72))] px-5 py-5 dark:bg-[linear-gradient(135deg,rgba(214,171,91,0.09),transparent_45%),linear-gradient(180deg,rgba(25,22,18,0.94),rgba(15,15,13,0.96))]">
        <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(260px,420px)]">
          <div className="space-y-3">
            <p className="text-[10px] uppercase tracking-[0.34em] text-[hsl(var(--muted))]">Places</p>
            <h2 className="font-display text-4xl leading-none sm:text-5xl">
              Browse geo-tagged photos on a map and in a searchable location list.
            </h2>
            <p className="max-w-2xl text-[13px] leading-relaxed text-[hsl(var(--muted-foreground))]">
              This view focuses on photos with coordinates. Search broadly, filter on AI text or place clues, then inspect
              the selected item on an embedded OpenStreetMap panel.
            </p>
          </div>
          <div className="grid gap-3 sm:grid-cols-3">
            <StatCard label="Mapped photos" value={String(visibleItems.length)} hint="results with coordinates" />
            <StatCard label="Selected place" value={selected?.place_label ?? "—"} hint={selected?.filename ?? "pick a photo"} />
            <StatCard
              label="Coordinates"
              value={mapItems[0]?.lat != null ? `${mapItems[0].lat?.toFixed(3)}, ${mapItems[0].lon?.toFixed(3) ?? "—"}` : "—"}
              hint={mapScope === "selected" ? "current map center" : `${mapItems.length} point view`}
            />
          </div>
        </div>

        <div className="mt-3 grid gap-2 xl:grid-cols-[minmax(0,1fr)_auto]">
          <div className="flex items-center gap-3 rounded-[1.25rem] border border-[hsl(var(--border))] bg-[hsl(var(--surface))]/90 px-4 py-2.5 shadow-[0_24px_80px_-60px_rgba(0,0,0,0.4)] backdrop-blur-sm">
            <Search size={16} className="shrink-0 text-[hsl(var(--muted))]" />
            <input
              type="text"
              placeholder="Search filename, OCR text, place, folder..."
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
              Filters
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
          </div>
        </div>
      </section>

      {filterOpen ? (
        <div className="grid gap-1.5 border-b border-[hsl(var(--border-subtle))] bg-[hsl(var(--surface))] px-5 py-1.5 md:grid-cols-[minmax(140px,0.9fr)_minmax(140px,1fr)_minmax(170px,1fr)_180px_180px_120px]">
          <Field placeholder="AI text: summary, notes, tags..." value={aiText} onChange={setAiText} />
          <Field placeholder="Place: bay, city, district..." value={placeFilter} onChange={setPlaceFilter} />
          <SelectField
            value={locationFilter}
            onChange={setLocationFilter}
            options={[
              { value: "all", label: "Location: all" },
              ...locationOptions.map((location) => ({ value: location, label: location })),
            ]}
          />
          <SelectField
            value={mapScope}
            onChange={(value) => setMapScope(value as "selected" | "all" | "folder")}
            options={[
              { value: "selected", label: "Map: selected" },
              { value: "all", label: "Map: all results" },
              { value: "folder", label: "Map: one folder" },
            ]}
          />
          <SelectField
            value={mapFolder}
            onChange={setMapFolder}
            disabled={mapScope !== "folder"}
            options={[
              { value: "all", label: "All folders" },
              ...folders.map((folder) => ({ value: folder, label: folder })),
            ]}
          />
          <button
            onClick={() => setLocationFilter("all")}
            className="h-9 rounded-[0.85rem] border border-[hsl(var(--border))] bg-[hsl(var(--surface-raised))] px-3 text-[12px] transition-colors hover:bg-[hsl(var(--surface))]"
          >
            Clear
          </button>
        </div>
      ) : null}

      <div className="flex-1 overflow-auto px-5 py-4">
        {items.length === 0 ? (
          <div className="rounded-[1.5rem] border border-[hsl(var(--border))] bg-[hsl(var(--surface))] p-6 text-[12px] text-[hsl(var(--muted-foreground))]">
            No geo-tagged photos match these filters.
          </div>
        ) : (
          <div className="grid gap-5 xl:grid-cols-[minmax(0,480px)_minmax(0,1fr)]">
            <section className="overflow-hidden rounded-[1.5rem] border border-[hsl(var(--border))] bg-[hsl(var(--surface))] shadow-[0_24px_80px_-66px_rgba(0,0,0,0.45)]">
              <div className="border-b border-[hsl(var(--border-subtle))] px-4 py-3 text-[10px] uppercase tracking-[0.18em] text-[hsl(var(--muted))]">
                Location list
              </div>
              <div className="divide-y divide-[hsl(var(--border-subtle))]">
                <div className="grid grid-cols-[92px_minmax(0,1.15fr)_minmax(150px,0.9fr)_110px_140px] gap-3 px-4 py-2 text-[10px] uppercase tracking-[0.16em] text-[hsl(var(--muted))]">
                  <span>Preview</span>
                  <span>Photo</span>
                  <span>Location</span>
                  <span>Date</span>
                  <span>Coords</span>
                </div>
                {visibleItems.map((item) => {
                  const selectedRow = item.id === selected?.id;
                  return (
                    <button
                      key={item.id}
                      onClick={() => setSelectedId(item.id)}
                      className={cn(
                        "grid w-full grid-cols-[92px_minmax(0,1.15fr)_minmax(150px,0.9fr)_110px_140px] gap-3 px-4 py-3 text-left transition-colors hover:bg-[hsl(var(--surface-raised))]",
                        selectedRow && "bg-[hsl(var(--surface-raised))]"
                      )}
                    >
                      <div className="overflow-hidden rounded-[0.9rem] bg-[hsl(var(--surface-raised))]">
                        <Link
                          href={`/gallery?focus=${item.id}`}
                          onClick={(event) => event.stopPropagation()}
                          className="block h-[74px] w-full"
                        >
                          {item.thumbnail_url ? (
                            // eslint-disable-next-line @next/next/no-img-element
                            <img src={item.thumbnail_url} alt={item.filename} className="h-[74px] w-full object-cover" />
                          ) : (
                            <div className="flex h-[74px] items-center justify-center text-[10px] text-[hsl(var(--muted))]">No preview</div>
                          )}
                        </Link>
                      </div>
                      <div className="min-w-0 space-y-1">
                        <p className="truncate text-[13px] font-medium">{item.filename}</p>
                        <p className="truncate text-[11px] text-[hsl(var(--muted-foreground))]">{item.folder_path ?? "/"}</p>
                      </div>
                      <div className="min-w-0 pt-1 text-[11px] text-[hsl(var(--muted-foreground))]">
                        {item.place_label ? (
                          <span className="inline-flex items-center gap-1 rounded-full border border-[hsl(var(--border))] px-2 py-0.5">
                            <MapPin size={11} />
                            {item.place_label}
                          </span>
                        ) : (
                          <span>GPS only</span>
                        )}
                      </div>
                      <div className="pt-1 text-[11px] text-[hsl(var(--muted-foreground))]">
                        {item.captured_at ? new Date(item.captured_at).toLocaleDateString() : "—"}
                      </div>
                      <div className="pt-1 font-mono text-[10px] text-[hsl(var(--muted))]">
                        {item.lat?.toFixed(5) ?? "—"}, {item.lon?.toFixed(5) ?? "—"}
                      </div>
                    </button>
                  );
                })}
              </div>
            </section>

            <section className="space-y-4">
              <div className="overflow-hidden rounded-[1.5rem] border border-[hsl(var(--border))] bg-[hsl(var(--surface))] shadow-[0_24px_80px_-66px_rgba(0,0,0,0.45)]">
                <div className="border-b border-[hsl(var(--border-subtle))] px-4 py-3 text-[10px] uppercase tracking-[0.18em] text-[hsl(var(--muted))]">
                  OpenStreetMap {mapScope === "all" ? "all results" : mapScope === "folder" ? "folder view" : "selected photo"}
                </div>
                {mapItems.length > 0 ? (
                  <PlacesMap items={mapItems} selectedId={selected?.id ?? null} onSelect={setSelectedId} mode={mapScope} />
                ) : (
                  <div className="flex h-[420px] items-center justify-center text-[12px] text-[hsl(var(--muted-foreground))]">
                    No coordinates available for this photo.
                  </div>
                )}
              </div>

              {selected ? (
                <div className="rounded-[1.5rem] border border-[hsl(var(--border))] bg-[hsl(var(--surface))] p-4 shadow-[0_24px_80px_-66px_rgba(0,0,0,0.45)]">
                  <div className="mb-3 flex items-center justify-between gap-3">
                    <div>
                      <p className="text-[10px] uppercase tracking-[0.18em] text-[hsl(var(--muted))]">Selected photo</p>
                      <p className="mt-1 text-[15px] font-medium">{selected.filename}</p>
                    </div>
                    <div className="flex gap-2">
                      <Link
                        href={`/asset/${selected.id}`}
                        className="inline-flex items-center gap-2 rounded-full border border-[hsl(var(--border))] px-3 py-1.5 text-[11px] uppercase tracking-[0.14em]"
                      >
                        Open photo
                      </Link>
                      {selected.lat != null && selected.lon != null ? (
                        <a
                          href={openStreetMapUrl(selected.lat, selected.lon)}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-2 rounded-full border border-[hsl(var(--border))] bg-[hsl(var(--surface-raised))] px-3 py-1.5 text-[11px] uppercase tracking-[0.14em]"
                        >
                          Open map
                          <ExternalLink size={12} />
                        </a>
                      ) : null}
                    </div>
                  </div>
                  <div className="grid gap-3 md:grid-cols-2">
                    <Info label="Place" value={selected.place_label ?? "—"} />
                    <Info label="Date" value={selected.captured_at ? new Date(selected.captured_at).toLocaleString() : "—"} />
                    <Info label="Folder" value={selected.folder_path ?? "/"} mono />
                    <Info label="Coordinates" value={selected.lat != null ? `${selected.lat.toFixed(5)}, ${selected.lon?.toFixed(5) ?? "—"}` : "—"} mono />
                  </div>
                </div>
              ) : null}
            </section>
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({ label, value, hint }: { label: string; value: string; hint: string }) {
  return (
    <div className="rounded-[1.25rem] border border-[hsl(var(--border))] bg-[hsl(var(--surface))]/85 p-4 shadow-[0_30px_90px_-70px_rgba(0,0,0,0.55)] backdrop-blur-sm">
      <p className="text-[10px] uppercase tracking-[0.22em] text-[hsl(var(--muted))]">{label}</p>
      <p className="mt-2 font-display text-3xl leading-none">{value}</p>
      <p className="mt-2 text-[11px] text-[hsl(var(--muted-foreground))]">{hint}</p>
    </div>
  );
}

function Field({ placeholder, value, onChange }: { placeholder: string; value: string; onChange: (value: string) => void }) {
  return (
    <input
      type="text"
      value={value}
      onChange={(event) => onChange(event.target.value)}
      placeholder={placeholder}
      className="h-9 rounded-[0.85rem] border border-[hsl(var(--border))] bg-[hsl(var(--surface-raised))] px-3 text-[12px] outline-none placeholder:text-[hsl(var(--muted))]"
    />
  );
}

function SelectField({
  value,
  onChange,
  options,
  disabled = false,
}: {
  value: string;
  onChange: (value: string) => void;
  options: { value: string; label: string }[];
  disabled?: boolean;
}) {
  return (
    <select
      value={value}
      onChange={(event) => onChange(event.target.value)}
      disabled={disabled}
      className="h-9 rounded-[0.85rem] border border-[hsl(var(--border))] bg-[hsl(var(--surface-raised))] px-3 text-[12px] outline-none disabled:opacity-50"
    >
      {options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  );
}

function Info({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="rounded-[1rem] bg-[hsl(var(--surface-raised))] px-3 py-2">
      <p className="text-[10px] uppercase tracking-[0.16em] text-[hsl(var(--muted))]">{label}</p>
      <p className={cn("mt-1 text-[12px] text-[hsl(var(--foreground))]", mono && "font-mono text-[11px] break-all")}>{value}</p>
    </div>
  );
}
