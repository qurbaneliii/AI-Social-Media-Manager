"use client";

import { useEffect } from "react";

import { navigateTo } from "@/lib/navigate";

export default function LegacySignInPage() {
  useEffect(() => {
    navigateTo("/login");
  }, []);

  return <main className="mx-auto max-w-4xl px-4 py-10 text-sm text-slate-600">Redirecting...</main>;
}
