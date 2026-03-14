"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { AlertCircle, ArrowLeft, Eye, Folder, MapPin, ScanSearch, Sparkles } from "lucide-react";
import { api, type AssetDetail } from "@/lib/api";
import { cn } from "@/lib/utils";

function formatBytes(n: number | null): string {
  if (n == null) return "—";
  if (n < 1024) return `${n} B`;
  if (n < 1024 ** 2) return `${(n / 1024).toFixed(1)} KB`;
  if (n < 1024 ** 3) return `${(n / 1024 ** 2).toFixed(1)} MB`;
  return `${(n / 1024 ** 3).toFixed(2)} GB`;
}

function formatDate(value: string | null | undefined) {
  if (!value) return "—";
  return new Date(value).toLocaleString();
}

function formatCost(value: number | null | undefined) {
  if (value == null) return "—";
  return value < 0.001 ? "< $0.001" : `$${value.toFixed(4)}`;
}

function confidenceLabel(value: number | null | undefined) {
  if (value == null) return null;
  if (value >= 0.9) return "high";
  if (value >= 0.75) return "med";
  return "low";
}

function analyzeFacts(asset: AssetDetail) {
  const counts = new Map<string, number>();
  for (const object of asset.objects) {
    const key = object.label.toLowerCase();
    counts.set(key, (counts.get(key) ?? 0) + (object.count ?? 1));
  }

  const personLabels = new Set(["person", "man", "woman", "child", "infant", "boy", "girl"]);
  const animalLabels = new Set(["cat", "dog", "bird", "horse", "cow", "sheep", "deer", "bear", "seal"]);
  const personCount = [...counts.entries()]
    .filter(([label]) => personLabels.has(label))
    .reduce((sum, [, count]) => sum + count, 0);
  const animals = [...counts.entries()].filter(([label]) => animalLabels.has(label));
  const strongestObjects = [...counts.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 4);
  const ocrLines = asset.ocr_text ? asset.ocr_text.split(/\n+/).filter(Boolean).length : 0;

  return { personCount, animals, strongestObjects, ocrLines };
}

export default function AssetDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [asset, setAsset] = useState<AssetDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [imgError, setImgError] = useState(false);

  useEffect(() => {
    if (!id) return;
    api.assets.detail(id)
      .then(setAsset)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return <div className="flex h-full items-center justify-center text-[12px] text-[hsl(var(--muted))]">Loading photo details...</div>;
  }

  if (error || !asset) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-3">
        <AlertCircle size={20} className="text-red-400" />
        <p className="text-[12px] text-[hsl(var(--muted-foreground))]">{error ?? "Asset not found"}</p>
        <Link href="/gallery" className="text-[11px] underline">Back to gallery</Link>
      </div>
    );
  }

  const thumbSrc = asset.large_thumbnail_url ?? asset.thumbnail_url ?? null;
  const folderPath = asset.canonical_path.split("/").slice(0, -1).join("/") || "/";
  const hasImageNotes = Boolean(
    asset.artistic_notes?.summary ||
    asset.artistic_notes?.composition ||
    asset.artistic_notes?.lighting ||
    asset.artistic_notes?.detail ||
    asset.artistic_notes?.resolution
  );
  const longSummary = [asset.summary, asset.scene?.description, asset.extraction_notes]
    .filter(Boolean)
    .filter((value, index, all) => all.indexOf(value) === index)
    .join(" ");
  const facts = analyzeFacts(asset);

  return (
    <div className="h-full overflow-auto px-5 pb-8 pt-5">
      <div className="mb-5 space-y-3">
        <Link href="/gallery" className="inline-flex items-center gap-2 text-[11px] uppercase tracking-[0.18em] text-[hsl(var(--muted))]">
          <ArrowLeft size={12} />
          Back to gallery
        </Link>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="space-y-2">
            <p className="text-[10px] uppercase tracking-[0.24em] text-[hsl(var(--muted))]">Photo details</p>
            <h2 className="font-display text-4xl leading-none">{asset.filename}</h2>
            <p className="max-w-3xl text-[14px] leading-relaxed text-[hsl(var(--muted-foreground))]">
              {longSummary || "No AI summary yet."}
            </p>
            {asset.extraction_run?.status === "failed" && asset.extraction_run.error_message && (
              <div className="max-w-3xl rounded-[1rem] border border-amber-300/40 bg-amber-300/12 px-3 py-2 text-[12px] text-amber-800 dark:text-amber-200">
                AI run failed: {asset.extraction_run.error_message}
              </div>
            )}
          </div>
          <div className="flex flex-wrap gap-2">
            <Pill>{asset.type}</Pill>
            {asset.tags.slice(0, 6).map((tag) => <Pill key={tag} tone="soft">{tag}</Pill>)}
          </div>
        </div>
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
        <main className="space-y-4">
          <section className="overflow-hidden rounded-[2rem] border border-[hsl(var(--border))] bg-[hsl(var(--surface))] shadow-[0_30px_120px_-80px_rgba(0,0,0,0.7)]">
            <div className="flex flex-wrap items-center gap-2 border-b border-[hsl(var(--border-subtle))] px-4 py-3">
              {asset.scene?.setting && <Pill tone="soft">{asset.scene.setting}</Pill>}
              {asset.scene?.time_of_day && <Pill tone="soft">{asset.scene.time_of_day}</Pill>}
              {asset.place_candidates[0]?.name && <Pill tone="soft">{asset.place_candidates[0].name}</Pill>}
              {asset.extraction_status && <Pill>{asset.extraction_status}</Pill>}
            </div>
            <div className="relative min-h-[55vh] bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.14),transparent_40%),linear-gradient(180deg,rgba(35,28,21,0.38),rgba(15,14,12,0.88))]">
              {thumbSrc && !imgError ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={thumbSrc}
                  alt={asset.filename}
                  onError={() => setImgError(true)}
                  className="h-full max-h-[78vh] w-full object-contain"
                />
              ) : (
                <div className="flex min-h-[55vh] flex-col items-center justify-center gap-3 text-[hsl(var(--muted))]">
                  <Eye size={32} strokeWidth={1} />
                  <p className="text-[11px]">No preview available</p>
                </div>
              )}
            </div>
          </section>

          <div className="grid gap-4 lg:grid-cols-2">
            {asset.summary || asset.scene?.description || asset.tags.length > 0 || asset.objects.length > 0 ? (
              <Panel title="AI summary" icon={<Sparkles size={14} />}>
                <div className="space-y-4">
                  <p className="text-[13px] leading-relaxed text-[hsl(var(--foreground))]">
                    {longSummary}
                  </p>
                  {asset.tag_details.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {asset.tag_details.map((tag) => (
                        <span
                          key={tag.label}
                          className="inline-flex items-center gap-1 rounded-full border border-[hsl(var(--border))] bg-[hsl(var(--surface-raised))] px-3 py-1 text-[10px] uppercase tracking-[0.16em]"
                        >
                          <span>{tag.label}</span>
                          {confidenceLabel(tag.confidence) ? (
                            <span className="text-[hsl(var(--muted))]">{confidenceLabel(tag.confidence)}</span>
                          ) : null}
                        </span>
                      ))}
                    </div>
                  )}
                  {hasImageNotes ? (
                    <div className="space-y-2 text-[12px] leading-relaxed text-[hsl(var(--muted-foreground))]">
                      {asset.artistic_notes?.summary ? <p>{asset.artistic_notes.summary}</p> : null}
                      {asset.artistic_notes?.composition ? <p><strong className="text-[hsl(var(--foreground))]">Composition:</strong> {asset.artistic_notes.composition}</p> : null}
                      {asset.artistic_notes?.lighting ? <p><strong className="text-[hsl(var(--foreground))]">Lighting:</strong> {asset.artistic_notes.lighting}</p> : null}
                      {asset.artistic_notes?.detail ? <p><strong className="text-[hsl(var(--foreground))]">Detail:</strong> {asset.artistic_notes.detail}</p> : null}
                      {asset.artistic_notes?.resolution ? <p><strong className="text-[hsl(var(--foreground))]">Resolution:</strong> {asset.artistic_notes.resolution}</p> : null}
                    </div>
                  ) : asset.extraction_run?.status === "done" ? (
                    <p className="text-[12px] text-[hsl(var(--muted-foreground))]">
                      This older AI run did not include image notes. Rerun extraction to add them.
                    </p>
                  ) : null}
                  {asset.objects.length > 0 && (
                    <div className="space-y-2">
                      {asset.objects.map((object, index) => (
                        <div key={`${object.label}-${object.count ?? 1}-${index}`} className="flex items-center justify-between gap-3 rounded-[1rem] bg-[hsl(var(--surface-raised))] px-3 py-2 text-[12px]">
                          <div className="space-y-1">
                            <span className="block">
                              {object.count && object.count > 1 ? `${object.label} x${object.count}` : object.label}
                              {object.color ? <span className="text-[hsl(var(--muted))]">{` · ${object.color}`}</span> : null}
                            </span>
                            {object.details.length > 0 ? (
                              <p className="text-[11px] text-[hsl(var(--muted-foreground))]">{object.details.join(", ")}</p>
                            ) : null}
                          </div>
                          <span className="shrink-0 text-[hsl(var(--muted))]">{object.confidence != null ? `${Math.round(object.confidence * 100)}%` : "—"}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </Panel>
            ) : (
              <Panel title="AI summary" icon={<Sparkles size={14} />}>
                <p className="text-[12px] text-[hsl(var(--muted-foreground))]">
                  No AI summary is available for this image yet.
                </p>
              </Panel>
            )}

            <Panel title="AI facts analysis" icon={<Sparkles size={14} />}>
              <div className="grid gap-3 sm:grid-cols-2">
                <FactBox label="People detected" value={String(facts.personCount)} />
                <FactBox label="Tag count" value={String(asset.tag_details.length || asset.tags.length)} />
                <FactBox label="Text lines" value={String(facts.ocrLines)} />
                <FactBox label="Place candidates" value={String(asset.place_candidates.length)} />
              </div>
              {facts.animals.length > 0 ? (
                <div className="mt-3 text-[12px] text-[hsl(var(--muted-foreground))]">
                  <strong className="text-[hsl(var(--foreground))]">Animals:</strong>{" "}
                  {facts.animals.map(([label, count]) => `${label} x${count}`).join(", ")}
                </div>
              ) : null}
              {facts.strongestObjects.length > 0 ? (
                <div className="mt-3 text-[12px] text-[hsl(var(--muted-foreground))]">
                  <strong className="text-[hsl(var(--foreground))]">Most frequent objects:</strong>{" "}
                  {facts.strongestObjects.map(([label, count]) => `${label} x${count}`).join(", ")}
                </div>
              ) : null}
            </Panel>

            <Panel title="Taken together" icon={<Folder size={14} />}>
              {asset.series ? (
                <div className="space-y-3">
                  <p className="text-[13px] text-[hsl(var(--foreground))]">{asset.series.label}</p>
                  <div className="space-y-1.5">
                    {asset.series.items.map((item) => (
                      <Link
                        key={item.id}
                        href={`/asset/${item.id}`}
                        className={cn(
                          "flex items-center justify-between rounded-[1rem] px-3 py-2 text-[11px] transition-colors hover:bg-[hsl(var(--surface-raised))]",
                          item.id === asset.id && "bg-[hsl(var(--surface-raised))]"
                        )}
                      >
                        <span className="font-mono">{item.filename}</span>
                        <span className="text-[hsl(var(--muted))]">{formatDate(item.captured_at)}</span>
                      </Link>
                    ))}
                  </div>
                </div>
              ) : (
                <p className="text-[12px] text-[hsl(var(--muted-foreground))]">This photo does not appear to be part of a close time sequence in the same folder.</p>
              )}
            </Panel>
          </div>
        </main>

        <aside className="space-y-4">
          <Panel title="Text found" icon={<ScanSearch size={14} />}>
            {asset.ocr_text ? (
              <pre className="max-h-[24rem] overflow-auto whitespace-pre-wrap rounded-[1.2rem] bg-[hsl(var(--surface-raised))] p-3 text-[11px] leading-relaxed text-[hsl(var(--foreground))]">
                {asset.ocr_text}
              </pre>
            ) : (
              <p className="text-[12px] text-[hsl(var(--muted-foreground))]">No text was saved for this image.</p>
            )}
          </Panel>

          <Panel title="Capture info" icon={<MapPin size={14} />}>
            <InfoRow label="Taken" value={formatDate(asset.temporal?.best_timestamp)} />
            <InfoRow label="Date source" value={asset.temporal?.source ?? "—"} />
            <InfoRow label="File size" value={formatBytes(asset.file_size_bytes)} />
            <InfoRow label="Dimensions" value={asset.media_info?.width && asset.media_info?.height ? `${asset.media_info.width} x ${asset.media_info.height}` : "—"} />
            <InfoRow label="Place" value={asset.place_candidates[0]?.name ?? "—"} />
            <InfoRow label="GPS" value={asset.location?.lat != null ? `${asset.location.lat.toFixed(5)}, ${asset.location.lon?.toFixed(5) ?? "—"}` : "—"} />
            <InfoRow label="Camera" value={[asset.media_info?.camera_make, asset.media_info?.camera_model].filter(Boolean).join(" ") || "—"} />
            <InfoRow label="Lens" value={asset.media_info?.lens_model ?? "—"} />
            <InfoRow label="Path" value={folderPath} mono />
          </Panel>

          <Panel title="AI run" icon={<Sparkles size={14} />}>
            <InfoRow label="Status" value={asset.extraction_run?.status ?? "—"} />
            <InfoRow label="Model" value={asset.extraction_run?.model_name ?? "—"} />
            <InfoRow label="Started" value={formatDate(asset.extraction_run?.started_at)} />
            <InfoRow label="Finished" value={formatDate(asset.extraction_run?.finished_at)} />
            <InfoRow label="Tokens" value={asset.extraction_run ? `${asset.extraction_run.tokens_in ?? 0} in / ${asset.extraction_run.tokens_out ?? 0} out` : "—"} />
            <InfoRow label="Cost" value={formatCost(asset.extraction_run?.cost_usd)} />
            {asset.extraction_run?.debug_stage ? (
              <InfoRow label="Debug stage" value={asset.extraction_run.debug_stage} />
            ) : null}
            {asset.extraction_run?.error_message ? (
              <div className="mt-3 rounded-[1rem] bg-[hsl(var(--surface-raised))] p-3 text-[12px] text-[hsl(var(--muted-foreground))]">
                {asset.extraction_run.error_message}
              </div>
            ) : null}
            {asset.extraction_run?.debug_excerpt ? (
              <div className="mt-3">
                <p className="mb-2 text-[10px] uppercase tracking-[0.16em] text-[hsl(var(--muted))]">Raw response excerpt</p>
                <pre className="max-h-[18rem] overflow-auto whitespace-pre-wrap rounded-[1rem] bg-[hsl(var(--surface-raised))] p-3 text-[11px] leading-relaxed text-[hsl(var(--foreground))]">
                  {asset.extraction_run.debug_excerpt}
                </pre>
              </div>
            ) : null}
          </Panel>
        </aside>
      </div>
    </div>
  );
}

function Panel({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <section className="rounded-[1.6rem] border border-[hsl(var(--border))] bg-[hsl(var(--surface))] p-4 shadow-[0_24px_80px_-66px_rgba(0,0,0,0.45)]">
      <div className="mb-3 flex items-center gap-2 text-[11px] uppercase tracking-[0.18em] text-[hsl(var(--muted))]">
        {icon}
        <span>{title}</span>
      </div>
      {children}
    </section>
  );
}

function InfoRow({ label, value, mono = false }: { label: string; value: React.ReactNode; mono?: boolean }) {
  return (
    <div className="flex items-start justify-between gap-3 border-b border-[hsl(var(--border-subtle))] py-2 last:border-b-0">
      <span className="text-[11px] uppercase tracking-[0.14em] text-[hsl(var(--muted))]">{label}</span>
      <span className={cn("max-w-[65%] text-right text-[12px] text-[hsl(var(--foreground))]", mono && "font-mono text-[11px] break-all")}>{value}</span>
    </div>
  );
}

function FactBox({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[1rem] bg-[hsl(var(--surface-raised))] px-3 py-2">
      <p className="text-[10px] uppercase tracking-[0.16em] text-[hsl(var(--muted))]">{label}</p>
      <p className="mt-1 text-[18px] font-medium leading-none">{value}</p>
    </div>
  );
}

function Pill({ children, tone = "default" }: { children: React.ReactNode; tone?: "default" | "soft" }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-3 py-1 text-[10px] uppercase tracking-[0.18em]",
        tone === "soft" ? "border-[hsl(var(--border))] bg-[hsl(var(--surface-raised))]" : "border-[hsl(var(--border))]"
      )}
    >
      {children}
    </span>
  );
}
