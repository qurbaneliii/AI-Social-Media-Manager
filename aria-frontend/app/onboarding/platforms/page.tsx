// filename: app/onboarding/platforms/page.tsx
// purpose: OAuth platform connection step.

"use client";

import { useRouter } from "next/navigation";
import { useEffect, useMemo } from "react";

import { OnboardingProgressStepper } from "@/components/onboarding/OnboardingProgressStepper";
import { getOAuthConnectUrl } from "@/lib/api";
import { getClientSession } from "@/lib/client-session";
import { useCompanyStore } from "@/stores/useCompanyStore";
import type { Platform } from "@/types";

const platforms: Platform[] = ["instagram", "linkedin", "facebook", "x", "tiktok", "pinterest"];

export default function PlatformsPage() {
  const router = useRouter();

  const companyId = useCompanyStore((s) => s.companyId) ?? getClientSession().companyId;
  const credentials = useCompanyStore((s) => s.platformCredentials);
  const updateCredential = useCompanyStore((s) => s.updatePlatformCredential);

  const callback = useMemo(() => {
    if (typeof window === "undefined") {
      return { platform: null, status: null, error: null, account_ref: null, token_expires_at: null };
    }
    const params = new URLSearchParams(window.location.search);
    return {
      platform: params.get("platform"),
      status: params.get("status"),
      error: params.get("error"),
      account_ref: params.get("account_ref"),
      token_expires_at: params.get("token_expires_at")
    };
  }, []);

  useEffect(() => {
    if (!callback.platform) return;
    const platform = callback.platform as Platform;
    if (!platforms.includes(platform)) return;

    if (callback.error === "state_mismatch") {
      updateCredential(platform, { status: "disconnected" });
      return;
    }

    if (callback.status === "connected") {
      updateCredential(platform, {
        status: "connected",
        account_ref: callback.account_ref ?? undefined,
        token_expires_at: callback.token_expires_at ?? undefined,
        updated_at: new Date().toISOString()
      });
    } else if (callback.status === "expired") {
      updateCredential(platform, {
        status: "expired",
        account_ref: callback.account_ref ?? undefined,
        token_expires_at: callback.token_expires_at ?? undefined,
        updated_at: new Date().toISOString()
      });
    }
  }, [callback, updateCredential]);

  if (!companyId) {
    return <div className="rounded-xl border bg-white p-6 text-sm text-red-700">Company ID is required. Return to sign in.</div>;
  }

  return (
    <main className="mx-auto grid max-w-7xl gap-6 px-4 py-8 lg:grid-cols-[300px_1fr]">
      <OnboardingProgressStepper currentStep={9} score={null} />

      <section className="space-y-6 rounded-2xl border bg-white p-6">
        <header>
          <h1 className="text-2xl font-semibold text-slate-900">Connect platforms</h1>
          <p className="text-sm text-slate-600">Authorize publishing destinations. You can reconnect expired tokens here.</p>
        </header>

        {callback.error === "state_mismatch" ? (
          <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            OAuth state mismatch detected. Please reconnect from this page.
          </div>
        ) : null}

        <div className="grid gap-3 md:grid-cols-2">
          {platforms.map((platform) => {
            const status = credentials[platform]?.status ?? "disconnected";
            const accountRef = credentials[platform]?.account_ref;
            const tokenExpiresAt = credentials[platform]?.token_expires_at;
            const expiresSoon =
              Boolean(tokenExpiresAt) &&
              new Date(tokenExpiresAt as string).getTime() - Date.now() <= 7 * 24 * 60 * 60 * 1000 &&
              new Date(tokenExpiresAt as string).getTime() > Date.now();
            const color = status === "connected" ? "bg-emerald-100 text-emerald-700" : status === "expired" ? "bg-amber-100 text-amber-700" : "bg-slate-100 text-slate-700";

            return (
              <article key={platform} className="rounded-xl border p-4">
                <div className="mb-3 flex items-center justify-between">
                  <h2 className="text-sm font-semibold capitalize text-slate-900">{platform}</h2>
                  <span className={`rounded-full px-2 py-1 text-xs ${color}`}>{status}</span>
                </div>
                <a
                  href={getOAuthConnectUrl(platform, companyId)}
                  className="inline-flex rounded-lg bg-slate-900 px-3 py-2 text-xs font-medium text-white"
                >
                  {status === "connected" ? "Reconnect" : "Connect"}
                </a>
                {accountRef ? <p className="mt-2 text-xs text-slate-600">Account: {accountRef}</p> : null}
                {tokenExpiresAt ? <p className="mt-1 text-xs text-slate-500">Token expires: {new Date(tokenExpiresAt).toLocaleString()}</p> : null}
                {expiresSoon ? <p className="mt-1 text-xs text-amber-700">Token expires within 7 days</p> : null}
              </article>
            );
          })}
        </div>

        <button
          type="button"
          onClick={() => router.push("/onboarding/quality-check")}
          className="rounded-lg bg-teal-700 px-4 py-2 text-sm font-medium text-white"
        >
          Continue to quality check
        </button>
      </section>
    </main>
  );
}
