"use client";

import { BarChart3, BrainCircuit, Building2, CalendarClock, CloudUpload, Database, LockKeyhole, Send, Server, ShieldCheck, Workflow } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";

import { getCapabilities } from "@/lib/api";
import { getClientSession } from "@/lib/client-session";

function DiagnosticRow({ icon: Icon, label, value, detail, tone = "neutral" }: { icon: typeof Server; label: string; value: string; detail: string; tone?: "neutral" | "success" | "warning" }) {
  const toneClass = tone === "success" ? "border-emerald-200 bg-emerald-50 text-emerald-800" : tone === "warning" ? "border-amber-200 bg-amber-50 text-amber-800" : "border-[var(--border)] bg-[var(--bg-secondary)] text-[var(--text-secondary)]";
  return (
    <div className="grid gap-3 border-b border-[var(--border)] py-5 last:border-b-0 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center">
      <div className="flex min-w-0 items-start gap-3"><span className="inline-flex size-9 shrink-0 items-center justify-center rounded bg-[var(--bg-elevated)] text-[var(--brand-primary)]"><Icon aria-hidden="true" className="size-4" /></span><div><h3 className="text-sm font-semibold">{label}</h3><p className="mt-1 text-sm text-[var(--text-secondary)]">{detail}</p></div></div>
      <span className={`w-fit rounded border px-2 py-1 text-xs font-semibold ${toneClass}`}>{value}</span>
    </div>
  );
}

export default function SettingsPage() {
  const session = useMemo(() => getClientSession(), []);
  const previewMode = process.env.NEXT_PUBLIC_PREVIEW_MODE === "true" || process.env.PREVIEW_MODE === "true";
  const apiConfigured = Boolean(process.env.NEXT_PUBLIC_API_BASE_URL?.trim());
  const capabilities = useQuery({ queryKey: ["capabilities"], queryFn: getCapabilities, enabled: !previewMode && apiConfigured });
  const capability = (key: keyof NonNullable<typeof capabilities.data>, fallback: string) => capabilities.data?.[key] ?? { status: capabilities.isError ? "Degraded" : "Unavailable", detail: fallback, interactive: false };

  return (
    <section className="mx-auto w-full max-w-5xl space-y-7">
      <header>
        <p className="label-xs mb-2">Workspace administration</p>
        <h1>Settings</h1>
        <p className="mt-1 max-w-2xl text-sm text-[var(--text-secondary)]">Inspect account context, runtime mode, and deployment readiness. Provider credentials remain server-side.</p>
      </header>

      <section className="surface-card rounded p-5 sm:p-6" aria-labelledby="workspace-settings-heading">
        <h2 id="workspace-settings-heading">Workspace</h2>
        <div className="mt-2">
          <DiagnosticRow icon={Building2} label="Organization context" value={session.companyId ? "Selected" : "Missing"} tone={session.companyId ? "success" : "warning"} detail={session.companyId ? `Workspace ${session.companyId.slice(0, 12)} is active for this browser session.` : "No organization is selected. Sign in again before creating content."} />
          <DiagnosticRow icon={ShieldCheck} label="Access role" value={session.role?.replaceAll("_", " ") ?? "Unknown"} detail="Navigation visibility reflects this role; backend authorization remains the source of truth." />
        </div>
      </section>

      <section className="surface-card rounded p-5 sm:p-6" aria-labelledby="runtime-settings-heading">
        <h2 id="runtime-settings-heading">Capability status</h2>
        <p className="mt-1 text-sm text-[var(--text-secondary)]">Configuration visibility from this frontend build. Degraded means a backend may be configured, but this screen cannot verify the capability end to end.</p>
        <div className="mt-2">
          <DiagnosticRow icon={Server} label="Environment mode" value={previewMode ? "Preview" : "Connected"} tone={previewMode ? "warning" : "success"} detail={previewMode ? "Static demo data is enabled and changes do not persist." : "The product expects authenticated backend services and persisted data."} />
          <DiagnosticRow icon={Database} label="Core API configuration" value={apiConfigured ? "Configured" : "Missing"} tone={apiConfigured ? "success" : "warning"} detail="The canonical frontend uses NEXT_PUBLIC_API_BASE_URL. Production does not silently fall back to localhost." />
          <DiagnosticRow icon={Database} label="Database" value={previewMode ? "Demo" : capability("database", "Database health could not be verified.").status} tone="warning" detail={previewMode ? "Preview records are static and are not persisted to a database." : capability("database", "Database health could not be verified.").detail} />
          <DiagnosticRow icon={ShieldCheck} label="Authentication" value={previewMode ? "Demo" : capability("authentication", "Authentication health could not be verified.").status} tone={previewMode ? "warning" : "success"} detail={previewMode ? "A preview session is active; it is not a production identity." : capability("authentication", "Authentication health could not be verified.").detail} />
          <DiagnosticRow icon={BrainCircuit} label="AI provider" value={previewMode ? "Demo" : capability("ai_provider", "AI provider health could not be verified.").status} tone="warning" detail={previewMode ? "Preview generation is deterministic and does not contact an AI provider." : capability("ai_provider", "AI provider health could not be verified.").detail} />
          <DiagnosticRow icon={BrainCircuit} label="AI mock mode" value={previewMode ? "Demo" : capability("ai_mock_mode", "AI mode could not be verified.").status} tone={previewMode ? "warning" : "neutral"} detail={previewMode ? "Mock output is visibly identified throughout the product." : capability("ai_mock_mode", "AI mode could not be verified.").detail} />
          <DiagnosticRow icon={CloudUpload} label="Media storage" value={capability("media_storage", "Media storage is unavailable.").status} tone="neutral" detail={capability("media_storage", "Media storage is unavailable.").detail} />
          <DiagnosticRow icon={CalendarClock} label="External scheduling" value={capability("external_scheduling", "External scheduling is unavailable.").status} tone="neutral" detail={capability("external_scheduling", "External scheduling is unavailable.").detail} />
          <DiagnosticRow icon={Send} label="Publishing" value={capability("publishing", "Publishing is unavailable.").status} tone="neutral" detail={capability("publishing", "Publishing is unavailable.").detail} />
          <DiagnosticRow icon={BarChart3} label="External analytics" value={capability("external_analytics", "External analytics is unavailable.").status} tone="neutral" detail={capability("external_analytics", "External analytics is unavailable.").detail} />
          <DiagnosticRow icon={Workflow} label="Background workers" value={capability("background_workers", "Background workers are unavailable.").status} tone="neutral" detail={capability("background_workers", "Background workers are unavailable.").detail} />
          <DiagnosticRow icon={LockKeyhole} label="Credential boundary" value="Server only" tone="success" detail="No OpenAI or Anthropic credential is accepted or stored by this frontend." />
        </div>
      </section>

      <p className="text-xs text-[var(--text-muted)]">Integration controls are intentionally hidden until an external platform connection can be configured and verified end to end.</p>
    </section>
  );
}
