"use client";

import { BrandProfileCard } from "@/components/dashboard/BrandProfileCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useDashboard } from "@/hooks/useDashboard";

export default function SettingsPage() {
  const { brandProfile } = useDashboard();

  return (
    <div className="space-y-6">
      <div>
        <h1>Settings</h1>
        <p className="text-sm text-[var(--text-secondary)]">Manage your workspace, generation style, and profile settings.</p>
      </div>

      <BrandProfileCard profile={brandProfile} />

      <Card>
        <CardHeader>
          <CardTitle>Workspace Controls</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-[var(--text-secondary)]">
          Notification preferences and workspace-level controls can be configured in this panel in the next iteration.
        </CardContent>
      </Card>
    </div>
  );
}
