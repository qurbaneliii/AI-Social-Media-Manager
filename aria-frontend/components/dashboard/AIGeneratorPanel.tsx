"use client";

import { useMemo, useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { AnimatePresence, motion } from "framer-motion";
import { Check, Copy, Loader2, RefreshCw, Save } from "lucide-react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { Textarea } from "@/components/ui/textarea";
import { useSaveDraftPost } from "@/hooks/useSaveDraftPost";
import { aiCtaOptions, aiPlatformOptions, aiToneOptions, platformCharacterLimits, platformLabels } from "@/lib/mock-data";
import { getClientSession } from "@/lib/client-session";
import { useDashboardStore } from "@/lib/store";
import { useCompanyStore } from "@/stores/useCompanyStore";
import { generateFormSchema, type GenerateFormValues, useGenerate } from "@/hooks/useGenerate";

export function AIGeneratorPanel() {
  const brandProfile = useDashboardStore((state) => state.brandProfile);
  const companyId = useCompanyStore((state) => state.companyId) ?? getClientSession().companyId;
  const saveDraftMutation = useSaveDraftPost();

  const [copied, setCopied] = useState(false);

  const {
    isGenerating,
    output,
    error,
    hashtags,
    run,
    regenerate,
    setOutput
  } = useGenerate();

  const form = useForm<GenerateFormValues>({
    resolver: zodResolver(generateFormSchema),
    defaultValues: {
      platform: "linkedin",
      tone: "Professional",
      topic: "",
      cta: "Learn More",
      context: ""
    }
  });

  const selectedPlatform = form.watch("platform");
  const charLimit = platformCharacterLimits[selectedPlatform];
  const usage = output.length;
  const usageRatio = Math.min((usage / charLimit) * 100, 100);

  const progressColor = usageRatio > 85 ? "bg-red-500" : usageRatio > 65 ? "bg-amber-500" : "bg-[var(--brand-primary)]";

  const platformPreviewClass = useMemo(() => {
    switch (selectedPlatform) {
      case "linkedin":
        return "border-[#0077B5]/30";
      case "twitter":
        return "border-slate-500/30";
      default:
        return "border-pink-500/30";
    }
  }, [selectedPlatform]);

  const onSubmit = form.handleSubmit(async (values) => {
    try {
      await run({
        ...values,
        context: values.context?.trim() || undefined,
        brandVocab: {
          approved: brandProfile.approvedVocabulary,
          banned: brandProfile.bannedVocabulary,
          brandName: brandProfile.companyName
        }
      });
      toast.success("Content generated!");
    } catch {
      toast.error("Generation failed. Try again.");
    }
  });

  return (
    <Card>
      <CardHeader className="rounded-t-2xl bg-gradient-to-r from-teal-700 via-teal-600 to-sky-700 text-white">
        <div className="flex items-center justify-between gap-3">
          <div>
            <CardTitle className="text-white">AI Content Studio</CardTitle>
            <p className="mt-1 text-xs text-white/80">Generate platform-optimized posts with brand-safe vocabulary.</p>
          </div>

          {isGenerating ? (
            <div className="inline-flex items-center gap-1 rounded-full bg-white/15 px-3 py-1 text-xs">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-white" />
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-white [animation-delay:140ms]" />
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-white [animation-delay:280ms]" />
              <span className="ml-1">Generating</span>
            </div>
          ) : null}
        </div>
      </CardHeader>

      <CardContent className="space-y-5 pt-5">
        <form onSubmit={onSubmit} className="space-y-4">
          <div className="space-y-2">
            <p className="label-xs">Platform</p>
            <ToggleGroup
              type="single"
              value={selectedPlatform}
              onValueChange={(value) => {
                if (value) {
                  form.setValue("platform", value as GenerateFormValues["platform"]);
                }
              }}
              className="flex flex-wrap"
            >
              {aiPlatformOptions.map((platform) => (
                <ToggleGroupItem key={platform} value={platform} variant="outline" className="rounded-full px-4">
                  {platformLabels[platform]}
                </ToggleGroupItem>
              ))}
            </ToggleGroup>
          </div>

          <div className="space-y-2">
            <p className="label-xs">Tone</p>
            <ToggleGroup
              type="single"
              value={form.watch("tone")}
              onValueChange={(value) => {
                if (value) {
                  form.setValue("tone", value);
                }
              }}
              className="flex flex-wrap"
            >
              {aiToneOptions.map((tone) => (
                <ToggleGroupItem key={tone} value={tone} variant="outline" className="rounded-full px-4">
                  {tone}
                </ToggleGroupItem>
              ))}
            </ToggleGroup>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-2 sm:col-span-2">
              <p className="label-xs">Topic</p>
              <Input placeholder="Write your campaign topic..." {...form.register("topic")} />
              {form.formState.errors.topic ? (
                <p className="text-xs text-red-500">{form.formState.errors.topic.message}</p>
              ) : null}
            </div>

            <div className="space-y-2">
              <p className="label-xs">CTA</p>
              <Select value={form.watch("cta")} onValueChange={(value) => form.setValue("cta", value)}>
                <SelectTrigger>
                  <SelectValue placeholder="Select CTA" />
                </SelectTrigger>
                <SelectContent>
                  {aiCtaOptions.map((cta) => (
                    <SelectItem key={cta} value={cta}>
                      {cta}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <details className="rounded-xl border border-[var(--border)] p-3">
            <summary className="cursor-pointer text-sm font-medium">Add Context (optional)</summary>
            <Textarea
              className="mt-3"
              rows={4}
              placeholder="Add campaign context, target audience, or product details..."
              {...form.register("context")}
            />
          </details>

          <div className="flex flex-wrap items-center gap-2">
            <Button type="submit" disabled={isGenerating}>
              {isGenerating ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
              Generate
            </Button>

            {output ? (
              <Button
                type="button"
                variant="ghost"
                onClick={async () => {
                  try {
                    await regenerate();
                    toast.success("Content generated!");
                  } catch {
                    toast.error("Generation failed. Try again.");
                  }
                }}
              >
                <RefreshCw className="h-4 w-4" />
                Regenerate
              </Button>
            ) : null}

            <Button
              type="button"
              variant="outline"
              disabled={!output}
              onClick={async () => {
                await navigator.clipboard.writeText(output);
                setCopied(true);
                toast.info("Copied to clipboard");
                setTimeout(() => setCopied(false), 1200);
              }}
            >
              {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
              Copy
            </Button>

            <Button
              type="button"
              variant="outline"
              disabled={!output || saveDraftMutation.isPending}
              onClick={async () => {
                if (!companyId) {
                  toast.error("Company profile is required before saving drafts.");
                  return;
                }

                try {
                  await saveDraftMutation.mutateAsync({
                    company_id: companyId,
                    platform: selectedPlatform,
                    content: output,
                    topic: form.getValues("topic"),
                    tone: form.getValues("tone"),
                    cta: form.getValues("cta"),
                    intent: "engage"
                  });
                  toast.success("Saved as draft");
                } catch (error) {
                  const message = error instanceof Error ? error.message : "Failed to save draft";
                  toast.error(message);
                }
              }}
            >
              {saveDraftMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
              Save as Draft
            </Button>
          </div>
        </form>

        <div className="space-y-4 rounded-xl border border-[var(--border)] bg-[color-mix(in_srgb,var(--bg-elevated)_58%,transparent)] p-4">
          <div className="flex items-center justify-between text-xs text-[var(--text-secondary)]">
            <span>Output</span>
            <span>
              {usage}/{charLimit}
            </span>
          </div>

          <div className="h-1.5 w-full rounded-full bg-[var(--bg-surface)]">
            <div className={`h-full rounded-full transition-all ${progressColor}`} style={{ width: `${usageRatio}%` }} />
          </div>

          <AnimatePresence mode="wait">
            <motion.div
              key={output || "empty"}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.2 }}
              className="min-h-[140px] whitespace-pre-wrap rounded-lg border border-[var(--border)] bg-[var(--bg-surface)] p-3 text-sm leading-6 text-[var(--text-secondary)]"
            >
              {output || "Your generated post will appear here..."}
            </motion.div>
          </AnimatePresence>

          {hashtags.length ? (
            <div className="flex flex-wrap gap-2">
              {hashtags.map((tag) => (
                <Badge
                  key={tag}
                  variant="info"
                  className="cursor-pointer"
                  onClick={() => setOutput((prev) => `${prev} ${tag}`.trim())}
                >
                  {tag}
                </Badge>
              ))}
            </div>
          ) : null}

          <div className={`rounded-xl border bg-[var(--bg-surface)] p-3 ${platformPreviewClass}`}>
            <p className="label-xs">Platform Preview</p>
            <div className="mt-2 rounded-xl border border-[var(--border)] bg-[color-mix(in_srgb,var(--bg-surface)_92%,transparent)] p-3">
              <div className="flex items-center gap-2">
                <div className="h-8 w-8 rounded-full bg-gradient-to-br from-teal-500 to-sky-500" />
                <div>
                  <p className="text-sm font-semibold">{brandProfile.companyName}</p>
                  <p className="text-[11px] text-[var(--text-muted)]">{platformLabels[selectedPlatform]} • now</p>
                </div>
              </div>
              <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-[var(--text-secondary)]">
                {output || "Preview is shown after generation."}
              </p>
            </div>
          </div>

          {error ? <p className="text-xs text-red-500">{error}</p> : null}
        </div>
      </CardContent>
    </Card>
  );
}
