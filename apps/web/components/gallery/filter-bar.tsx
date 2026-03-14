"use client";

import { X } from "lucide-react";
import { cn } from "@/lib/utils";

interface FilterBarProps {
  typeFilter?: string;
  onTypeChange?: (type: string | undefined) => void;
}

export function FilterBar({ typeFilter, onTypeChange }: FilterBarProps) {
  const dirty = !!typeFilter;

  return (
    <div className="flex items-center gap-4 px-5 py-2 border-b border-[hsl(var(--border-subtle))] bg-[hsl(var(--surface))] text-[11px] shrink-0">
      <div className="flex items-center gap-1">
        <span className="text-[10px] uppercase tracking-wider text-[hsl(var(--muted))] mr-1">Type</span>
        {([undefined, "photo", "video"] as const).map((t) => (
          <button
            key={t ?? "all"}
            onClick={() => onTypeChange?.(t)}
            className={cn(
              "px-2 py-0.5 rounded text-[10px] uppercase tracking-wider font-medium transition-colors",
              typeFilter === t
                ? "bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]"
                : "text-[hsl(var(--muted))] hover:text-[hsl(var(--foreground))]"
            )}
          >
            {t ?? "all"}
          </button>
        ))}
      </div>

      {dirty && (
        <>
          <div className="flex-1" />
          <button
            onClick={() => onTypeChange?.(undefined)}
            className="flex items-center gap-1 text-[hsl(var(--muted))] hover:text-[hsl(var(--foreground))] transition-colors"
          >
            <X size={11} />
            Clear
          </button>
        </>
      )}
    </div>
  );
}
