"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AUTH_PREVIEW_MESSAGE } from "@/lib/mockData";
import { getBasePath } from "@/lib/navigate";
import type { UserRole } from "@/types";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPreviewModeNotice, setShowPreviewModeNotice] = useState(false);

  const [registered, setRegistered] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    const params = new URLSearchParams(window.location.search);
    setRegistered(params.get("registered") === "1");
  }, []);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setShowPreviewModeNotice(false);

    if (email === "preview@ariaconsole.com" &&
        password === "Preview123!") {
      localStorage.setItem("user", JSON.stringify({
        id: "preview-user-001",
        name: "Preview User",
        email: "preview@ariaconsole.com",
        role: "brand_manager"
      }));
      localStorage.setItem("token", "preview-token-static-mode");
      localStorage.setItem("isPreview", "true");
      window.location.href = "/AI-Social-Media-Manager/dashboard";
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ email: email.trim(), password })
      });

      let data: { token?: string; user?: { role?: UserRole }; error?: string } = {};
      try {
        data = (await response.json()) as { token?: string; user?: { role?: UserRole }; error?: string };
      } catch {
        data = {};
      }

      if (!response.ok) {
        setError(data.error ?? "Invalid email or password");
        return;
      }

      if (!data.token || !data.user?.role) {
        setError("Invalid server response.");
        return;
      }

      if (typeof window !== "undefined") {
        localStorage.setItem("token", data.token);
        localStorage.setItem("user", JSON.stringify(data.user));
        localStorage.setItem("aria_token", data.token);
        sessionStorage.setItem("aria_token", data.token);
        localStorage.setItem("aria_role", data.user.role);
      }

      const role = data.user.role;
      if (role === "agency_admin") {
        window.location.href = `${getBasePath()}/dashboard/admin`;
      } else if (role === "brand_manager") {
        window.location.href = `${getBasePath()}/dashboard/brand`;
      } else if (role === "content_creator") {
        window.location.href = `${getBasePath()}/dashboard/content`;
      } else if (role === "analyst") {
        window.location.href = `${getBasePath()}/dashboard/analytics`;
      } else {
        window.location.href = `${getBasePath()}/dashboard`;
      }
    } catch {
      setError("Connection failed. Please try again.");
      setShowPreviewModeNotice(true);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handlePreviewLogin = () => {
    const previewUser = {
      id: "preview-user-001",
      name: "Preview User",
      email: "preview@ariaconsole.com",
      role: "brand_manager"
    };
    localStorage.setItem("user", JSON.stringify(previewUser));
    localStorage.setItem("token", "preview-token-static-mode");
    localStorage.setItem("isPreview", "true");
    window.location.href = "/AI-Social-Media-Manager/dashboard";
  };

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-5xl items-center justify-center px-4 py-8">
      <section className="grid w-full overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-xl md:grid-cols-2">
        <div className="bg-gradient-to-br from-teal-700 via-sky-700 to-cyan-700 p-8 text-white">
          <p className="text-xs uppercase tracking-[0.2em] text-cyan-100">ARIA Console</p>
          <h1 className="mt-3 text-3xl font-semibold">Scale your social pipeline</h1>
          <p className="mt-4 text-sm text-cyan-100">Generate platform-native content, review quality signals, and schedule with confidence.</p>
        </div>

        <form onSubmit={submit} className="space-y-4 p-8">
          <h2 className="text-xl font-semibold text-slate-900">Sign in</h2>

          {registered ? <p className="rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">Account created. Please sign in.</p> : null}

          <label className="block space-y-1 text-sm text-slate-700">
            <span>Email</span>
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </label>

          <label className="block space-y-1 text-sm text-slate-700">
            <span>Password</span>
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </label>

          {error ? <p className="text-xs text-red-600">{error}</p> : null}

          {showPreviewModeNotice ? <p className="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800">{AUTH_PREVIEW_MESSAGE}</p> : null}

          <button className="w-full rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-60" type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Signing in..." : "Sign in"}
          </button>

          <button
            className="w-full rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700"
            type="button"
            onClick={handlePreviewLogin}
          >
            Continue as Preview User
          </button>

          <p className="text-sm text-slate-600">
            Don&apos;t have an account?{" "}
            <Link href="/register" className="font-medium text-slate-900 underline">
              Register
            </Link>
          </p>
        </form>
      </section>
    </main>
  );
}
