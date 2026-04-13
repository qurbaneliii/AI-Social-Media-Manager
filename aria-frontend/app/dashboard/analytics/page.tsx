"use client";

import { useRequireAuth } from "@/hooks/useRequireAuth";

export default function AnalyticsDashboardPage() {
  const { user, isLoading } = useRequireAuth();

  if (isLoading) {
    return <main className="mx-auto max-w-4xl px-4 py-10 text-sm text-slate-600">Loading...</main>;
  }

  if (user?.role !== "analyst") {
    return <main className="mx-auto max-w-4xl px-4 py-10 text-sm text-red-700">Unauthorized role access.</main>;
  }

  return (
    <main className="mx-auto max-w-4xl space-y-3 px-4 py-10">
      <h1 className="text-3xl font-semibold text-slate-900">Analytics Dashboard</h1>
      <p className="text-slate-600">Signed in as {user.email}</p>
    </main>
  );
}
