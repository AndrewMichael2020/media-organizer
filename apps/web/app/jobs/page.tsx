"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { Activity, RefreshCw, Cpu, Image, Layers, Coins, FolderOpen, Square, RotateCcw } from "lucide-react";
import { cn } from "@/lib/utils";
import { api, type JobOut, type CostStats } from "@/lib/api";

type JobStatus = "running" | "queued" | "done" | "failed" | "cancelled";

const STATUS_STYLES: Record<JobStatus, string> = {
  running: "text-blue-500",
  queued:  "text-[hsl(var(--muted))]",
  done:    "text-emerald-600",
  failed:  "text-red-500",
  cancelled: "text-amber-600",
};

const STATUS_DOT: Record<JobStatus, string> = {
  running: "bg-blue-500 animate-pulse",
  queued:  "bg-[hsl(var(--muted))]",
  done:    "bg-emerald-500",
  failed:  "bg-red-500",
  cancelled: "bg-amber-500",
};

const JOB_ACTIONS = [
  { type: "enrich",    label: "Enrich metadata",    icon: Layers, description: "ExifTool + ffprobe on all un-enriched assets" },
  { type: "reprocess", label: "Generate thumbnails", icon: Image,  description: "Create 400px thumbs & video keyframes" },
  { type: "extract",   label: "AI extraction",       icon: Cpu,    description: "Run Gemini on all un-extracted photos" },
];

export default function JobsPage() {
  const [jobs, setJobs] = useState<JobOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState<string | null>(null);
  const [costStats, setCostStats] = useState<CostStats | null>(null);
  const [scopePath, setScopePath] = useState("");
  const [busyReset, setBusyReset] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const jobsRef = useRef<JobOut[]>([]);

  const load = useCallback(() => {
    api.jobs.list()
      .then(setJobs)
      .catch(() => {})
      .finally(() => setLoading(false));
    api.jobs.costStats()
      .then(setCostStats)
      .catch(() => {});
  }, []);

  useEffect(() => {
    jobsRef.current = jobs;
  }, [jobs]);

  // Poll while any job is running
  useEffect(() => {
    load();
    pollRef.current = setInterval(() => {
      if (jobsRef.current.some((j) => j.status === "running" || j.status === "queued")) {
        load();
      }
    }, 3000);
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [load]);

  // Re-poll when running jobs exist
  useEffect(() => {
    if (jobs.some((j) => j.status === "running" || j.status === "queued")) {
      const t = setTimeout(load, 2500);
      return () => clearTimeout(t);
    }
  }, [jobs, load]);

  async function startJob(type: string) {
    setStarting(type);
    try {
      await api.jobs.startIngest({ type, source_root: scopePath.trim() || undefined });
      load();
    } finally {
      setStarting(null);
    }
  }

  async function stopJob(id: string) {
    await api.jobs.stop(id);
    load();
  }

  async function pickFolder() {
    try {
      const result = await api.config.pickFolder();
      setScopePath(result.path);
    } catch {}
  }

  async function resetScope() {
    if (!scopePath.trim()) return;
    setBusyReset(true);
    try {
      await api.assets.resetMetadata(scopePath.trim());
      load();
    } finally {
      setBusyReset(false);
    }
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-[hsl(var(--border-subtle))]">
        <div className="flex items-center gap-2">
          <Activity size={13} className="text-[hsl(var(--muted))]" />
          <span className="text-[11px] tracking-[0.15em] uppercase font-medium text-[hsl(var(--muted))]">
            Job Queue
          </span>
        </div>
        <button onClick={load} className="flex items-center gap-1.5 text-[11px] text-[hsl(var(--muted))] hover:text-[hsl(var(--foreground))] transition-colors">
          <RefreshCw size={11} />
          Refresh
        </button>
      </div>

      {/* Quick actions */}
      <div className="px-6 py-4 border-b border-[hsl(var(--border-subtle))] bg-[hsl(var(--surface))]">
        <p className="text-[10px] tracking-[0.2em] uppercase font-medium text-[hsl(var(--muted))] mb-3">
          Run a Job
        </p>
        <div className="mb-3 flex flex-wrap gap-2">
          <button
            onClick={pickFolder}
            className="flex items-center gap-1.5 px-3 py-2 rounded-md text-[11px] font-medium border border-[hsl(var(--border))]"
          >
            <FolderOpen size={11} />
            Pick folder
          </button>
          <input
            type="text"
            value={scopePath}
            onChange={(e) => setScopePath(e.target.value)}
            placeholder="Optional: run only on this folder"
            className="min-w-[320px] flex-1 rounded-md border border-[hsl(var(--border))] bg-[hsl(var(--surface-raised))] px-3 py-2 text-[12px] font-mono"
          />
          <button
            onClick={resetScope}
            disabled={!scopePath.trim() || busyReset}
            className="flex items-center gap-1.5 px-3 py-2 rounded-md text-[11px] font-medium border border-[hsl(var(--border))] disabled:opacity-50"
          >
            <RotateCcw size={11} />
            Reset metadata
          </button>
        </div>
        <div className="flex gap-2 flex-wrap">
          {JOB_ACTIONS.map(({ type, label, icon: Icon, description }) => (
            <button
              key={type}
              onClick={() => startJob(type)}
              disabled={starting === type}
              title={description}
              className={cn(
                "flex items-center gap-1.5 px-3 py-2 rounded-md text-[11px] font-medium border transition-colors",
                starting === type
                  ? "border-[hsl(var(--border))] text-[hsl(var(--muted))] cursor-wait"
                  : "border-[hsl(var(--border))] hover:bg-[hsl(var(--surface-raised))] text-[hsl(var(--foreground))]"
              )}
            >
              {starting === type
                ? <RefreshCw size={11} className="animate-spin" />
                : <Icon size={11} />}
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* AI cost stats */}
      {costStats && costStats.total_runs > 0 && (
        <div className="px-6 py-3 border-b border-[hsl(var(--border-subtle))] bg-[hsl(var(--surface-raised))]">
          <div className="flex items-center gap-1.5 mb-2">
            <Coins size={10} className="text-[hsl(var(--muted))]" />
            <span className="text-[10px] tracking-[0.2em] uppercase font-medium text-[hsl(var(--muted))]">AI Usage</span>
          </div>
          <div className="flex gap-6 flex-wrap">
            <Stat label="Extractions" value={String(costStats.total_runs)} />
            <Stat label="Tokens in" value={costStats.total_tokens_in.toLocaleString()} />
            <Stat label="Tokens out" value={costStats.total_tokens_out.toLocaleString()} />
            <Stat
              label="Total cost"
              value={costStats.total_cost_usd < 0.001
                ? `< $0.001`
                : `$${costStats.total_cost_usd.toFixed(4)}`}
              highlight
            />
            <Stat label="Avg / image" value={`$${costStats.avg_cost_per_run_usd.toFixed(5)}`} />
          </div>
        </div>
      )}

      {/* Job list */}
      <div className="flex-1 overflow-auto">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <span className="text-[11px] text-[hsl(var(--muted))]">Loading…</span>
          </div>
        ) : jobs.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full gap-3">
            <p className="text-[11px] tracking-[0.2em] uppercase font-medium text-[hsl(var(--muted))]">No Jobs</p>
            <p className="text-[12px] text-[hsl(var(--muted-foreground))] max-w-xs text-center leading-relaxed">
              Use the buttons above or scan a folder from Settings to get started.
            </p>
          </div>
        ) : (
          <table className="w-full text-[12px]">
            <thead>
              <tr className="border-b border-[hsl(var(--border-subtle))]">
                {["Type", "Status", "Started", "Duration", "Message", "Actions"].map((h) => (
                  <th key={h} className="text-left px-6 py-2.5 text-[10px] tracking-[0.15em] uppercase font-medium text-[hsl(var(--muted))]">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => {
                const started = new Date(job.started_at);
                const finished = job.finished_at ? new Date(job.finished_at) : null;
                const durationMs = finished ? finished.getTime() - started.getTime() : null;
                const duration = durationMs !== null
                  ? durationMs < 1000 ? `${durationMs}ms`
                  : durationMs < 60000 ? `${(durationMs / 1000).toFixed(1)}s`
                  : `${Math.round(durationMs / 60000)}m`
                  : job.status === "running" ? "running…" : "—";

                return (
                  <tr key={job.id} className="border-b border-[hsl(var(--border-subtle))] hover:bg-[hsl(var(--surface-raised))] transition-colors">
                    <td className="px-6 py-3 font-medium font-mono text-[11px]">{job.type}</td>
                    <td className="px-6 py-3">
                      <span className={cn("flex items-center gap-1.5", STATUS_STYLES[job.status as JobStatus] || "")}>
                        <span className={cn("w-1.5 h-1.5 rounded-full", STATUS_DOT[job.status as JobStatus] || "bg-gray-300")} />
                        {job.status}
                      </span>
                    </td>
                    <td className="px-6 py-3 text-[hsl(var(--muted))] font-mono text-[10px]">
                      {started.toLocaleTimeString()}
                    </td>
                    <td className="px-6 py-3 text-[hsl(var(--muted))] font-mono text-[10px]">
                      {duration}
                    </td>
                    <td className="px-6 py-3 text-[hsl(var(--muted-foreground))] max-w-sm truncate">{job.message ?? "—"}</td>
                    <td className="px-6 py-3">
                      {(job.status === "running" || job.status === "queued") && (
                        <button
                          onClick={() => stopJob(job.id)}
                          className="inline-flex items-center gap-1 rounded-md border border-[hsl(var(--border))] px-2 py-1 text-[10px] uppercase tracking-[0.14em]"
                        >
                          <Square size={10} />
                          Stop
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function Stat({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-[9px] tracking-[0.15em] uppercase text-[hsl(var(--muted))]">{label}</span>
      <span className={cn(
        "text-[12px] font-mono tabular-nums",
        highlight ? "text-emerald-600 font-semibold" : "text-[hsl(var(--foreground))]"
      )}>{value}</span>
    </div>
  );
}
