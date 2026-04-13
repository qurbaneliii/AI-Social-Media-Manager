"use client";

import { useEffect } from "react";

import { navigateTo } from "@/lib/navigate";

export default function HomePage() {
  useEffect(() => {
    const redirect = sessionStorage.getItem("redirect");
    if (redirect) {
      sessionStorage.removeItem("redirect");
      window.location.replace(redirect);
      return;
    }

    navigateTo("/login");
  }, []);

  return <main className="mx-auto max-w-4xl px-4 py-10 text-sm text-slate-600">Redirecting...</main>;
}
