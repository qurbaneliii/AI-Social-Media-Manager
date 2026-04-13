"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuth } from "@/context/AuthContext";
import { useRequireAuth } from "@/hooks/useRequireAuth";
import { getRoleRedirectPath } from "@/lib/role-routing";

export default function DashboardPage() {
  const router = useRouter();
  const { isLoading } = useRequireAuth();
  const { user } = useAuth();

  useEffect(() => {
    if (!isLoading && user) {
      router.replace(getRoleRedirectPath(user.role));
    }
  }, [isLoading, router, user]);

  if (isLoading) {
    return <main className="mx-auto max-w-4xl px-4 py-10 text-sm text-slate-600">Loading...</main>;
  }

  return (
    <main className="mx-auto max-w-4xl space-y-4 px-4 py-10">
      <h1 className="text-3xl font-semibold text-slate-900">Dashboard</h1>
      <p className="text-slate-600">Redirecting...</p>
    </main>
  );
}
