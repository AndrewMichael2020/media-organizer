import Link from "next/link";
import { Copy, Film, Folder, ScanSearch, TriangleAlert } from "lucide-react";
import { cn } from "@/lib/utils";
import type { AssetListItem } from "@/lib/api";

export function AssetCard({ asset, compact = false }: { asset: AssetListItem; compact?: boolean }) {
  const paddingPct = asset.width && asset.height ? `${(asset.height / asset.width) * 100}%` : "75%";

  return (
    <Link href={`/asset/${asset.id}`} className="group relative mb-3 block break-inside-avoid">
      <div
        className="relative overflow-hidden rounded-[1.4rem] border border-[hsl(var(--border-subtle))] bg-[hsl(var(--surface-raised))] shadow-[0_24px_60px_-40px_rgba(0,0,0,0.42)] transition-all duration-300 group-hover:-translate-y-1 group-hover:border-[hsl(var(--border-strong))]"
        style={{ paddingBottom: paddingPct }}
      >
        {asset.thumbnail_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={asset.thumbnail_url}
            alt={asset.filename}
            className="absolute inset-0 h-full w-full object-cover transition-transform duration-500 group-hover:scale-[1.02]"
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center text-[hsl(var(--muted))]">No preview</div>
        )}

        <div className="absolute inset-0 bg-[linear-gradient(to_top,rgba(10,10,10,0.92),rgba(10,10,10,0.18)_44%,rgba(10,10,10,0.03)_75%)]" />

        <div className="absolute left-3 top-3 flex flex-wrap gap-1.5">
          {asset.review_bucket && (
            <Badge tone="warning">
              <TriangleAlert size={10} />
              {asset.review_bucket.replace(/-/g, " ")}
            </Badge>
          )}
          {asset.confidence_label && <Badge>{asset.confidence_label}</Badge>}
        </div>

        <div className="absolute right-3 top-3 flex gap-1.5">
          {asset.type === "video" && <IconBubble><Film size={10} /></IconBubble>}
          {asset.is_duplicate && <IconBubble><Copy size={10} /></IconBubble>}
        </div>

        <div className="absolute inset-x-0 bottom-0 p-3">
          <div className="rounded-[1.1rem] border border-white/12 bg-black/42 p-3 text-white backdrop-blur-md">
            <div className="mb-2 flex items-center gap-2 text-[10px] uppercase tracking-[0.22em] text-white/72">
              <span>{asset.type}</span>
              {asset.captured_at && <span>{new Date(asset.captured_at).toLocaleDateString()}</span>}
            </div>
            {!compact && <p className="truncate text-[13px] font-medium">{asset.filename}</p>}
            {!compact && asset.summary && (
              <p className="mt-2 line-clamp-2 text-[12px] leading-snug text-white/84">{asset.summary}</p>
            )}
            <div className="mt-2 flex flex-wrap gap-1.5">
              {asset.tags.slice(0, compact ? 3 : 6).map((tag) => (
                <span key={tag} className="rounded-full border border-white/12 bg-white/10 px-2 py-0.5 text-[10px] text-white/82">
                  {tag}
                </span>
              ))}
            </div>
            <div className="mt-2 flex flex-wrap gap-1.5 text-[10px] text-white/74">
              {asset.has_ocr && (
                <MetaPill>
                  <ScanSearch size={10} />
                  Text
                </MetaPill>
              )}
              {asset.folder_path && (
                <MetaPill>
                  <Folder size={10} />
                  <span className="max-w-[12rem] truncate">{asset.folder_path}</span>
                </MetaPill>
              )}
            </div>
          </div>
        </div>
      </div>
    </Link>
  );
}

function IconBubble({ children }: { children: React.ReactNode }) {
  return <span className="rounded-full bg-black/45 p-1 text-white backdrop-blur-sm">{children}</span>;
}

function MetaPill({ children }: { children: React.ReactNode }) {
  return <span className="inline-flex items-center gap-1 rounded-full border border-white/12 bg-white/8 px-2 py-0.5">{children}</span>;
}

function Badge({ children, tone = "muted" }: { children: React.ReactNode; tone?: "muted" | "warning" }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2 py-1 text-[10px] uppercase tracking-[0.18em] backdrop-blur-sm",
        tone === "warning" ? "border-amber-300/30 bg-amber-300/14 text-amber-50" : "border-white/16 bg-black/25 text-white/85"
      )}
    >
      {children}
    </span>
  );
}
