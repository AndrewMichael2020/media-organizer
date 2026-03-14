"use client";

import { X } from "lucide-react";
import { cn } from "@/lib/utils";

interface FilterBarProps {
  typeFilter?: string;
  matchMode?: "any" | "all";
  aiTextFilter?: string;
  sceneFilter?: string;
  placeFilter?: string;
  objectFilter?: string;
  hasOcr?: boolean;
  hasGps?: boolean;
  hasAi?: boolean;
  reviewBucket?: string;
  onTypeChange?: (type: string | undefined) => void;
  onMatchModeChange?: (value: "any" | "all") => void;
  onAiTextChange?: (value: string) => void;
  onSceneChange?: (value: string) => void;
  onPlaceChange?: (value: string) => void;
  onObjectChange?: (value: string) => void;
  onHasOcrChange?: (value: boolean) => void;
  onHasGpsChange?: (value: boolean) => void;
  onHasAiChange?: (value: boolean) => void;
  onReviewBucketChange?: (value: string | undefined) => void;
}

const REVIEW_FILTERS = [
  { value: undefined, label: "All" },
  { value: "needs-extraction", label: "Needs AI" },
  { value: "timestamp-conflict", label: "Date conflict" },
  { value: "low-confidence", label: "Low confidence" },
  { value: "location-unverified", label: "GPS no place" },
] as const;

export function FilterBar({
  typeFilter,
  matchMode = "any",
  aiTextFilter = "",
  sceneFilter = "",
  placeFilter = "",
  objectFilter = "",
  hasOcr = false,
  hasGps = false,
  hasAi = false,
  reviewBucket,
  onTypeChange,
  onMatchModeChange,
  onAiTextChange,
  onSceneChange,
  onPlaceChange,
  onObjectChange,
  onHasOcrChange,
  onHasGpsChange,
  onHasAiChange,
  onReviewBucketChange,
}: FilterBarProps) {
  const dirty = !!typeFilter || !!aiTextFilter || !!sceneFilter || !!placeFilter || !!objectFilter || hasOcr || hasGps || hasAi || !!reviewBucket || matchMode !== "any";

  return (
    <div className="grid gap-1.5 border-b border-[hsl(var(--border-subtle))] bg-[hsl(var(--surface))] px-5 py-1.5 text-[11px] xl:grid-cols-[auto_auto_minmax(0,1fr)_auto]">
      <div className="flex flex-wrap items-center gap-1">
        <span className="mr-1 text-[10px] uppercase tracking-[0.18em] text-[hsl(var(--muted))]">Type</span>
        {([undefined, "photo", "video"] as const).map((t) => (
          <button
            key={t ?? "all"}
            onClick={() => onTypeChange?.(t)}
            className={cn(
              "rounded-full px-2.5 py-1 text-[10px] uppercase tracking-[0.18em] font-medium transition-colors",
              typeFilter === t
                ? "bg-[hsl(var(--accent-strong))] text-[hsl(var(--accent-foreground))]"
                : "border border-[hsl(var(--border))] text-[hsl(var(--muted))] hover:border-[hsl(var(--border-strong))] hover:text-[hsl(var(--foreground))]"
            )}
          >
            {t ?? "all"}
          </button>
        ))}
      </div>

      <div className="flex flex-wrap items-center gap-1">
        <span className="mr-1 text-[10px] uppercase tracking-[0.18em] text-[hsl(var(--muted))]">Quick filters</span>
        <ToggleChip active={hasAi} onClick={() => onHasAiChange?.(!hasAi)} label="Has AI" />
        <ToggleChip active={hasOcr} onClick={() => onHasOcrChange?.(!hasOcr)} label="Has text" />
        <ToggleChip active={hasGps} onClick={() => onHasGpsChange?.(!hasGps)} label="Has GPS" />
        <span className="ml-2 mr-1 text-[10px] uppercase tracking-[0.18em] text-[hsl(var(--muted))]">Match</span>
        <ToggleChip active={matchMode === "any"} onClick={() => onMatchModeChange?.("any")} label="Any" />
        <ToggleChip active={matchMode === "all"} onClick={() => onMatchModeChange?.("all")} label="All" />
      </div>

      <div className="grid gap-2 lg:grid-cols-[minmax(150px,0.9fr)_repeat(3,minmax(140px,1fr))_auto]">
        <Field placeholder="AI text: summary, notes, tags..." value={aiTextFilter} onChange={onAiTextChange} />
        <Field placeholder="Scene: outdoor, snow..." value={sceneFilter} onChange={onSceneChange} />
        <Field placeholder="Place: city, mountain..." value={placeFilter} onChange={onPlaceChange} />
        <Field placeholder="Object: dog, purse..." value={objectFilter} onChange={onObjectChange} />
        <div className="flex flex-wrap items-center gap-1">
          {REVIEW_FILTERS.map((item) => (
            <button
              key={item.label}
              onClick={() => onReviewBucketChange?.(item.value)}
              className={cn(
                "rounded-full border px-2.5 py-1 text-[10px] uppercase tracking-[0.14em] transition-colors",
                reviewBucket === item.value
                  ? "border-transparent bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]"
                  : "border-[hsl(var(--border))] text-[hsl(var(--muted))] hover:border-[hsl(var(--border-strong))] hover:text-[hsl(var(--foreground))]"
              )}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {dirty && (
        <div className="flex items-center justify-end">
          <button
            onClick={() => {
              onTypeChange?.(undefined);
              onAiTextChange?.("");
              onSceneChange?.("");
              onPlaceChange?.("");
              onObjectChange?.("");
              onHasOcrChange?.(false);
              onHasGpsChange?.(false);
              onHasAiChange?.(false);
              onReviewBucketChange?.(undefined);
              onMatchModeChange?.("any");
            }}
            className="flex items-center gap-1 text-[hsl(var(--muted))] transition-colors hover:text-[hsl(var(--foreground))]"
          >
            <X size={11} />
            Reset
          </button>
        </div>
      )}
    </div>
  );
}

function ToggleChip({ active, onClick, label }: { active: boolean; onClick: () => void; label: string }) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "rounded-full border px-2 py-[3px] text-[10px] uppercase tracking-[0.14em] transition-colors",
        active
          ? "border-transparent bg-[hsl(var(--accent-strong))] text-[hsl(var(--accent-foreground))]"
          : "border-[hsl(var(--border))] text-[hsl(var(--muted))] hover:border-[hsl(var(--border-strong))] hover:text-[hsl(var(--foreground))]"
      )}
    >
      {label}
    </button>
  );
}

function Field({ placeholder, value, onChange }: { placeholder: string; value: string; onChange?: (value: string) => void }) {
  return (
    <input
      type="text"
      value={value}
      onChange={(event) => onChange?.(event.target.value)}
      placeholder={placeholder}
      className="h-9 rounded-[0.85rem] border border-[hsl(var(--border))] bg-[hsl(var(--surface-raised))] px-3 text-[12px] outline-none placeholder:text-[hsl(var(--muted))]"
    />
  );
}
