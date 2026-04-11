// filename: app/oauth/callback/page.tsx
// purpose: OAuth callback relay that forwards callback params to onboarding platform connection screen.

"use client";

import { useEffect } from "react";

export default function OAuthCallbackPage() {
  useEffect(() => {
    const query = window.location.search.replace(/^\?/, "");
    const next = query ? `/onboarding/platforms?${query}` : "/onboarding/platforms";
    window.location.replace(next);
  }, []);

  return (
    <main className="rounded-xl border bg-white p-6 text-sm text-slate-700">
      Processing OAuth callback...
    </main>
  );
}
