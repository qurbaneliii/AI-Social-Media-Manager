"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { getBasePath } from "@/lib/navigate";
import { getRoleRedirectPath } from "@/lib/role-routing";
import type { UserRole } from "@/types";

const DEFAULT_COMPANY_ID =
  process.env.NEXT_PUBLIC_DEFAULT_COMPANY_ID ??
  "00000000-0000-0000-0000-000000000000";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
        localStorage.setItem("aria_company_id", DEFAULT_COMPANY_ID);
      }

      const role = data.user.role;
      window.location.href = `${getBasePath()}${getRoleRedirectPath(role)}`;
    } catch {
      setError("Connection failed. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
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

          <button className="w-full rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-60" type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Signing in..." : "Sign in"}
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
