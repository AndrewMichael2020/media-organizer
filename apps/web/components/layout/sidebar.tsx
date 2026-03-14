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
    <aside className="flex flex-col h-full w-14 border-r border-[hsl(var(--border))] bg-[hsl(var(--surface))] shrink-0 z-20">
      {/* Logo mark */}
      <div className="h-11 flex items-center justify-center border-b border-[hsl(var(--border-subtle))]">
        <span className="text-[11px] font-semibold tracking-[0.2em] text-[hsl(var(--muted))] uppercase select-none">
          FMO
        </span>
      </div>

      {/* Nav icons */}
      <nav className="flex flex-col gap-0.5 p-1.5 flex-1 pt-3">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              title={label}
              className={cn(
                "flex flex-col items-center gap-1 py-2.5 px-1 rounded-md transition-colors group",
                active
                  ? "bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]"
                  : "text-[hsl(var(--muted))] hover:text-[hsl(var(--foreground))] hover:bg-[hsl(var(--surface-raised))]"
              )}
            >
              <Icon size={16} strokeWidth={1.5} />
              <span className="text-[9px] tracking-wide uppercase font-medium">{label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Theme toggle */}
      <div className="p-1.5 pb-3">
        <button
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          title="Toggle theme"
          className="w-full flex flex-col items-center gap-1 py-2.5 px-1 rounded-md text-[hsl(var(--muted))] hover:text-[hsl(var(--foreground))] hover:bg-[hsl(var(--surface-raised))] transition-colors"
        >
          {theme === "dark" ? (
            <SunMedium size={16} strokeWidth={1.5} />
          ) : (
            <Moon size={16} strokeWidth={1.5} />
          )}
          <span className="text-[9px] tracking-wide uppercase font-medium">Theme</span>
        </button>
      </div>
    </aside>
  );
}
