"use client";

import { useEffect } from "react";

import { navigateTo } from "@/lib/navigate";

export default function AdminDashboardPage() {
  useEffect(() => {
    navigateTo("/dashboard/analytics");
  }, []);

  return (
    <main className="mx-auto max-w-4xl px-4 py-10 text-sm text-[var(--text-secondary)]">Redirecting to analytics...</main>
  );
}
