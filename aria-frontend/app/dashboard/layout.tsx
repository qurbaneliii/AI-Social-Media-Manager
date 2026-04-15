"use client";

import { useEffect } from "react";
import { usePathname } from "next/navigation";

import { useAuth } from "@/context/AuthContext";
import { navigateTo } from "@/lib/navigate";

const navLinks = [
  { label: "Analytics", href: "/analytics" },
  { label: "Create Post", href: "/posts/new" },
  { label: "Posts", href: "/posts" },
  { label: "Scheduler", href: "/scheduler" },
  { label: "Settings", href: "/onboarding/company-profile" }
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    const storedUser = localStorage.getItem("user");
    const token = localStorage.getItem("token") ?? localStorage.getItem("aria_token");
    if (!storedUser || !token) {
      navigateTo("/login");
    }
  }, []);

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="mx-auto grid max-w-7xl gap-5 px-4 py-5 lg:grid-cols-[260px_1fr]">
        <aside className="rounded-xl border bg-white p-4">
          <p className="text-xs uppercase tracking-widest text-slate-500">ARIA Console</p>
          <p className="mt-1 text-sm font-semibold text-slate-900">Navigation</p>

          <nav className="mt-4 space-y-2">
            {navLinks.map((item) => {
              const active = pathname.startsWith(item.href);
              return (
                <button
                  key={item.href}
                  type="button"
                  onClick={() => {
                    navigateTo(item.href);
                  }}
                  className={`w-full rounded-lg px-3 py-2 text-left text-sm ${
                    active ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-700"
                  }`}
                >
                  {item.label}
                </button>
              );
            })}
          </nav>
        </aside>

        <section className="space-y-4">
          <header className="flex items-center justify-between rounded-xl border bg-white px-4 py-3">
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-500">Signed in</p>
              <p className="text-sm font-semibold text-slate-900">{user?.name ?? "User"}</p>
              <p className="text-xs text-slate-600">{user?.email ?? "No email"}</p>
            </div>
            <button
              type="button"
              onClick={logout}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700"
            >
              Logout
            </button>
          </header>

          <div>{children}</div>
        </section>
      </div>
    </div>
  );
}
