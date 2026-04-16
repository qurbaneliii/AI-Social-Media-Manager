"use client";

import { useMemo, useState } from "react";
import { Facebook, Instagram, Linkedin, PencilLine, Save, Twitter } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Sheet, SheetContent, SheetDescription, SheetFooter, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { Textarea } from "@/components/ui/textarea";
import type { BrandProfile, DashboardPlatform } from "@/lib/mock-data";
import { useDashboardStore } from "@/lib/store";

interface BrandProfileCardProps {
  profile: BrandProfile;
}

const platformIcons: Record<DashboardPlatform, React.ComponentType<{ className?: string }>> = {
  linkedin: Linkedin,
  twitter: Twitter,
  instagram: Instagram,
  facebook: Facebook
};

const platformColors: Record<DashboardPlatform, string> = {
  linkedin: "text-[#0077B5]",
  twitter: "text-slate-800",
  instagram: "text-[#E1306C]",
  facebook: "text-[#1877F2]"
};

export function BrandProfileCard({ profile }: BrandProfileCardProps) {
  const updateCompanyName = useDashboardStore((state) => state.updateCompanyName);
  const updateBrandProfile = useDashboardStore((state) => state.updateBrandProfile);

  const [draftName, setDraftName] = useState(profile.companyName);
  const [isEditingName, setIsEditingName] = useState(false);

  const [approvedText, setApprovedText] = useState(profile.approvedVocabulary.join(", "));
  const [bannedText, setBannedText] = useState(profile.bannedVocabulary.join(", "));

  const progressVariant = profile.completion >= 80 ? "bg-emerald-500" : "bg-amber-500";

  const timelineMax = useMemo(() => Math.max(...profile.postingFrequency), [profile.postingFrequency]);

  const saveInlineName = () => {
    const next = draftName.trim();
    if (!next) {
      setDraftName(profile.companyName);
      setIsEditingName(false);
      return;
    }
    updateCompanyName(next);
    setIsEditingName(false);
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between gap-4">
        <div>
          {isEditingName ? (
            <Input
              autoFocus
              value={draftName}
              onChange={(event) => setDraftName(event.target.value)}
              onBlur={saveInlineName}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  saveInlineName();
                }
              }}
              className="h-9 w-[220px]"
            />
          ) : (
            <button type="button" onClick={() => setIsEditingName(true)} className="inline-flex items-center gap-2 text-left">
              <CardTitle>{profile.companyName}</CardTitle>
              <PencilLine className="h-4 w-4 text-[var(--text-muted)]" />
            </button>
          )}
          <p className="mt-1 text-sm text-[var(--text-secondary)]">Brand profile and voice settings</p>
        </div>

        <Sheet>
          <SheetTrigger asChild>
            <Button variant="outline">Edit Profile</Button>
          </SheetTrigger>
          <SheetContent side="right" className="w-full sm:max-w-lg">
            <SheetHeader>
              <SheetTitle>Edit Brand Profile</SheetTitle>
              <SheetDescription>Update voice constraints used by AI generation.</SheetDescription>
            </SheetHeader>

            <div className="mt-4 space-y-4">
              <div className="space-y-2">
                <p className="label-xs">Approved Vocabulary</p>
                <Textarea value={approvedText} onChange={(event) => setApprovedText(event.target.value)} />
              </div>
              <div className="space-y-2">
                <p className="label-xs">Banned Vocabulary</p>
                <Textarea value={bannedText} onChange={(event) => setBannedText(event.target.value)} />
              </div>
            </div>

            <SheetFooter>
              <Button
                onClick={() => {
                  const approved = approvedText
                    .split(",")
                    .map((token) => token.trim())
                    .filter(Boolean);
                  const banned = bannedText
                    .split(",")
                    .map((token) => token.trim())
                    .filter(Boolean);
                  updateBrandProfile({ approvedVocabulary: approved, bannedVocabulary: banned });
                }}
              >
                <Save className="h-4 w-4" />
                Save Changes
              </Button>
            </SheetFooter>
          </SheetContent>
        </Sheet>
      </CardHeader>

      <CardContent className="space-y-6">
        <div className="space-y-2">
          <p className="label-xs">Connected Platforms</p>
          <div className="flex flex-wrap gap-2">
            {profile.platforms.map((platform) => {
              const PlatformIcon = platformIcons[platform];
              return (
                <Badge key={platform} variant="outline" className="gap-1.5 rounded-full px-3 py-1 text-xs">
                  <PlatformIcon className={`h-3.5 w-3.5 ${platformColors[platform]}`} />
                  {platform}
                </Badge>
              );
            })}
          </div>
        </div>

        <div className="space-y-2">
          <p className="label-xs">Posting Frequency</p>
          <div className="grid grid-cols-7 gap-1">
            {profile.postingFrequency.map((value, idx) => (
              <div key={`${idx}-${value}`} className="rounded-lg border border-[var(--border)] p-2">
                <div className="h-16 w-full rounded bg-[var(--bg-elevated)] p-1">
                  <div
                    className="w-full rounded bg-[var(--brand-primary)]"
                    style={{ height: `${Math.max((value / timelineMax) * 100, 8)}%`, marginTop: `${100 - Math.max((value / timelineMax) * 100, 8)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-2">
          <p className="label-xs">Brand Colors</p>
          <div className="flex items-center gap-3">
            {profile.colors.map((color) => (
              <div key={color} className="flex items-center gap-2 rounded-full border border-[var(--border)] px-2 py-1">
                <span className="h-4 w-4 rounded-full border border-white/40" style={{ backgroundColor: color }} />
                <span className="font-mono text-xs text-[var(--text-secondary)]">{color}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          <div className="space-y-2">
            <p className="label-xs">Approved</p>
            <div className="flex flex-wrap gap-2">
              {profile.approvedVocabulary.map((word) => (
                <Badge key={word} variant="success" className="rounded-full">
                  {word}
                </Badge>
              ))}
            </div>
          </div>
          <div className="space-y-2">
            <p className="label-xs">Banned</p>
            <div className="flex flex-wrap gap-2">
              {profile.bannedVocabulary.map((word) => (
                <Badge key={word} variant="danger" className="rounded-full line-through">
                  {word}
                </Badge>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-[var(--text-secondary)]">Profile {profile.completion}% complete</span>
            <span className="font-semibold">{profile.completion}%</span>
          </div>
          <div className="h-2 w-full rounded-full bg-[var(--bg-elevated)]">
            <div className={`${progressVariant} h-full rounded-full transition-all`} style={{ width: `${profile.completion}%` }} />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
