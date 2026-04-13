// filename: app/(dashboard)/posts/new/page.tsx
// purpose: Post generation form with RHF+Zod validation.

"use client";

import Link from "next/link";
import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { toast } from "sonner";

import { FileDropzone } from "@/components/ui/FileDropzone";
import { PLATFORM_CHAR_LIMITS } from "@/config/constants";
import { TagInput } from "@/components/ui/TagInput";
import { useAuth } from "@/context/AuthContext";
import { useGeneratePost } from "@/hooks/useGeneratePost";
import { usePresignUpload } from "@/hooks/usePresignUpload";
import { getClientSession } from "@/lib/client-session";
import { IS_STATIC } from "@/lib/isStatic";
import { navigateTo } from "@/lib/navigate";
import { mockCompanyProfile } from "@/lib/mockData";
import { GeneratePostSchema } from "@/lib/zod-schemas";
import {
  analyzeContent,
  generateBatch,
  generateContent,
  improveContent,
  suggestHashtags,
  suggestTopics,
  type AIAnalyzeContentResponse,
  type AIGenerateBatchResult,
  type AIPlatform
} from "@/services/aiService";
import { useCompanyStore } from "@/stores/useCompanyStore";
import { usePostStore } from "@/stores/usePostStore";
import type { GeneratePostForm, Platform, PostIntent, UserRole } from "@/types";

const platforms: Platform[] = ["instagram", "linkedin", "facebook", "x", "tiktok", "pinterest"];
const intents: PostIntent[] = ["announce", "educate", "promote", "engage", "inspire", "crisis_response"];

const roleDefaultIntent: Record<UserRole, PostIntent> = {
  agency_admin: "promote",
  brand_manager: "announce",
  content_creator: "engage",
  analyst: "educate"
};

const toAIPlatform = (platform: Platform): AIPlatform => {
  return platform === "x" ? "twitter" : platform;
};

const toPlatform = (platform: AIPlatform): Platform => {
  return platform === "twitter" ? "x" : platform;
};

const getFriendlyAiError = (error: unknown): string => {
  if (!(error instanceof Error)) {
    return "Failed to generate content. Please try again.";
  }

  const message = error.message.toLowerCase();
  if (message.includes("quota") || message.includes("rate") || message.includes("temporarily") || message.includes("503")) {
    return "OpenAI service is temporarily unavailable.";
  }

  return "Failed to generate content. Please try again.";
};

export default function NewPostPage() {
  const companyId = useCompanyStore((s) => s.companyId) ?? getClientSession().companyId;
  const profile = useCompanyStore((s) => s.profile);
  const { user } = useAuth();
  const setDraftForm = usePostStore((s) => s.setDraftForm);
  const generateMutation = useGeneratePost();
  const upload = usePresignUpload();

  const [didPrefillFromProfile, setDidPrefillFromProfile] = useState(false);
  const [aiPlatform, setAiPlatform] = useState<AIPlatform>("linkedin");
  const [isGeneratingAI, setIsGeneratingAI] = useState(false);
  const [isBatchGenerating, setIsBatchGenerating] = useState(false);
  const [isImproving, setIsImproving] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isSuggestingHashtags, setIsSuggestingHashtags] = useState(false);
  const [isSuggestingTopics, setIsSuggestingTopics] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);
  const [generatedContent, setGeneratedContent] = useState("");
  const [improvedContent, setImprovedContent] = useState("");
  const [improveInstruction, setImproveInstruction] = useState("Make it sharper and more action-oriented.");
  const [analysis, setAnalysis] = useState<AIAnalyzeContentResponse | null>(null);
  const [hashtags, setHashtags] = useState<string[]>([]);
  const [topics, setTopics] = useState<string[]>([]);
  const [batchResults, setBatchResults] = useState<AIGenerateBatchResult[]>([]);

  const resolvedCompanyProfile = profile
    ? {
        platforms: platforms.filter((platform) => profile.platform_presence[platform]).map(toAIPlatform),
        postingFrequency: profile.posting_frequency_goal,
        ctaTypes: profile.primary_cta_types,
        brandColors: profile.brand_color_hex_codes,
        approvedVocabulary: profile.approved_vocabulary_list,
        bannedVocabulary: profile.banned_vocabulary_list,
        companyName: profile.company_name,
        industry: profile.industry_vertical,
        targetMarket: profile.target_market,
        tone: profile.tone_of_voice_descriptors
      }
    : IS_STATIC
      ? mockCompanyProfile
      : null;

  const form = useForm<GeneratePostForm>({
    resolver: zodResolver(GeneratePostSchema),
    defaultValues: {
      company_id: companyId ?? "",
      post_intent: "announce",
      core_message: "",
      target_platforms: ["linkedin"],
      campaign_tag: "",
      attached_media_id: undefined,
      manual_keywords: [],
      urgency_level: "immediate",
      requested_publish_at: undefined
    }
  });

  useEffect(() => {
    if ((!profile && !IS_STATIC) || didPrefillFromProfile) {
      return;
    }

    const activePlatforms = profile
      ? platforms.filter((platform) => profile.platform_presence[platform])
      : mockCompanyProfile.platforms.map((platform) => (platform === "twitter" ? "x" : platform as Platform));
    if (activePlatforms.length > 0) {
      form.setValue("target_platforms", activePlatforms, { shouldValidate: true });
      setAiPlatform(toAIPlatform(activePlatforms[0]));
    }

    const approved = profile?.approved_vocabulary_list ?? [...mockCompanyProfile.approvedVocabulary];
    if (approved.length > 0) {
      form.setValue("manual_keywords", approved.slice(0, 8), { shouldValidate: true });
    }

    if (user?.role) {
      form.setValue("post_intent", roleDefaultIntent[user.role], { shouldValidate: true });
    }

    setDidPrefillFromProfile(true);
  }, [didPrefillFromProfile, form, profile, user?.role]);

  if (!companyId) {
    return <div className="rounded-xl border bg-white p-6 text-sm text-red-700">Company ID is required. Return to sign in.</div>;
  }

  const selectedTargets = form.watch("target_platforms");
  const strictestLimit = selectedTargets.length
    ? Math.min(...selectedTargets.map((platform) => PLATFORM_CHAR_LIMITS[platform]))
    : 0;
  const coreMessageLength = form.watch("core_message").length;
  const aiResult = improvedContent || generatedContent;

  const buildGeneratePayload = (platformOverride?: AIPlatform) => {
    if (!resolvedCompanyProfile) {
      return null;
    }

    const resolvedPlatform = platformOverride ?? aiPlatform;
    const frontendPlatform = toPlatform(resolvedPlatform);
    const topic =
      form.getValues("core_message").trim() || `${profile?.company_name ?? "Preview Company"} update`;

    return {
      platform: resolvedPlatform,
      topic,
      tone: profile ? profile.tone_of_voice_descriptors.join(", ") || "professional" : "professional",
      ctaType: (profile?.primary_cta_types[0] ?? mockCompanyProfile.ctaTypes[0]) as any,
      brandColors: profile?.brand_color_hex_codes ?? [...mockCompanyProfile.brandColors],
      approvedVocabulary: profile?.approved_vocabulary_list ?? [...mockCompanyProfile.approvedVocabulary],
      bannedVocabulary: profile?.banned_vocabulary_list ?? [...mockCompanyProfile.bannedVocabulary],
      postingFrequency: profile
        ? profile.posting_frequency_goal[frontendPlatform]
        : mockCompanyProfile.postingFrequency[frontendPlatform === "x" ? "twitter" : "linkedin"],
      companyProfile: {
        companyId,
        ...resolvedCompanyProfile,
        selectedPlatforms: selectedTargets,
        userRole: user?.role ?? null
      }
    };
  };

  const handleGenerateWithAI = async () => {
    const payload = buildGeneratePayload();
    if (!payload) {
      setAiError("Complete your company profile for better AI results");
      return;
    }

    setAiError(null);
    setIsGeneratingAI(true);
    try {
      const response = await generateContent(payload);
      setGeneratedContent(response.content);
      setImprovedContent("");
      setAnalysis(null);
      setHashtags([]);
      toast.success("AI content generated");
    } catch (error) {
      setAiError(getFriendlyAiError(error));
    } finally {
      setIsGeneratingAI(false);
    }
  };

  const handleBatchGenerate = async () => {
    if (!resolvedCompanyProfile) {
      setAiError("Complete your company profile for better AI results");
      return;
    }

    const targetPlatforms = selectedTargets.length > 0 ? selectedTargets : [toPlatform(aiPlatform)];
    const payloads = targetPlatforms
      .map((platform) => buildGeneratePayload(toAIPlatform(platform)))
      .filter((item): item is NonNullable<typeof item> => item !== null);

    if (!payloads.length) {
      setAiError("Select at least one platform to generate batch content");
      return;
    }

    setAiError(null);
    setIsBatchGenerating(true);
    try {
      const response = await generateBatch(payloads);
      setBatchResults(response.results);

      const firstSuccess = response.results.find((item) => item.success && item.content);
      if (firstSuccess?.content) {
        setGeneratedContent(firstSuccess.content);
        setImprovedContent("");
        setAiPlatform(firstSuccess.platform);
      }
      toast.success("Batch generation completed");
    } catch (error) {
      setAiError(getFriendlyAiError(error));
    } finally {
      setIsBatchGenerating(false);
    }
  };

  const handleImproveContent = async () => {
    if (!aiResult.trim()) {
      setAiError("Generate content first before improving it");
      return;
    }

    setAiError(null);
    setIsImproving(true);
    try {
      const response = await improveContent({ content: aiResult, instruction: improveInstruction });
      setImprovedContent(response.improved);
      toast.success("Content improved");
    } catch (error) {
      setAiError(getFriendlyAiError(error));
    } finally {
      setIsImproving(false);
    }
  };

  const handleAnalyzeContent = async () => {
    if (!aiResult.trim()) {
      setAiError("Generate content first before analyzing it");
      return;
    }

    setAiError(null);
    setIsAnalyzing(true);
    try {
      const response = await analyzeContent({ content: aiResult, platform: aiPlatform });
      setAnalysis(response);
    } catch (error) {
      setAiError(getFriendlyAiError(error));
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleSuggestHashtags = async () => {
    if (!aiResult.trim()) {
      setAiError("Generate content first before suggesting hashtags");
      return;
    }

    setAiError(null);
    setIsSuggestingHashtags(true);
    try {
      const response = await suggestHashtags({ content: aiResult, platform: aiPlatform });
      setHashtags(response.hashtags);
    } catch (error) {
      setAiError(getFriendlyAiError(error));
    } finally {
      setIsSuggestingHashtags(false);
    }
  };

  const handleSuggestTopics = async () => {
    if (!resolvedCompanyProfile) {
      setAiError("Complete your company profile for better AI results");
      return;
    }

    const platformsForTopicRequest =
      selectedTargets.length > 0 ? selectedTargets.map(toAIPlatform) : [aiPlatform];

    setAiError(null);
    setIsSuggestingTopics(true);
    try {
      const response = await suggestTopics({
        industry: profile?.industry_vertical ?? "marketing",
        platforms: platformsForTopicRequest,
        companyProfile: {
          companyId,
          companyName: profile?.company_name ?? "Preview Company",
          userRole: user?.role ?? null,
          targetMarket: profile?.target_market ?? {},
          tone: profile?.tone_of_voice_descriptors ?? ["professional"]
        }
      });
      setTopics(response.topics);
    } catch (error) {
      setAiError(getFriendlyAiError(error));
    } finally {
      setIsSuggestingTopics(false);
    }
  };

  const copyResultToClipboard = async () => {
    if (!aiResult.trim()) {
      return;
    }

    try {
      await navigator.clipboard.writeText(aiResult);
      toast.success("Generated content copied");
    } catch {
      toast.error("Could not copy content");
    }
  };

  return (
    <main className="space-y-6 rounded-2xl border bg-white p-6">
      <header>
        <h1 className="text-2xl font-semibold text-slate-900">Generate post</h1>
        <p className="text-sm text-slate-600">Create intent-aligned variants, hashtags, audience definition, timing, and SEO metadata.</p>
      </header>

      <form
        className="space-y-5"
        onSubmit={form.handleSubmit(async (payload) => {
          const fullPayload = { ...payload, company_id: companyId };
          setDraftForm(fullPayload);
          const res = await generateMutation.mutateAsync(fullPayload);
          navigateTo(`/posts/${res.post_id}/result`);
        })}
      >
        <label className="block space-y-1 text-sm">
          <span className="text-slate-700">Post intent</span>
          <div className="flex flex-wrap gap-2">
            {intents.map((intent) => (
              <button
                key={intent}
                type="button"
                onClick={() => form.setValue("post_intent", intent, { shouldValidate: true })}
                className={`rounded-full px-3 py-1 text-xs ${form.watch("post_intent") === intent ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-700"}`}
              >
                {intent}
              </button>
            ))}
          </div>
        </label>

        <label className="block space-y-1 text-sm">
          <div className="flex items-center justify-between">
            <span className="text-slate-700">Core message</span>
            <span className={`text-xs ${strictestLimit > 0 && coreMessageLength > strictestLimit ? "text-red-600" : "text-slate-500"}`}>
              {coreMessageLength}/{strictestLimit || 500}
            </span>
          </div>
          <textarea {...form.register("core_message")} rows={5} className="w-full rounded-lg border px-3 py-2" />
          {strictestLimit > 0 && coreMessageLength > strictestLimit ? (
            <p className="text-xs text-red-600">Core message exceeds strictest selected platform limit by {coreMessageLength - strictestLimit} characters.</p>
          ) : null}
        </label>

        <div className="space-y-2">
          <p className="text-sm font-medium text-slate-700">Target platforms</p>
          <div className="flex flex-wrap gap-2">
            {platforms.map((platform) => {
              const selected = form.watch("target_platforms").includes(platform);
              return (
                <button
                  type="button"
                  key={platform}
                  onClick={() => {
                    const next = selected
                      ? form.getValues("target_platforms").filter((p) => p !== platform)
                      : [...form.getValues("target_platforms"), platform];
                    form.setValue("target_platforms", next, { shouldValidate: true });
                  }}
                  className={`rounded-full px-3 py-1 text-xs capitalize ${selected ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-700"}`}
                >
                  {platform} ({PLATFORM_CHAR_LIMITS[platform]})
                </button>
              );
            })}
          </div>
        </div>

        <section className="space-y-4 rounded-xl border border-teal-200 bg-teal-50/50 p-4">
          <header className="space-y-1">
            <h2 className="text-sm font-semibold text-teal-900">AI Content Studio</h2>
            <p className="text-xs text-teal-800">
              Generate, improve, analyze, and optimize copy using your company profile constraints.
            </p>
          </header>

          {!resolvedCompanyProfile ? (
            <p className="rounded-lg border border-amber-300 bg-amber-50 px-3 py-2 text-xs text-amber-800">
              Complete your company profile for better AI results. {" "}
              <Link href="/onboarding/company-profile" className="font-medium underline">
                Go to company profile settings
              </Link>
            </p>
          ) : IS_STATIC ? (
            <p className="rounded-lg border border-sky-300 bg-sky-50 px-3 py-2 text-xs text-sky-800">
              Preview mode: AI actions are using mock/static responses.
            </p>
          ) : null}

          <label className="block space-y-1 text-sm">
            <span className="text-slate-700">AI platform</span>
            <select
              value={aiPlatform}
              onChange={(event) => setAiPlatform(event.target.value as AIPlatform)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
            >
              {platforms.map((platform) => {
                const value = toAIPlatform(platform);
                return (
                  <option key={platform} value={value}>
                    {platform}
                  </option>
                );
              })}
            </select>
          </label>

          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={handleGenerateWithAI}
              disabled={isGeneratingAI}
              className="rounded-lg bg-teal-700 px-3 py-2 text-xs font-medium text-white disabled:opacity-60"
            >
              {isGeneratingAI ? "Generating..." : "Create with AI"}
            </button>

            <button
              type="button"
              onClick={handleBatchGenerate}
              disabled={isBatchGenerating}
              className="rounded-lg bg-slate-900 px-3 py-2 text-xs font-medium text-white disabled:opacity-60"
            >
              {isBatchGenerating ? "Generating batch..." : "Generate batch"}
            </button>

            <button
              type="button"
              onClick={handleGenerateWithAI}
              disabled={isGeneratingAI || !aiResult}
              className="rounded-lg border border-slate-300 px-3 py-2 text-xs font-medium text-slate-700 disabled:opacity-60"
            >
              Regenerate
            </button>
          </div>

          {aiError ? <p className="text-xs text-red-700">{aiError}</p> : null}

          {aiResult ? (
            <div className="space-y-2">
              <label className="block text-xs font-medium text-slate-700">Generated content</label>
              <textarea
                readOnly
                value={aiResult}
                rows={6}
                className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800"
              />
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={copyResultToClipboard}
                  className="rounded-lg border border-slate-300 px-3 py-2 text-xs font-medium text-slate-700"
                >
                  Copy
                </button>
                <button
                  type="button"
                  onClick={() => form.setValue("core_message", aiResult.slice(0, 500), { shouldValidate: true })}
                  className="rounded-lg border border-slate-300 px-3 py-2 text-xs font-medium text-slate-700"
                >
                  Use as core message
                </button>
              </div>
            </div>
          ) : null}

          <label className="block space-y-1 text-sm">
            <span className="text-slate-700">Improve instruction</span>
            <input
              value={improveInstruction}
              onChange={(event) => setImproveInstruction(event.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
              placeholder="Example: Make this more concise and high-converting"
            />
          </label>

          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={handleImproveContent}
              disabled={isImproving || !aiResult}
              className="rounded-lg border border-slate-300 px-3 py-2 text-xs font-medium text-slate-700 disabled:opacity-60"
            >
              {isImproving ? "Improving..." : "Improve content"}
            </button>

            <button
              type="button"
              onClick={handleAnalyzeContent}
              disabled={isAnalyzing || !aiResult}
              className="rounded-lg border border-slate-300 px-3 py-2 text-xs font-medium text-slate-700 disabled:opacity-60"
            >
              {isAnalyzing ? "Analyzing..." : "Analyze content"}
            </button>

            <button
              type="button"
              onClick={handleSuggestHashtags}
              disabled={isSuggestingHashtags || !aiResult}
              className="rounded-lg border border-slate-300 px-3 py-2 text-xs font-medium text-slate-700 disabled:opacity-60"
            >
              {isSuggestingHashtags ? "Suggesting..." : "Suggest hashtags"}
            </button>

            <button
              type="button"
              onClick={handleSuggestTopics}
              disabled={isSuggestingTopics}
              className="rounded-lg border border-slate-300 px-3 py-2 text-xs font-medium text-slate-700 disabled:opacity-60"
            >
              {isSuggestingTopics ? "Suggesting..." : "Suggest topics"}
            </button>
          </div>

          {analysis ? (
            <div className="rounded-lg border border-slate-200 bg-white p-3 text-xs text-slate-700">
              <p className="font-semibold text-slate-900">Quality analysis</p>
              <p>Engagement: {analysis.scores.engagement}</p>
              <p>Clarity: {analysis.scores.clarity}</p>
              <p>CTA strength: {analysis.scores.cta_strength}</p>
              <ul className="mt-2 list-disc pl-5">
                {analysis.suggestions.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          ) : null}

          {hashtags.length > 0 ? (
            <div className="rounded-lg border border-slate-200 bg-white p-3 text-xs text-slate-700">
              <p className="mb-2 font-semibold text-slate-900">Suggested hashtags</p>
              <div className="flex flex-wrap gap-2">
                {hashtags.map((tag) => (
                  <span key={tag} className="rounded-full bg-slate-100 px-2 py-1">
                    #{tag}
                  </span>
                ))}
              </div>
            </div>
          ) : null}

          {topics.length > 0 ? (
            <div className="rounded-lg border border-slate-200 bg-white p-3 text-xs text-slate-700">
              <p className="mb-2 font-semibold text-slate-900">Suggested topics</p>
              <ul className="list-disc pl-5">
                {topics.map((topic) => (
                  <li key={topic}>{topic}</li>
                ))}
              </ul>
            </div>
          ) : null}

          {batchResults.length > 0 ? (
            <div className="rounded-lg border border-slate-200 bg-white p-3 text-xs text-slate-700">
              <p className="mb-2 font-semibold text-slate-900">Batch generation results</p>
              <ul className="space-y-1">
                {batchResults.map((result, index) => (
                  <li key={`${result.platform}-${index}`}>
                    <span className="font-medium capitalize">{result.platform}:</span>{" "}
                    {result.success ? "Success" : result.error ?? "Failed"}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </section>

        <Controller
          control={form.control}
          name="manual_keywords"
          render={({ field }) => <TagInput label="Manual keywords" values={field.value ?? []} onChange={field.onChange} />}
        />

        <div className="grid gap-4 md:grid-cols-2">
          <label className="space-y-1 text-sm">
            <span className="text-slate-700">Campaign tag</span>
            <input {...form.register("campaign_tag")} className="w-full rounded-lg border px-3 py-2" />
          </label>

          <label className="space-y-1 text-sm">
            <span className="text-slate-700">Urgency</span>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => {
                  form.setValue("urgency_level", "scheduled", { shouldValidate: true });
                }}
                className={`rounded-full px-3 py-1 text-xs ${form.watch("urgency_level") === "scheduled" ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-700"}`}
              >
                Schedule later
              </button>
              <button
                type="button"
                onClick={() => {
                  form.setValue("urgency_level", "immediate", { shouldValidate: true });
                  form.setValue("requested_publish_at", undefined, { shouldValidate: true });
                }}
                className={`rounded-full px-3 py-1 text-xs ${form.watch("urgency_level") === "immediate" ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-700"}`}
              >
                Publish now
              </button>
            </div>
          </label>
        </div>

        {form.watch("urgency_level") === "scheduled" ? (
          <label className="block space-y-1 text-sm">
            <span className="text-slate-700">Requested publish time</span>
            <input
              type="datetime-local"
              onChange={(e) => {
                const value = e.target.value ? new Date(e.target.value).toISOString() : undefined;
                form.setValue("requested_publish_at", value, { shouldValidate: true });
              }}
              className="w-full rounded-lg border px-3 py-2"
            />
          </label>
        ) : null}

        <div className="space-y-2">
          <p className="text-sm font-medium text-slate-700">Attach media (optional)</p>
          <FileDropzone
            label="Upload media"
            onFiles={async (files) => {
              const file = files[0];
              if (!file) return;
              const assetId = await upload.upload({ company_id: companyId, file });
              form.setValue("attached_media_id", assetId, { shouldValidate: true });
            }}
            disabled={upload.isUploading}
          />
          {form.watch("attached_media_id") ? <p className="text-xs text-slate-600">Asset: {form.watch("attached_media_id")}</p> : null}
          {upload.error ? <p className="text-xs text-red-600">Upload failed. Please retry.</p> : null}
        </div>

        <button
          type="submit"
          disabled={generateMutation.isPending}
          className="rounded-lg bg-teal-700 px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
        >
          {generateMutation.isPending ? "Generating..." : "Generate post"}
        </button>
      </form>
    </main>
  );
}
