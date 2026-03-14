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
  return "Forensic Media Organizer";
}

export function Topbar() {
  const pathname = usePathname();
  const title = getTitle(pathname);

  return (
    <header className="h-11 border-b border-[hsl(var(--border-subtle))] bg-[hsl(var(--surface))] flex items-center px-5 shrink-0 gap-4">
      <h1 className="text-[12px] font-semibold tracking-wider uppercase text-[hsl(var(--foreground))]">
        {title}
      </h1>
      <div className="flex-1" />
      <span className="text-[10px] text-[hsl(var(--muted))] tracking-widest uppercase font-medium">
        Local Archive
      </span>
    </header>
  );
}
