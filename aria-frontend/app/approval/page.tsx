"use client";

import { useEffect } from "react";

import { navigateTo } from "@/lib/navigate";

export default function ApprovalRedirectPage() {
  useEffect(() => {
    navigateTo("/dashboard/approval");
  }, []);

  return <main className="mx-auto max-w-4xl px-4 py-10 text-sm text-[var(--text-secondary)]">Opening approval queue...</main>;
}
