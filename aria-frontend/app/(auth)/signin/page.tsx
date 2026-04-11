// filename: app/(auth)/signin/page.tsx
// purpose: Simple sign-in page to bootstrap role/company session.

"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { setClientSession } from "@/lib/client-session";
import { useCompanyStore } from "@/stores/useCompanyStore";
import type { UserRole } from "@/types";

const roles: UserRole[] = ["agency_admin", "brand_manager", "content_creator", "analyst"];

export default function SignInPage() {
  const router = useRouter();
  const setActiveRole = useCompanyStore((s) => s.setActiveRole);
  const setCompanyId = useCompanyStore((s) => s.setCompanyId);

  const [email, setEmail] = useState("");
  const [token, setToken] = useState("");
  const [companyId, setCompanyIdInput] = useState("");
  const [role, setRole] = useState<UserRole>("brand_manager");

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!token.trim() || !companyId.trim() || !email.trim()) {
      return;
    }
    setClientSession({ token, role, companyId });
    setActiveRole(role);
    setCompanyId(companyId);
    router.push("/onboarding/company-profile");
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
            <span>API Token</span>
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
              type="password"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              required
            />
          </label>

          <label className="block space-y-1 text-sm text-slate-700">
            <span>Company ID</span>
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
              type="text"
              value={companyId}
              onChange={(e) => setCompanyIdInput(e.target.value)}
              required
            />
          </label>

          <label className="block space-y-1 text-sm text-slate-700">
            <span>Role</span>
            <select
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
              value={role}
              onChange={(e) => setRole(e.target.value as UserRole)}
            >
              {roles.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>

          <button className="w-full rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white" type="submit">
            Continue
          </button>
        </form>
      </section>
    </main>
  );
}
