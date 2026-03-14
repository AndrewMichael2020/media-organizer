import Link from "next/link";
import { Film, Copy } from "lucide-react";
import { cn } from "@/lib/utils";
import type { AssetListItem } from "@/lib/api";

export function AssetCard({ asset, compact = false }: { asset: AssetListItem; compact?: boolean }) {
  const paddingPct =
    asset.width && asset.height
      ? `${(asset.height / asset.width) * 100}%`
      : "75%";

  // thumbnail_url is "/api/assets/{id}/thumbnail" — serve through Next.js proxy
  const thumbSrc = asset.thumbnail_url ?? null;

  return (
    <Link href={`/asset/${asset.id}`} className="break-inside-avoid mb-1.5 group cursor-pointer relative block">
      {/* Thumbnail area */}
      <div
        className="relative w-full overflow-hidden bg-[hsl(var(--surface-raised))] rounded-sm border border-[hsl(var(--border-subtle))] group-hover:border-[hsl(var(--border))] transition-colors"
        style={{ paddingBottom: paddingPct }}
      >
        {thumbSrc ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={thumbSrc}
            alt={asset.filename}
            className="absolute inset-0 w-full h-full object-cover"
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-[10px] text-[hsl(var(--muted))] font-mono tracking-wider opacity-40">
              {asset.type === "video" ? "VID" : "IMG"}
            </span>
          </div>
        )}

        {/* Hover overlay */}
        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors" />

        {/* Top-right badges */}
        <div className="absolute top-1 right-1 flex gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
          {asset.type === "video" && (
            <span className="p-0.5 rounded bg-black/60 text-white">
              <Film size={9} />
            </span>
          )}
          {asset.is_duplicate && (
            <span className="p-0.5 rounded bg-amber-500/80 text-white">
              <Copy size={9} />
            </span>
          )}
        </div>

        {/* Bottom flag strip */}
        {(asset.has_ocr || asset.has_gps) && (
          <div className="absolute bottom-0 left-0 right-0 flex gap-0.5 p-1 opacity-0 group-hover:opacity-100 transition-opacity">
            {asset.has_ocr && <FlagDot color="blue" />}
            {asset.has_gps && <FlagDot color="green" />}
          </div>
        )}
      </div>

      {/* Filename — hidden in compact (zoomed-out) mode */}
      {!compact && (
        <p className="mt-0.5 px-0.5 text-[10px] text-[hsl(var(--muted))] font-mono truncate leading-tight">
          {asset.filename}
        </p>
      )}
    </Link>
  );
}

function FlagDot({ color }: { color: "blue" | "green" }) {
  return (
    <span
      className={cn(
        "w-1.5 h-1.5 rounded-full",
        color === "blue" ? "bg-blue-400" : "bg-emerald-400"
      )}
    />
  );
}
