"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Grid2X2,
  MapPin,
  ClipboardList,
  Cpu,
  Settings,
  SunMedium,
  Moon,
} from "lucide-react";
import { useTheme } from "next-themes";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/gallery",  label: "Gallery",  icon: Grid2X2 },
  { href: "/places",   label: "Places",   icon: MapPin },
  { href: "/review",   label: "Review",   icon: ClipboardList },
  { href: "/jobs",     label: "Jobs",     icon: Cpu },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { theme, setTheme } = useTheme();

  return (
    <aside className="z-20 flex min-h-screen w-[var(--sidebar-width)] shrink-0 flex-col border-r border-[hsl(var(--border))] bg-[linear-gradient(180deg,hsl(var(--surface)),hsl(var(--surface-raised)))]">
      <div className="border-b border-[hsl(var(--border-subtle))] px-3 py-4">
        <p className="text-[10px] uppercase tracking-[0.28em] text-[hsl(var(--muted))]">Media</p>
        <p className="mt-2 font-display text-xl leading-none text-[hsl(var(--foreground))]">Archive Tool</p>
        <p className="mt-1 text-[10px] leading-relaxed text-[hsl(var(--muted-foreground))]">
          Local-first photo archive workspace
        </p>
      </div>

      <nav className="flex flex-1 flex-col gap-1 p-2 pt-4">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              title={label}
              className={cn(
                "group flex flex-col items-center gap-1 rounded-[1.1rem] px-1 py-3 transition-colors",
                active
                  ? "bg-[hsl(var(--accent-strong))] text-[hsl(var(--accent-foreground))] shadow-[0_20px_40px_-24px_rgba(0,0,0,0.55)]"
                  : "text-[hsl(var(--muted))] hover:bg-[hsl(var(--surface-strong))] hover:text-[hsl(var(--foreground))]"
              )}
            >
              <Icon size={16} strokeWidth={1.5} />
              <span className="text-[9px] uppercase tracking-[0.18em] font-medium">{label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-[hsl(var(--border-subtle))] p-2 pb-3">
        <button
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          title="Toggle theme"
          className="flex w-full flex-col items-center gap-1 rounded-[1.1rem] px-1 py-3 text-[hsl(var(--muted))] transition-colors hover:bg-[hsl(var(--surface-strong))] hover:text-[hsl(var(--foreground))]"
        >
          {theme === "dark" ? (
            <SunMedium size={16} strokeWidth={1.5} />
          ) : (
            <Moon size={16} strokeWidth={1.5} />
          )}
          <span className="text-[9px] uppercase tracking-[0.18em] font-medium">Theme</span>
        </button>
      </div>
    </aside>
  );
}
