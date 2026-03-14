"use client";

import { usePathname } from "next/navigation";

const TITLES: Record<string, string> = {
  "/gallery":  "Gallery",
  "/places":   "Places",
  "/review":   "Review",
  "/jobs":     "Jobs",
  "/settings": "Settings",
};

function getTitle(pathname: string): string {
  for (const [prefix, title] of Object.entries(TITLES)) {
    if (pathname.startsWith(prefix)) return title;
  }
  return "Media Archive Tool";
}

export function Topbar() {
  const pathname = usePathname();
  const title = getTitle(pathname);
  const subtitles: Record<string, string> = {
    Gallery: "Search by content, place, text, and folder",
    Places: "Spatial reconstruction of the archive",
    Review: "Items that need a closer look",
    Jobs: "Ingestion, extraction, and reprocessing orchestration",
    Settings: "Local sources, model routing, and runtime controls",
  };

  return (
    <header className="flex h-[var(--topbar-height)] shrink-0 items-center gap-4 border-b border-[hsl(var(--border-subtle))] bg-[hsl(var(--surface))]/92 px-5 backdrop-blur-md">
      <div>
        <h1 className="font-display text-3xl leading-none text-[hsl(var(--foreground))]">
          {title}
        </h1>
        <p className="mt-1 text-[11px] uppercase tracking-[0.18em] text-[hsl(var(--muted))]">
          {subtitles[title] ?? "Private archive search and browsing"}
        </p>
      </div>
      <div className="flex-1" />
      <div className="text-right">
        <p className="text-[10px] uppercase tracking-[0.24em] text-[hsl(var(--muted))]">Local archive</p>
        <p className="mt-1 text-[11px] text-[hsl(var(--muted-foreground))]">Originals stay in place, metadata lives on top</p>
      </div>
    </header>
  );
}
