"use client";

import { useEffect } from "react";
import { usePathname } from "next/navigation";

import { useAuth } from "@/context/AuthContext";

const navLinks = [
  { label: "Brand Dashboard", href: "/AI-Social-Media-Manager/dashboard/brand" },
  { label: "Content Dashboard", href: "/AI-Social-Media-Manager/dashboard/content" },
  { label: "Analytics Dashboard", href: "/AI-Social-Media-Manager/dashboard/analytics" },
  { label: "Admin Dashboard", href: "/AI-Social-Media-Manager/dashboard/admin" },
  { label: "Create Post", href: "/AI-Social-Media-Manager/posts/new" },
  { label: "Posts", href: "/AI-Social-Media-Manager/posts" },
  { label: "Scheduler", href: "/AI-Social-Media-Manager/scheduler" },
  { label: "Settings", href: "/AI-Social-Media-Manager/onboarding/company-profile" }
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    const storedUser = localStorage.getItem("user");
    const token = localStorage.getItem("token");
    if (!storedUser || !token) {
      window.location.href = "/AI-Social-Media-Manager/login";
    }
  }, []);

  return (
    <div className="min-h-screen bg-slate-50">
      <div
        style={{
          background: "#FEF3C7",
          borderBottom: "1px solid #F59E0B",
          padding: "8px 16px",
          textAlign: "center",
          fontSize: "14px",
          color: "#92400E"
        }}
      >
        ⚠️ Preview Mode — AI and database features are disabled. Deploy with a live backend for full functionality.
      </div>

      <div className="mx-auto grid max-w-7xl gap-5 px-4 py-5 lg:grid-cols-[260px_1fr]">
        <aside className="rounded-xl border bg-white p-4">
          <p className="text-xs uppercase tracking-widest text-slate-500">ARIA Console</p>
          <p className="mt-1 text-sm font-semibold text-slate-900">Navigation</p>

          <nav className="mt-4 space-y-2">
            {navLinks.map((item) => {
              const active = pathname.startsWith(item.href.replace("/AI-Social-Media-Manager", ""));
              return (
                <button
                  key={item.href}
                  type="button"
                  onClick={() => {
                    window.location.href = item.href;
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
              <p className="text-sm font-semibold text-slate-900">{user?.name ?? "Preview User"}</p>
              <p className="text-xs text-slate-600">{user?.email ?? "preview@ariaconsole.com"}</p>
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
