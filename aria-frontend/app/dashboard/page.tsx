"use client";

import { useEffect } from "react";

import { navigateTo } from "@/lib/navigate";

export default function DashboardPage() {
  useEffect(() => {
    navigateTo("/dashboard/brand");
  }, []);

  return <main className="mx-auto max-w-4xl px-4 py-10 text-sm text-[var(--text-secondary)]">Redirecting to brand dashboard...</main>;
}
