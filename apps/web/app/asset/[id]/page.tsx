"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { AlertCircle, ArrowLeft, Eye, Folder, MapPin, Pencil, Save, ScanSearch, Sparkles, X } from "lucide-react";
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

function displayValue(value: unknown) {
  if (value == null || value === "") return "unknown";
  return String(value).replace(/_/g, " ");
}

function displayExposure(value: unknown) {
  const text = displayValue(value);
  if (text === "high") return "exposed";
  if (text === "extreme") return "highly exposed";
  return text;
}

function summaryBlocks(text: string | null | undefined) {
  if (!text) return [];
  return text
    .split(/(?=Archive place note:|Location context:|Archive note:|Operational context:)/g)
    .map((part) => part.trim())
    .filter(Boolean)
    .filter((part) => !/^(Archive place note:|Location context:|Archive note:|Operational context:)\s*$/i.test(part))
    .filter((value, index, all) => all.indexOf(value) === index);
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
  const analysis = (asset.analysis ?? {}) as Record<string, unknown>;
  const peopleOverview = (analysis.people_overview ?? {}) as Record<string, unknown>;
  const objectsRaw = Array.isArray(analysis.objects) ? analysis.objects : [];
  const highSignificanceObjects = objectsRaw.filter(
    (item) => item && typeof item === "object" && (item as Record<string, unknown>).significance === "high"
  ).length;

  return {
    personCount: typeof peopleOverview.people_count_visible === "number" ? Number(peopleOverview.people_count_visible) : personCount,
    animals,
    strongestObjects,
    ocrLines,
    highSignificanceObjects,
    peopleOverview,
    analysis,
  };
}

export default function AssetDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [asset, setAsset] = useState<AssetDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [imgError, setImgError] = useState(false);
  const [editingCapture, setEditingCapture] = useState(false);
  const [savingCapture, setSavingCapture] = useState(false);
  const [captureError, setCaptureError] = useState<string | null>(null);
  const [captureForm, setCaptureForm] = useState({ place: "", gps_coords: "", comments: "" });

  useEffect(() => {
    if (!id) return;
    api.assets.detail(id)
      .then(setAsset)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    if (!asset) return;
    setCaptureForm({
      place: asset.user_context?.place ?? asset.place_candidates[0]?.name ?? "",
      gps_coords: asset.user_context?.gps_coords ?? (asset.location?.lat != null ? `${asset.location.lat.toFixed(5)}, ${asset.location.lon?.toFixed(5) ?? ""}` : ""),
      comments: asset.user_context?.comments ?? "",
    });
  }, [asset]);

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
  const longSummaryBlocks = summaryBlocks(longSummary);
  const facts = analyzeFacts(asset);
  const displayPlace = asset.user_context?.place ?? asset.place_candidates[0]?.name ?? "—";
  const displayGps = asset.user_context?.gps_coords ?? (asset.location?.lat != null ? `${asset.location.lat.toFixed(5)}, ${asset.location.lon?.toFixed(5) ?? "—"}` : "—");
  const displayComments = asset.user_context?.comments ?? "—";
  const people = Array.isArray((facts.analysis as Record<string, unknown>).people)
    ? ((facts.analysis as Record<string, unknown>).people as Array<Record<string, unknown>>)
    : [];
  const setting = ((facts.analysis as Record<string, unknown>).setting_analysis ?? {}) as Record<string, unknown>;
  const operational = ((facts.analysis as Record<string, unknown>).operational_context ?? {}) as Record<string, unknown>;
  const landscape = ((facts.analysis as Record<string, unknown>).landscape_analysis ?? {}) as Record<string, unknown>;
  const sensitivity = ((facts.analysis as Record<string, unknown>).sensitivity_review ?? {}) as Record<string, unknown>;
  const analysisObjects = Array.isArray((facts.analysis as Record<string, unknown>).objects)
    ? ((facts.analysis as Record<string, unknown>).objects as Array<Record<string, unknown>>)
    : [];

  async function saveCaptureInfo() {
    if (!asset) return;
    setSavingCapture(true);
    setCaptureError(null);
    try {
      const userContext = await api.assets.updateUserContext(asset.id, {
        place: captureForm.place.trim() || null,
        gps_coords: captureForm.gps_coords.trim() || null,
        comments: captureForm.comments.trim() || null,
      });
      setAsset((prev) => prev ? { ...prev, user_context: userContext } : prev);
      setEditingCapture(false);
    } catch (err) {
      setCaptureError(err instanceof Error ? err.message : "Failed to save capture info");
    } finally {
      setSavingCapture(false);
    }
  }

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
            <div className="max-w-3xl space-y-1.5 text-[14px] leading-relaxed text-[hsl(var(--muted-foreground))]">
              {(longSummaryBlocks.length > 0 ? longSummaryBlocks : ["No AI summary yet."]).map((block, index) => (
                <p key={`header-summary-${index}`}>{block}</p>
              ))}
            </div>
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
                  <div className="space-y-2 text-[13px] leading-relaxed text-[hsl(var(--foreground))]">
                    {longSummaryBlocks.map((block, index) => (
                      <p key={`summary-block-${index}`}>{block}</p>
                    ))}
                  </div>
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
                <FactBox label="High-signal objects" value={String(facts.highSignificanceObjects)} />
                <FactBox label="Dominant activity" value={String(facts.peopleOverview.dominant_activity ?? "unknown")} />
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

            {(people.length > 0 || setting.confidence || operational.confidence || landscape.confidence) ? (
              <Panel title="Operational reading" icon={<Sparkles size={14} />} className="lg:col-span-2">
                <div className="space-y-4 text-[12px] leading-relaxed text-[hsl(var(--muted-foreground))]">
                  {people.length > 0 ? (
                    <div className="space-y-2">
                      <p className="text-[11px] uppercase tracking-[0.16em] text-[hsl(var(--muted))]">People</p>
                      {people.slice(0, 6).map((person, index) => {
                        const roles = Array.isArray(person.role_hypotheses) ? (person.role_hypotheses as Array<Record<string, unknown>>) : [];
                        const topRole = roles[0];
                        const clothing = Array.isArray(person.clothing_items) ? person.clothing_items.join(", ") : "";
                        const gear = Array.isArray(person.carried_or_worn_gear) ? person.carried_or_worn_gear.join(", ") : "";
                        return (
                          <div key={`person-${index}`} className="rounded-[1rem] bg-[hsl(var(--surface-raised))] px-3 py-2">
                            <p className="text-[hsl(var(--foreground))]">
                              Person {index + 1}: {String(topRole?.label ?? "unknown")}
                              {topRole?.confidence ? <span className="text-[hsl(var(--muted))]">{` · ${String(topRole.confidence)}`}</span> : null}
                            </p>
                            {clothing ? <p>Clothing: {clothing}</p> : null}
                            {gear ? <p>Gear: {gear}</p> : null}
                          </div>
                        );
                      })}
                    </div>
                  ) : null}

                  <div className="grid gap-3 md:grid-cols-2">
                    <div className="rounded-[1rem] bg-[hsl(var(--surface-raised))] px-3 py-2">
                      <p className="mb-1 text-[11px] uppercase tracking-[0.16em] text-[hsl(var(--muted))]">Setting</p>
                      <p>Public/private: {displayValue(setting.public_private)}</p>
                      <p>Use: {displayValue(setting.institutional_commercial_leisure)}</p>
                      <p>Economic signal: {displayValue(setting.built_environment_economic_signal)}</p>
                      {Array.isArray(setting.organization_text_cues) && setting.organization_text_cues.length > 0 ? <p>Text cues: {setting.organization_text_cues.join(", ")}</p> : null}
                      {Array.isArray(setting.visible_logos) && setting.visible_logos.length > 0 ? <p>Logos: {setting.visible_logos.join(", ")}</p> : null}
                    </div>
                    <div className="rounded-[1rem] bg-[hsl(var(--surface-raised))] px-3 py-2">
                      <p className="mb-1 text-[11px] uppercase tracking-[0.16em] text-[hsl(var(--muted))]">Operational</p>
                      <p>Security presence: {displayValue(operational.security_presence)}</p>
                      <p>Mobility: {displayValue(operational.mobility_context)}</p>
                      <p>Infrastructure: {displayValue(operational.infrastructure_status)}</p>
                      {Array.isArray(operational.scene_function_hypotheses) && operational.scene_function_hypotheses.length > 0 ? (
                        <p>Scene function: {operational.scene_function_hypotheses.map((item) => String((item as Record<string, unknown>).label ?? "unknown").replace(/_/g, " ")).join(", ")}</p>
                      ) : null}
                      {Array.isArray(operational.damage_indicators) && operational.damage_indicators.length > 0 ? <p>Damage: {operational.damage_indicators.join(", ")}</p> : null}
                      {Array.isArray(operational.threat_indicators) && operational.threat_indicators.length > 0 ? <p>Threat cues: {operational.threat_indicators.join(", ")}</p> : null}
                    </div>
                    <div className="rounded-[1rem] bg-[hsl(var(--surface-raised))] px-3 py-2">
                      <p className="mb-1 text-[11px] uppercase tracking-[0.16em] text-[hsl(var(--muted))]">Landscape</p>
                      <p>Terrain: {displayValue(landscape.terrain_type)}</p>
                      <p>Slope: {displayValue(landscape.slope_character)}</p>
                      <p>Exposure: {displayExposure(landscape.exposure_level)}</p>
                      <p>Visibility: {displayValue(landscape.weather_visibility_cues)}</p>
                    </div>
                    <div className="rounded-[1rem] bg-[hsl(var(--surface-raised))] px-3 py-2">
                      <p className="mb-1 text-[11px] uppercase tracking-[0.16em] text-[hsl(var(--muted))]">Sensitivity</p>
                      <p>Severity: {displayValue(sensitivity.severity ?? "low")}</p>
                      {Array.isArray(sensitivity.flags) && sensitivity.flags.length > 0 ? <p>Flags: {sensitivity.flags.join(", ")}</p> : null}
                      {Array.isArray(sensitivity.reasons) && sensitivity.reasons.length > 0 ? <p>Reasons: {sensitivity.reasons.join(", ")}</p> : null}
                    </div>
                  </div>
                  {analysisObjects.length > 0 ? (
                    <div className="rounded-[1rem] bg-[hsl(var(--surface-raised))] px-3 py-2">
                      <p className="mb-2 text-[11px] uppercase tracking-[0.16em] text-[hsl(var(--muted))]">High-signal objects</p>
                      <div className="space-y-2">
                        {analysisObjects.slice(0, 8).map((item, index) => {
                          const object = item as Record<string, unknown>;
                          const evidence = Array.isArray(object.evidence) ? object.evidence.map((entry) => String(entry)) : [];
                          return (
                            <div key={`analysis-object-${index}`} className="text-[12px] text-[hsl(var(--foreground))]">
                              <p>
                                {displayValue(object.object_label)}
                                {object.count_estimate ? ` x${String(object.count_estimate)}` : ""}
                                {object.significance ? <span className="text-[hsl(var(--muted))]">{` · ${displayValue(object.significance)}`}</span> : null}
                              </p>
                              {evidence.length > 0 ? <p className="text-[hsl(var(--muted-foreground))]">{evidence.join(", ")}</p> : null}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  ) : null}
                </div>
              </Panel>
            ) : null}

            {asset.location_meta ? (
              <Panel title="Location meta" icon={<MapPin size={14} />} className="lg:col-span-2">
                <div className="grid gap-3 md:grid-cols-2">
                  <div className="rounded-[1rem] bg-[hsl(var(--surface-raised))] px-3 py-2">
                    <p className="mb-1 text-[11px] uppercase tracking-[0.16em] text-[hsl(var(--muted))]">Candidate place</p>
                    <p className="break-words text-[hsl(var(--foreground))]">{asset.location_meta.place_name_candidate ?? "—"}</p>
                  </div>
                  <div className="rounded-[1rem] bg-[hsl(var(--surface-raised))] px-3 py-2">
                    <p className="mb-1 text-[11px] uppercase tracking-[0.16em] text-[hsl(var(--muted))]">Nearest city</p>
                    <p className="break-words text-[hsl(var(--foreground))]">{asset.location_meta.nearest_city_candidate ?? "—"}</p>
                  </div>
                  <div className="rounded-[1rem] bg-[hsl(var(--surface-raised))] px-3 py-2">
                    <p className="mb-1 text-[11px] uppercase tracking-[0.16em] text-[hsl(var(--muted))]">Province or state</p>
                    <p className="break-words text-[hsl(var(--foreground))]">{asset.location_meta.province_or_state_candidate ?? "—"}</p>
                  </div>
                  <div className="rounded-[1rem] bg-[hsl(var(--surface-raised))] px-3 py-2">
                    <p className="mb-1 text-[11px] uppercase tracking-[0.16em] text-[hsl(var(--muted))]">Country</p>
                    <p className="break-words text-[hsl(var(--foreground))]">{asset.location_meta.country_candidate ?? "—"}</p>
                  </div>
                </div>
                <div className="mt-3 rounded-[1rem] bg-[hsl(var(--surface-raised))] px-3 py-2">
                  <p className="mb-1 text-[11px] uppercase tracking-[0.16em] text-[hsl(var(--muted))]">Confidence</p>
                  <p className="break-words text-[hsl(var(--foreground))]">{displayValue(asset.location_meta.location_confidence)}</p>
                </div>
                {asset.location_meta.location_evidence.length > 0 ? (
                  <div className="mt-3 rounded-[1rem] bg-[hsl(var(--surface-raised))] px-3 py-2">
                    <p className="mb-2 text-[11px] uppercase tracking-[0.16em] text-[hsl(var(--muted))]">Evidence</p>
                    <div className="space-y-1 text-[12px] leading-relaxed text-[hsl(var(--foreground))]">
                      {asset.location_meta.location_evidence.map((item, index) => (
                        <p key={`location-evidence-${index}`} className="break-words">{item}</p>
                      ))}
                    </div>
                  </div>
                ) : null}
              </Panel>
            ) : null}

            <Panel title="Taken together" icon={<Folder size={14} />} className="lg:col-span-2">
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

          <Panel
            title="Capture info"
            icon={<MapPin size={14} />}
            actions={editingCapture ? (
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setEditingCapture(false);
                    setCaptureError(null);
                    setCaptureForm({
                      place: asset.user_context?.place ?? asset.place_candidates[0]?.name ?? "",
                      gps_coords: asset.user_context?.gps_coords ?? (asset.location?.lat != null ? `${asset.location.lat.toFixed(5)}, ${asset.location.lon?.toFixed(5) ?? ""}` : ""),
                      comments: asset.user_context?.comments ?? "",
                    });
                  }}
                  className="inline-flex items-center gap-1 rounded-full border border-[hsl(var(--border))] px-3 py-1 text-[10px] uppercase tracking-[0.16em]"
                >
                  <X size={12} />
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={saveCaptureInfo}
                  disabled={savingCapture}
                  className="inline-flex items-center gap-1 rounded-full border border-[hsl(var(--border))] bg-[hsl(var(--surface-raised))] px-3 py-1 text-[10px] uppercase tracking-[0.16em] disabled:opacity-60"
                >
                  <Save size={12} />
                  {savingCapture ? "Saving" : "Save"}
                </button>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => setEditingCapture(true)}
                className="inline-flex items-center gap-1 rounded-full border border-[hsl(var(--border))] px-3 py-1 text-[10px] uppercase tracking-[0.16em]"
              >
                <Pencil size={12} />
                Edit
              </button>
            )}
          >
            <InfoRow label="Taken" value={formatDate(asset.temporal?.best_timestamp)} />
            <InfoRow label="Date source" value={asset.temporal?.source ?? "—"} />
            <InfoRow label="File size" value={formatBytes(asset.file_size_bytes)} />
            <InfoRow label="Dimensions" value={asset.media_info?.width && asset.media_info?.height ? `${asset.media_info.width} x ${asset.media_info.height}` : "—"} />
            {editingCapture ? (
              <>
                <FieldRow
                  label="Place"
                  value={captureForm.place}
                  onChange={(value) => setCaptureForm((prev) => ({ ...prev, place: value }))}
                  placeholder="Add place context for the next AI run"
                />
                <FieldRow
                  label="GPS"
                  value={captureForm.gps_coords}
                  onChange={(value) => setCaptureForm((prev) => ({ ...prev, gps_coords: value }))}
                  placeholder="48.14573, 11.58769"
                />
                <TextAreaRow
                  label="Comments"
                  value={captureForm.comments}
                  onChange={(value) => setCaptureForm((prev) => ({ ...prev, comments: value }))}
                  placeholder="Add archive notes or scene context for the next AI run"
                />
              </>
            ) : (
              <>
                <InfoRow label="Place" value={displayPlace} />
                <InfoRow label="GPS" value={displayGps} />
                <InfoRow label="Comments" value={displayComments} />
              </>
            )}
            <InfoRow label="Camera" value={[asset.media_info?.camera_make, asset.media_info?.camera_model].filter(Boolean).join(" ") || "—"} />
            <InfoRow label="Lens" value={asset.media_info?.lens_model ?? "—"} />
            <InfoRow label="Path" value={folderPath} mono />
            {captureError ? (
              <div className="mt-3 rounded-[1rem] bg-[hsl(var(--surface-raised))] p-3 text-[12px] text-red-500">
                {captureError}
              </div>
            ) : null}
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

function Panel({ title, icon, children, className, actions }: { title: string; icon: React.ReactNode; children: React.ReactNode; className?: string; actions?: React.ReactNode }) {
  return (
    <section className={cn("rounded-[1.6rem] border border-[hsl(var(--border))] bg-[hsl(var(--surface))] p-4 shadow-[0_24px_80px_-66px_rgba(0,0,0,0.45)]", className)}>
      <div className="mb-3 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-[11px] uppercase tracking-[0.18em] text-[hsl(var(--muted))]">
          {icon}
          <span>{title}</span>
        </div>
        {actions}
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

function FieldRow({ label, value, onChange, placeholder }: { label: string; value: string; onChange: (value: string) => void; placeholder?: string }) {
  return (
    <div className="flex items-start justify-between gap-3 border-b border-[hsl(var(--border-subtle))] py-2">
      <span className="pt-2 text-[11px] uppercase tracking-[0.14em] text-[hsl(var(--muted))]">{label}</span>
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        className="w-[65%] rounded-[0.9rem] border border-[hsl(var(--border))] bg-[hsl(var(--surface-raised))] px-3 py-2 text-right text-[12px] text-[hsl(var(--foreground))] outline-none"
      />
    </div>
  );
}

function TextAreaRow({ label, value, onChange, placeholder }: { label: string; value: string; onChange: (value: string) => void; placeholder?: string }) {
  return (
    <div className="flex items-start justify-between gap-3 border-b border-[hsl(var(--border-subtle))] py-2">
      <span className="pt-2 text-[11px] uppercase tracking-[0.14em] text-[hsl(var(--muted))]">{label}</span>
      <textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        rows={4}
        className="w-[65%] resize-y rounded-[0.9rem] border border-[hsl(var(--border))] bg-[hsl(var(--surface-raised))] px-3 py-2 text-[12px] text-[hsl(var(--foreground))] outline-none"
      />
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
