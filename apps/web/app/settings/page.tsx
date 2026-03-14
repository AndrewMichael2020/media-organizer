"use client";

import { useState, useEffect, useRef } from "react";
import { FolderOpen, Check, X, AlertCircle, Loader, Play } from "lucide-react";
import { api, type ConfigSnapshot, type SourceRootInfo } from "@/lib/api";
import { cn } from "@/lib/utils";

function StatusBadge({ status }: { status: "ok" | "error" | "loading" }) {
  const styles = {
    ok:      "text-emerald-600 bg-emerald-50 dark:bg-emerald-950",
    error:   "text-red-500 bg-red-50 dark:bg-red-950",
    loading: "text-[hsl(var(--muted))] bg-[hsl(var(--surface-raised))]",
  };
  return (
    <span className={`text-[10px] tracking-wider uppercase font-medium px-2 py-0.5 rounded ${styles[status]}`}>
      {status === "loading" ? "checking…" : status}
    </span>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-[10px] tracking-[0.2em] uppercase font-medium text-[hsl(var(--muted))] mb-3">
      {children}
    </p>
  );
}

function InfoRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between px-4 py-3 text-[12px] border-b border-[hsl(var(--border-subtle))] last:border-0">
      <span className="text-[hsl(var(--muted-foreground))] font-medium">{label}</span>
      <span className="text-[hsl(var(--foreground))] font-mono">{value}</span>
    </div>
  );
}

// ── Source Root Picker ────────────────────────────────────────────────────────

type ValidationState = "idle" | "validating" | "valid" | "invalid";

function SourceRootPicker({ onScanned }: { onScanned: () => void }) {
  const [path, setPath] = useState("");
  const [validation, setValidation] = useState<ValidationState>("idle");
  const [info, setInfo] = useState<SourceRootInfo | null>(null);
  const [scanning, setScanning] = useState(false);
  const [picking, setPicking] = useState(false);
  const [scanJobId, setScanJobId] = useState<string | null>(null);
  const [scanMessage, setScanMessage] = useState<string | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Validate path as user types (debounced)
  useEffect(() => {
    if (!path.trim()) {
      setValidation("idle");
      setInfo(null);
      return;
    }
    setValidation("validating");
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      try {
        const result = await api.config.validate(path.trim());
        setInfo(result);
        setValidation(result.exists && result.readable ? "valid" : "invalid");
      } catch {
        setValidation("invalid");
        setInfo(null);
      }
    }, 500);
  }, [path]);

  async function handleBrowse() {
    setPicking(true);
    setScanMessage(null);
    try {
      const result = await api.config.pickFolder();
      setPath(result.path);
      setInfo(result);
      setValidation(result.exists && result.readable ? "valid" : "invalid");
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "";
      // 400 = user cancelled — silent
      if (!msg.includes("400")) {
        setScanMessage("Could not open folder picker");
      }
    } finally {
      setPicking(false);
    }
  }

  async function handleScan() {
    if (!path.trim() || validation !== "valid") return;
    setScanning(true);
    setScanMessage(null);
    try {
      const result = await api.config.scan(path.trim());
      setScanJobId(result.job_id);
      setScanMessage("Scan started — check Jobs for progress.");
      onScanned();
    } catch (e: unknown) {
      setScanMessage(e instanceof Error ? e.message : "Scan failed");
    } finally {
      setScanning(false);
    }
  }

  const validationIcon = {
    idle:       null,
    validating: <Loader size={12} className="animate-spin text-[hsl(var(--muted))]" />,
    valid:      <Check size={12} className="text-emerald-500" />,
    invalid:    <X size={12} className="text-red-400" />,
  }[validation];

  return (
    <div className="space-y-2">
      {/* Path input row */}
      <div className="flex gap-2">
        {/* Browse button — opens native macOS folder picker */}
        <button
          onClick={handleBrowse}
          disabled={picking}
          title="Open native folder picker (macOS)"
          className="flex items-center gap-1.5 px-3 py-2 rounded-md text-[11px] font-medium border border-[hsl(var(--border))] hover:bg-[hsl(var(--surface-raised))] transition-colors shrink-0 text-[hsl(var(--foreground))]"
        >
          {picking ? <Loader size={12} className="animate-spin" /> : <FolderOpen size={12} />}
          Browse…
        </button>

        <div className={cn(
          "flex items-center gap-2 flex-1 border rounded-md px-3 py-2 bg-[hsl(var(--surface))] transition-colors",
          validation === "valid"   && "border-emerald-400",
          validation === "invalid" && "border-red-300",
          validation === "idle" || validation === "validating" ? "border-[hsl(var(--border))]" : ""
        )}>
          <input
            type="text"
            value={path}
            onChange={(e) => setPath(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleScan()}
            placeholder="/Users/you/Photos  or  /Volumes/Drive/Archive"
            className="flex-1 text-[12px] font-mono bg-transparent outline-none placeholder:text-[hsl(var(--muted))] text-[hsl(var(--foreground))]"
          />
          <div className="shrink-0 w-4 flex items-center justify-center">
            {validationIcon}
          </div>
        </div>

        <button
          onClick={handleScan}
          disabled={validation !== "valid" || scanning}
          className={cn(
            "flex items-center gap-1.5 px-3 py-2 rounded-md text-[11px] font-medium transition-colors shrink-0",
            validation === "valid" && !scanning
              ? "bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))] hover:opacity-90"
              : "bg-[hsl(var(--surface-raised))] text-[hsl(var(--muted))] cursor-not-allowed"
          )}
        >
          {scanning ? <Loader size={12} className="animate-spin" /> : <Play size={12} />}
          Scan
        </button>
      </div>

      {/* Validation feedback */}
      {info && validation === "valid" && (
        <p className="text-[11px] text-[hsl(var(--muted-foreground))] pl-1 flex items-center gap-1.5">
          <Check size={10} className="text-emerald-500" />
          Path found
          {info.file_count_estimate !== null && (
            <> · {info.file_count_estimate.toLocaleString()} top-level items</>
          )}
        </p>
      )}
      {validation === "invalid" && (
        <p className="text-[11px] text-red-400 pl-1 flex items-center gap-1.5">
          <AlertCircle size={10} />
          {info && !info.exists ? "Path does not exist" : info && !info.readable ? "Path is not readable" : "Invalid path"}
        </p>
      )}
      {scanMessage && (
        <p className="text-[11px] text-[hsl(var(--muted-foreground))] pl-1">
          {scanMessage}
          {scanJobId && (
            <a href="/jobs" className="ml-1 underline text-[hsl(var(--foreground))]">View job →</a>
          )}
        </p>
      )}
    </div>
  );
}

// ── Source Roots List ─────────────────────────────────────────────────────────

function SourceRootRow({ root }: { root: SourceRootInfo }) {
  return (
    <div className="flex items-center gap-3 px-4 py-3 border-b border-[hsl(var(--border-subtle))] last:border-0 text-[12px]">
      <div className="flex-1 min-w-0">
        <p className="font-mono truncate text-[hsl(var(--foreground))]">{root.path}</p>
        {root.file_count_estimate !== null && (
          <p className="text-[10px] text-[hsl(var(--muted))] mt-0.5">
            {root.file_count_estimate.toLocaleString()} top-level items
          </p>
        )}
      </div>
      <div className="flex items-center gap-1.5 shrink-0">
        {root.exists && root.readable ? (
          <span className="text-[9px] uppercase tracking-wider font-medium px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-600 dark:bg-emerald-950 dark:text-emerald-400">
            Ready
          </span>
        ) : (
          <span className="text-[9px] uppercase tracking-wider font-medium px-1.5 py-0.5 rounded bg-red-50 text-red-500 dark:bg-red-950">
            {!root.exists ? "Missing" : "Unreadable"}
          </span>
        )}
      </div>
    </div>
  );
}

// ── Settings Page ─────────────────────────────────────────────────────────────

export default function SettingsPage() {
  const [health, setHealth] = useState<{ api: "ok" | "error" | "loading"; db: "ok" | "error" | "loading" }>({
    api: "loading",
    db: "loading",
  });
  const [cfg, setCfg] = useState<ConfigSnapshot | null>(null);
  const [purgeText, setPurgeText] = useState("");
  const [purging, setPurging] = useState(false);
  const [purgeMessage, setPurgeMessage] = useState<string | null>(null);

  const loadConfig = () => {
    api.config.get().then(setCfg).catch(() => {});
  };

  useEffect(() => {
    api.health()
      .then((d) => setHealth({ api: "ok", db: d.db === "ok" ? "ok" : "error" }))
      .catch(() => setHealth({ api: "error", db: "error" }));
    loadConfig();
  }, []);

  async function handlePurgeMetadata() {
    setPurging(true);
    setPurgeMessage(null);
    try {
      const result = await api.config.purgeMetadata(purgeText);
      setPurgeText("");
      setPurgeMessage(
        `Metadata purged. Cache cleared: ${result.cache_cleared ? "yes" : "no"} · Debug files cleared: ${result.debug_cleared ? "yes" : "no"}`
      );
      loadConfig();
    } catch (error: unknown) {
      setPurgeMessage(error instanceof Error ? error.message : "Purge failed");
    } finally {
      setPurging(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-8 py-10 space-y-10">

      {/* ── Scan a folder ── */}
      <div>
        <SectionLabel>Scan a Source Folder</SectionLabel>
        <p className="text-[11px] text-[hsl(var(--muted-foreground))] mb-4 leading-relaxed">
          Enter the absolute path to a folder of photos or videos on this machine.
          The scanner will recursively register all supported media without moving any files.
        </p>
        <SourceRootPicker onScanned={loadConfig} />
      </div>

      {/* ── Registered roots ── */}
      {cfg && cfg.source_roots.length > 0 && (
        <div>
          <SectionLabel>Registered Source Roots</SectionLabel>
          <div className="border border-[hsl(var(--border))] rounded-lg overflow-hidden">
            {cfg.source_roots.map((r) => <SourceRootRow key={r.path} root={r} />)}
          </div>
        </div>
      )}

      {/* ── System Status ── */}
      <div>
        <SectionLabel>System Status</SectionLabel>
        <div className="border border-[hsl(var(--border))] rounded-lg overflow-hidden">
          <InfoRow label="API" value={<StatusBadge status={health.api} />} />
          <InfoRow label="Database" value={<StatusBadge status={health.db} />} />
        </div>
      </div>

      {/* ── Runtime ── */}
      <div>
        <SectionLabel>Runtime</SectionLabel>
        <div className="border border-[hsl(var(--border))] rounded-lg overflow-hidden">
          <InfoRow label="API URL" value="http://localhost:8000" />
          <InfoRow label="Mode" value="local-first" />
          <InfoRow label="Version" value={cfg?.api_version ?? "—"} />
          <InfoRow
            label="Derivative cache"
            value={cfg?.derivative_cache_root ?? "—"}
          />
        </div>
      </div>

      {/* ── Model ── */}
      <div>
        <SectionLabel>Extraction Model</SectionLabel>
        <div className="border border-[hsl(var(--border))] rounded-lg overflow-hidden">
          <InfoRow label="Provider" value={cfg?.model_provider ?? "—"} />
          <InfoRow label="Model" value={cfg?.model_name ?? "—"} />
          <InfoRow label="Configured via" value="config/local.yaml" />
        </div>
      </div>

      <div>
        <SectionLabel>Danger Zone</SectionLabel>
        <div className="rounded-lg border border-red-200 bg-red-50/60 p-4 dark:border-red-900 dark:bg-red-950/30">
          <p className="text-[12px] leading-relaxed text-[hsl(var(--foreground))]">
            Purge all metadata, extracted AI data, jobs, thumbnails, keyframes, and cached debug files. Original photos
            and videos stay in place.
          </p>
          <p className="mt-2 text-[11px] text-[hsl(var(--muted-foreground))]">
            Type <span className="font-mono">PURGE ALL METADATA</span> to confirm.
          </p>
          <div className="mt-3 flex gap-2">
            <input
              type="text"
              value={purgeText}
              onChange={(event) => setPurgeText(event.target.value)}
              placeholder="PURGE ALL METADATA"
              className="flex-1 rounded-md border border-[hsl(var(--border))] bg-[hsl(var(--surface))] px-3 py-2 text-[12px] font-mono outline-none"
            />
            <button
              onClick={handlePurgeMetadata}
              disabled={purgeText.trim() !== "PURGE ALL METADATA" || purging}
              className={cn(
                "rounded-md px-4 py-2 text-[11px] font-medium transition-colors",
                purgeText.trim() === "PURGE ALL METADATA" && !purging
                  ? "bg-red-600 text-white hover:bg-red-700"
                  : "bg-[hsl(var(--surface-raised))] text-[hsl(var(--muted))] cursor-not-allowed"
              )}
            >
              {purging ? "Purging..." : "Purge all metadata"}
            </button>
          </div>
          {purgeMessage && (
            <p className="mt-2 text-[11px] text-[hsl(var(--muted-foreground))]">{purgeMessage}</p>
          )}
        </div>
      </div>

    </div>
  );
}
