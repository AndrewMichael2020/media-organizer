"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowRight, Clock3, MapPin, Sparkles, TriangleAlert } from "lucide-react";
import { api, type ReviewQueueResponse } from "@/lib/api";
import { cn } from "@/lib/utils";

export default function ReviewPage() {
  const [data, setData] = useState<ReviewQueueResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.assets.reviewQueues()
      .then(setData)
      .catch(() => setError("Could not load review queues from the local API."))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="flex h-full items-center justify-center text-[12px] text-[hsl(var(--muted))]">Loading review desk...</div>;
  }

  if (error || !data) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-3">
        <TriangleAlert size={18} className="text-red-400" />
        <p className="text-[12px] text-[hsl(var(--muted-foreground))]">{error ?? "Review data unavailable."}</p>
      </div>
    );
  }

  const total = data.queues.reduce((sum, queue) => sum + queue.count, 0);

  return (
    <div className="h-full overflow-auto px-5 pb-8 pt-5">
      <section className="rounded-[1.4rem] border border-[hsl(var(--border))] bg-[linear-gradient(135deg,rgba(103,77,41,0.12),transparent_45%),hsl(var(--surface))] p-4 shadow-[0_30px_120px_-90px_rgba(0,0,0,0.75)]">
        <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_280px]">
          <div className="space-y-3">
            <p className="text-[10px] uppercase tracking-[0.28em] text-[hsl(var(--muted))]">Operational Review</p>
            <h2 className="font-display text-4xl leading-none">Review desk</h2>
            <p className="max-w-2xl text-[13px] leading-relaxed text-[hsl(var(--muted-foreground))]">
              This desk groups assets by weak AI results, date conflicts, and missing place context so you can improve
              the archive where it matters most.
            </p>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-1">
            <SummaryCard icon={<Sparkles size={16} />} label="Total queued" value={String(total)} />
            <SummaryCard icon={<Clock3 size={16} />} label="Active queues" value={String(data.queues.filter((queue) => queue.count > 0).length)} />
          </div>
        </div>
      </section>

      <div className="mt-5 grid gap-5">
        {data.queues.map((queue) => (
          <section key={queue.name} className="rounded-[1.4rem] border border-[hsl(var(--border))] bg-[hsl(var(--surface))] p-4 shadow-[0_24px_80px_-66px_rgba(0,0,0,0.45)]">
            <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
              <div>
                <div className="flex items-center gap-2">
                  <QueueTone tone={queue.name} />
                  <h3 className="font-display text-3xl leading-none">{queue.label}</h3>
                </div>
                <p className="mt-2 max-w-2xl text-[13px] leading-relaxed text-[hsl(var(--muted-foreground))]">{queue.description}</p>
              </div>
              <div className="rounded-[1.2rem] bg-[hsl(var(--surface-raised))] px-4 py-3 text-right">
                <p className="text-[10px] uppercase tracking-[0.18em] text-[hsl(var(--muted))]">Queue size</p>
                <p className="mt-1 font-display text-3xl leading-none">{queue.count}</p>
              </div>
            </div>

            {queue.items.length === 0 ? (
              <div className="rounded-[1.2rem] border border-dashed border-[hsl(var(--border))] p-4 text-[12px] text-[hsl(var(--muted-foreground))]">
                Nothing currently matches this queue.
              </div>
            ) : (
              <div className="overflow-hidden rounded-[1.2rem] border border-[hsl(var(--border))]">
                {queue.items.map((asset) => (
                  <Link
                    key={asset.id}
                    href={`/asset/${asset.id}`}
                    className="grid grid-cols-[minmax(0,1.3fr)_150px_150px_120px] items-center gap-3 border-b border-[hsl(var(--border-subtle))] bg-[hsl(var(--surface-raised))] px-4 py-3 text-[12px] transition-colors hover:bg-[hsl(var(--surface))] last:border-b-0"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-[13px] font-medium">{asset.filename}</p>
                      <p className="mt-1 truncate text-[11px] text-[hsl(var(--muted-foreground))]">{asset.summary ?? "No summary yet."}</p>
                    </div>
                    <div className="text-[11px] text-[hsl(var(--muted-foreground))]">
                      {asset.captured_at ? new Date(asset.captured_at).toLocaleDateString() : "No date"}
                    </div>
                    <div className="text-[11px] text-[hsl(var(--muted-foreground))]">
                      {asset.place_label ? (
                        <span className="inline-flex items-center gap-1">
                          <MapPin size={10} />
                          {asset.place_label}
                        </span>
                      ) : "No place"}
                    </div>
                    <div className="flex items-center justify-between gap-2">
                      {asset.review_bucket ? <Tag tone="warning">{asset.review_bucket.replace(/-/g, " ")}</Tag> : <span />}
                      <span className="inline-flex items-center gap-2 text-[11px] uppercase tracking-[0.16em] text-[hsl(var(--foreground))]">
                        Inspect
                        <ArrowRight size={12} />
                      </span>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </section>
        ))}
      </div>
    </div>
  );
}

function SummaryCard({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="rounded-[1.25rem] border border-[hsl(var(--border))] bg-[hsl(var(--surface))]/90 p-4">
      <div className="flex items-center justify-between text-[hsl(var(--muted))]">
        {icon}
        <span className="text-[10px] uppercase tracking-[0.18em]">{label}</span>
      </div>
      <p className="mt-3 font-display text-4xl leading-none">{value}</p>
    </div>
  );
}

function Tag({ children, tone = "default" }: { children: React.ReactNode; tone?: "default" | "warning" }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2 py-1 text-[10px] uppercase tracking-[0.14em]",
        tone === "warning"
          ? "border-amber-300/40 bg-amber-300/12 text-amber-700 dark:text-amber-300"
          : "border-[hsl(var(--border))] bg-[hsl(var(--surface))] text-[hsl(var(--muted))]"
      )}
    >
      {children}
    </span>
  );
}

function QueueTone({ tone }: { tone: string }) {
  return (
    <span
      className={cn(
        "inline-block h-3 w-3 rounded-full",
        tone === "needs-extraction" && "bg-sky-500",
        tone === "timestamp-conflict" && "bg-amber-500",
        tone === "low-confidence" && "bg-rose-500",
        tone === "location-unverified" && "bg-emerald-500"
      )}
    />
  );
}
