"use client";

import { BrainCircuit, Building2, Database, LockKeyhole, Server, ShieldCheck } from "lucide-react";
import { useMemo } from "react";

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
        <h2 id="runtime-settings-heading">Runtime and AI</h2>
        <div className="mt-2">
          <DiagnosticRow icon={Server} label="Environment mode" value={previewMode ? "Preview" : "Connected"} tone={previewMode ? "warning" : "success"} detail={previewMode ? "Static demo data is enabled and changes do not persist." : "The product expects authenticated backend services and persisted data."} />
          <DiagnosticRow icon={Database} label="Core API configuration" value={apiConfigured ? "Configured" : "Missing"} tone={apiConfigured ? "success" : "warning"} detail="The canonical frontend uses NEXT_PUBLIC_API_BASE_URL. Production does not silently fall back to localhost." />
          <DiagnosticRow icon={BrainCircuit} label="AI provider gateway" value={previewMode ? "Simulated" : "Backend managed"} tone={previewMode ? "warning" : "neutral"} detail={previewMode ? "Preview generation is deterministic and does not contact an AI provider." : "Model selection and provider credentials are controlled by the orchestration backend."} />
          <DiagnosticRow icon={LockKeyhole} label="Credential boundary" value="Server only" tone="success" detail="No OpenAI or Anthropic credential is accepted or stored by this frontend." />
        </div>
      </section>

      <p className="text-xs text-[var(--text-muted)]">Integration controls are intentionally hidden until an external platform connection can be configured and verified end to end.</p>
    </section>
  );
}
