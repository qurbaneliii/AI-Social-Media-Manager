// filename: app/(dashboard)/posts/new/page.tsx
// purpose: Guided post generation wizard with autosave and AI-assisted drafting.

"use client";

import Link from "next/link";
import { zodResolver } from "@hookform/resolvers/zod";
import { CheckCircle2, Clock3, Loader2, RotateCcw, Sparkles, WandSparkles } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { toast } from "sonner";

import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { EmptyStateCard } from "@/components/ui/EmptyStateCard";
import { SkeletonBlock } from "@/components/ui/SkeletonBlock";
import { FileDropzone } from "@/components/ui/FileDropzone";
import { TagInput } from "@/components/ui/TagInput";
import { PLATFORM_CHAR_LIMITS } from "@/config/constants";
import { useAuth } from "@/context/AuthContext";
import { useGeneratePost } from "@/hooks/useGeneratePost";
import { usePresignUpload } from "@/hooks/usePresignUpload";
import { getClientSession } from "@/lib/client-session";
import { IS_STATIC } from "@/lib/isStatic";
import { mockCompanyProfile } from "@/lib/mockData";
import { navigateTo } from "@/lib/navigate";
import { GeneratePostSchema } from "@/lib/zod-schemas";
import {
  analyzeContent,
  generateBatch,
  generateContent,
  improveContent,
  suggestHashtags,
  suggestTopics,
  type AICtaType,
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

const wizardSteps = [
  {
    id: 1,
    title: "Topic + Platforms",
    description: "Define intent, message, targeting, and publishing urgency."
  },
  {
    id: 2,
    title: "AI Draft",
    description: "Generate platform-aligned drafts and quick alternatives."
  },
  {
    id: 3,
    title: "Review + Refine",
    description: "Polish language, run analysis, and enrich with hashtags."
  },
  {
    id: 4,
    title: "Confirm + Generate",
    description: "Validate summary and generate the full package."
  }
] as const;

const UUID_REGEX =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

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

interface NewPostDraftCache {
  form: Partial<GeneratePostForm>;
  step: number;
  aiPlatform: AIPlatform;
  contentDraft: string;
  improveInstruction: string;
}

export default function NewPostPage() {
  const companyId = useCompanyStore((s) => s.companyId) ?? getClientSession().companyId;
  const profile = useCompanyStore((s) => s.profile);
  const { user } = useAuth();
  const setDraftForm = usePostStore((s) => s.setDraftForm);
  const generateMutation = useGeneratePost();
  const upload = usePresignUpload();

  const [didPrefillFromProfile, setDidPrefillFromProfile] = useState(false);
  const [didHydrateDraft, setDidHydrateDraft] = useState(false);
  const [lastSavedAt, setLastSavedAt] = useState<number | null>(null);
  const [activeStep, setActiveStep] = useState(1);
  const [showResetConfirm, setShowResetConfirm] = useState(false);

  const [aiPlatform, setAiPlatform] = useState<AIPlatform>("linkedin");
  const [isGeneratingAI, setIsGeneratingAI] = useState(false);
  const [isBatchGenerating, setIsBatchGenerating] = useState(false);
  const [isImproving, setIsImproving] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isSuggestingHashtags, setIsSuggestingHashtags] = useState(false);
  const [isSuggestingTopics, setIsSuggestingTopics] = useState(false);

  const [aiError, setAiError] = useState<string | null>(null);
  const [contentDraft, setContentDraft] = useState("");
  const [improveInstruction, setImproveInstruction] = useState("Make it sharper and more action-oriented.");
  const [analysis, setAnalysis] = useState<AIAnalyzeContentResponse | null>(null);
  const [hashtags, setHashtags] = useState<string[]>([]);
  const [topics, setTopics] = useState<string[]>([]);
  const [batchResults, setBatchResults] = useState<AIGenerateBatchResult[]>([]);

  const companyIdForValidation = useMemo(() => {
    if (!companyId) {
      return "";
    }

    if (UUID_REGEX.test(companyId)) {
      return companyId;
    }

    return IS_STATIC ? "00000000-0000-4000-8000-000000000000" : companyId;
  }, [companyId]);

  const defaultValues = useMemo<GeneratePostForm>(
    () => ({
      company_id: companyIdForValidation,
      post_intent: "announce",
      core_message: "",
      target_platforms: ["linkedin"],
      campaign_tag: "",
      attached_media_id: undefined,
      manual_keywords: [],
      urgency_level: "immediate",
      requested_publish_at: undefined
    }),
    [companyIdForValidation]
  );

  const form = useForm<GeneratePostForm>({
    resolver: zodResolver(GeneratePostSchema),
    mode: "onChange",
    defaultValues
  });

  const draftStorageKey = companyId ? `aria-new-post-draft:${companyId}` : null;

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

  useEffect(() => {
    if (!draftStorageKey || didHydrateDraft) {
      return;
    }

    const cachedRaw = localStorage.getItem(draftStorageKey);
    if (!cachedRaw) {
      setDidHydrateDraft(true);
      return;
    }

    try {
      const cached = JSON.parse(cachedRaw) as NewPostDraftCache;
      form.reset({
        ...defaultValues,
        ...cached.form,
        company_id: companyIdForValidation
      });

      if (cached.step >= 1 && cached.step <= 4) {
        setActiveStep(cached.step);
      }

      if (cached.aiPlatform) {
        setAiPlatform(cached.aiPlatform);
      }

      setContentDraft(cached.contentDraft ?? "");
      setImproveInstruction(cached.improveInstruction || "Make it sharper and more action-oriented.");
      setDidPrefillFromProfile(true);
      toast.success("Recovered your saved draft.");
    } catch {
      localStorage.removeItem(draftStorageKey);
    } finally {
      setDidHydrateDraft(true);
    }
  }, [companyIdForValidation, defaultValues, didHydrateDraft, draftStorageKey, form]);

  useEffect(() => {
    if ((!profile && !IS_STATIC) || didPrefillFromProfile) {
      return;
    }

    const activePlatforms = profile
      ? platforms.filter((platform) => profile.platform_presence[platform])
      : mockCompanyProfile.platforms.map((platform) => (platform === "twitter" ? "x" : (platform as Platform)));

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

  const watchedFormValues = form.watch();

  useEffect(() => {
    if (!draftStorageKey || !didHydrateDraft) {
      return;
    }

    const payload: NewPostDraftCache = {
      form: {
        ...watchedFormValues,
        company_id: companyIdForValidation
      },
      step: activeStep,
      aiPlatform,
      contentDraft,
      improveInstruction
    };

    localStorage.setItem(draftStorageKey, JSON.stringify(payload));
    setLastSavedAt(Date.now());
  }, [
    activeStep,
    aiPlatform,
    companyIdForValidation,
    contentDraft,
    didHydrateDraft,
    draftStorageKey,
    improveInstruction,
    watchedFormValues
  ]);

  if (!companyId) {
    return (
      <div className="rounded-xl border bg-white p-6 text-sm text-red-700">
        Company ID is required. Return to sign in.
      </div>
    );
  }

  const selectedTargets = form.watch("target_platforms");
  const manualKeywords = form.watch("manual_keywords") ?? [];
  const strictestLimit = selectedTargets.length
    ? Math.min(...selectedTargets.map((platform) => PLATFORM_CHAR_LIMITS[platform]))
    : 0;
  const coreMessage = form.watch("core_message");
  const coreMessageLength = coreMessage.length;
  const requestedPublishAt = form.watch("requested_publish_at");
  const isScheduled = form.watch("urgency_level") === "scheduled";

  const buildGeneratePayload = (platformOverride?: AIPlatform) => {
    if (!resolvedCompanyProfile) {
      return null;
    }

    const resolvedPlatform = platformOverride ?? aiPlatform;
    const frontendPlatform = toPlatform(resolvedPlatform);
    const topic = coreMessage.trim() || `${profile?.company_name ?? "Preview Company"} update`;
    const resolvedCtaType: AICtaType = (profile?.primary_cta_types[0] ?? mockCompanyProfile.ctaTypes[0]) as AICtaType;

    return {
      platform: resolvedPlatform,
      topic,
      tone: profile ? profile.tone_of_voice_descriptors.join(", ") || "professional" : "professional",
      ctaType: resolvedCtaType,
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

  const addKeywordSuggestion = (keyword: string) => {
    const normalized = keyword.replace(/^#/, "").trim();
    if (!normalized || manualKeywords.includes(normalized)) {
      return;
    }
    form.setValue("manual_keywords", [...manualKeywords, normalized], { shouldValidate: true });
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
      setContentDraft(response.content);
      setAnalysis(null);
      setHashtags([]);
      setBatchResults([]);
      toast.success("AI draft generated");
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
        setContentDraft(firstSuccess.content);
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
    if (!contentDraft.trim()) {
      setAiError("Generate content first before improving it");
      return;
    }

    setAiError(null);
    setIsImproving(true);
    try {
      const response = await improveContent({ content: contentDraft, instruction: improveInstruction });
      setContentDraft(response.improved);
      toast.success("Content improved");
    } catch (error) {
      setAiError(getFriendlyAiError(error));
    } finally {
      setIsImproving(false);
    }
  };

  const handleAnalyzeContent = async () => {
    if (!contentDraft.trim()) {
      setAiError("Generate content first before analyzing it");
      return;
    }

    setAiError(null);
    setIsAnalyzing(true);
    try {
      const response = await analyzeContent({ content: contentDraft, platform: aiPlatform });
      setAnalysis(response);
    } catch (error) {
      setAiError(getFriendlyAiError(error));
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleSuggestHashtags = async () => {
    if (!contentDraft.trim()) {
      setAiError("Generate content first before suggesting hashtags");
      return;
    }

    setAiError(null);
    setIsSuggestingHashtags(true);
    try {
      const response = await suggestHashtags({ content: contentDraft, platform: aiPlatform });
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

    const platformsForTopicRequest = selectedTargets.length > 0 ? selectedTargets.map(toAIPlatform) : [aiPlatform];

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
    if (!contentDraft.trim()) {
      return;
    }

    try {
      await navigator.clipboard.writeText(contentDraft);
      toast.success("Draft copied to clipboard");
    } catch {
      toast.error("Could not copy content");
    }
  };

  const goToNextStep = async () => {
    if (activeStep === 1) {
      // UX: Prevent navigation until required fields are valid so users immediately see what blocks progress.
      const valid = await form.trigger([
        "post_intent",
        "core_message",
        "target_platforms",
        "urgency_level",
        "requested_publish_at"
      ]);

      if (!valid) {
        toast.error("Complete required fields before continuing.");
        return;
      }
    }

    setActiveStep((prev) => Math.min(4, prev + 1));
  };

  const clearDraft = () => {
    form.reset(defaultValues);
    setContentDraft("");
    setImproveInstruction("Make it sharper and more action-oriented.");
    setAnalysis(null);
    setHashtags([]);
    setTopics([]);
    setBatchResults([]);
    setAiError(null);
    setActiveStep(1);

    if (draftStorageKey) {
      localStorage.removeItem(draftStorageKey);
    }

    setShowResetConfirm(false);
    toast.success("Draft reset");
  };

  const submitGenerateRequest = form.handleSubmit(async (payload) => {
    if (!IS_STATIC && !UUID_REGEX.test(companyId)) {
      toast.error("Company ID is invalid. Complete onboarding and try again.");
      return;
    }

    const fullPayload = {
      ...payload,
      company_id: companyId
    };

    setDraftForm(fullPayload);

    try {
      const res = await generateMutation.mutateAsync(fullPayload);
      if (draftStorageKey) {
        localStorage.removeItem(draftStorageKey);
      }
      navigateTo(`/posts/${res.post_id}/result`);
    } catch {
      // useGeneratePost already surfaces toast details.
    }
  });

  const saveHint = lastSavedAt
    ? `Saved ${new Date(lastSavedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`
    : "Autosave active";

  const canSubmit =
    form.formState.isValid &&
    selectedTargets.length > 0 &&
    coreMessageLength >= 20 &&
    (!isScheduled || Boolean(requestedPublishAt));

  return (
    <main className="space-y-6 rounded-3xl border border-emerald-100 bg-white/95 p-5 shadow-sm sm:p-6 aria-fade-in">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 sm:text-3xl">Content Generator</h1>
          <p className="mt-1 text-sm text-slate-600">
            Move through a guided flow: define context, draft with AI, refine, then generate your final package.
          </p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600">
          <p className="font-semibold text-slate-800">{saveHint}</p>
          <p className="mt-0.5">Step {activeStep} of {wizardSteps.length}</p>
        </div>
      </header>

      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
        {wizardSteps.map((step) => {
          const isActive = activeStep === step.id;
          const isComplete = activeStep > step.id;

          return (
            <button
              key={step.id}
              type="button"
              onClick={() => {
                if (step.id <= activeStep) {
                  setActiveStep(step.id);
                }
              }}
              className={`rounded-xl border px-3 py-3 text-left transition ${
                isActive
                  ? "border-emerald-300 bg-emerald-50"
                  : isComplete
                    ? "border-emerald-200 bg-emerald-50/50"
                    : "border-slate-200 bg-white"
              }`}
              aria-current={isActive ? "step" : undefined}
            >
              <p className="inline-flex items-center gap-1 text-xs font-semibold uppercase tracking-wide text-slate-500">
                {isComplete ? <CheckCircle2 className="h-3.5 w-3.5 text-emerald-700" /> : null}
                Step {step.id}
              </p>
              <p className="mt-1 text-sm font-semibold text-slate-900">{step.title}</p>
              <p className="mt-1 text-xs text-slate-600">{step.description}</p>
            </button>
          );
        })}
      </div>

      <form className="space-y-5" onSubmit={submitGenerateRequest}>
        {activeStep === 1 ? (
          <section className="space-y-4 rounded-2xl border border-slate-200 bg-white p-4 sm:p-5">
            <header className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="text-lg font-semibold text-slate-900">Topic + Platform Selection</h2>
              <p className="text-xs text-slate-500">Fields marked by validation must be completed before next step.</p>
            </header>

            <label className="block space-y-2 text-sm">
              <span className="font-medium text-slate-700">Post intent</span>
              <div className="flex flex-wrap gap-2">
                {intents.map((intent) => (
                  <button
                    key={intent}
                    type="button"
                    onClick={() => form.setValue("post_intent", intent, { shouldValidate: true })}
                    className={`rounded-full px-3 py-1 text-xs ${
                      form.watch("post_intent") === intent ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-700"
                    }`}
                  >
                    {intent}
                  </button>
                ))}
              </div>
            </label>

            <label className="block space-y-1.5 text-sm">
              <div className="flex items-center justify-between">
                <span className="font-medium text-slate-700">Core message</span>
                <span className={`text-xs ${strictestLimit > 0 && coreMessageLength > strictestLimit ? "text-red-600" : "text-slate-500"}`}>
                  {coreMessageLength}/{strictestLimit || 500}
                </span>
              </div>
              <textarea
                {...form.register("core_message")}
                rows={5}
                className="w-full rounded-lg border border-slate-300 px-3 py-2"
                aria-invalid={Boolean(form.formState.errors.core_message)}
              />
              {form.formState.errors.core_message?.message ? (
                <p className="text-xs text-red-600">{form.formState.errors.core_message.message}</p>
              ) : null}
              {strictestLimit > 0 && coreMessageLength > strictestLimit ? (
                <p className="text-xs text-red-600">
                  Core message exceeds strictest selected platform limit by {coreMessageLength - strictestLimit} characters.
                </p>
              ) : null}
            </label>

            <div className="space-y-2">
              <p className="text-sm font-medium text-slate-700">Target platforms</p>
              <div className="flex flex-wrap gap-2">
                {platforms.map((platform) => {
                  const selected = selectedTargets.includes(platform);
                  return (
                    <button
                      type="button"
                      key={platform}
                      onClick={() => {
                        const next = selected
                          ? form.getValues("target_platforms").filter((item) => item !== platform)
                          : [...form.getValues("target_platforms"), platform];
                        form.setValue("target_platforms", next, { shouldValidate: true });
                      }}
                      className={`rounded-full px-3 py-1 text-xs capitalize ${
                        selected ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-700"
                      }`}
                    >
                      {platform} ({PLATFORM_CHAR_LIMITS[platform]})
                    </button>
                  );
                })}
              </div>
              {form.formState.errors.target_platforms?.message ? (
                <p className="text-xs text-red-600">{form.formState.errors.target_platforms.message}</p>
              ) : null}
            </div>

            <Controller
              control={form.control}
              name="manual_keywords"
              render={({ field }) => (
                <TagInput
                  label="Manual keywords"
                  values={field.value ?? []}
                  onChange={field.onChange}
                  placeholder="Type keyword and press Enter"
                />
              )}
            />

            <div className="grid gap-4 md:grid-cols-2">
              <label className="space-y-1 text-sm">
                <span className="font-medium text-slate-700">Campaign tag</span>
                <input {...form.register("campaign_tag")} className="w-full rounded-lg border px-3 py-2" placeholder="Q3-product-launch" />
              </label>

              <label className="space-y-1 text-sm">
                <span className="font-medium text-slate-700">Urgency</span>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => form.setValue("urgency_level", "scheduled", { shouldValidate: true })}
                    className={`rounded-full px-3 py-1 text-xs ${
                      isScheduled ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-700"
                    }`}
                  >
                    Schedule later
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      form.setValue("urgency_level", "immediate", { shouldValidate: true });
                      form.setValue("requested_publish_at", undefined, { shouldValidate: true });
                    }}
                    className={`rounded-full px-3 py-1 text-xs ${
                      !isScheduled ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-700"
                    }`}
                  >
                    Publish now
                  </button>
                </div>
              </label>
            </div>

            {isScheduled ? (
              <label className="block space-y-1 text-sm">
                <span className="font-medium text-slate-700">Requested publish time</span>
                <input
                  type="datetime-local"
                  onChange={(e) => {
                    const value = e.target.value ? new Date(e.target.value).toISOString() : undefined;
                    form.setValue("requested_publish_at", value, { shouldValidate: true });
                  }}
                  className="w-full rounded-lg border px-3 py-2"
                />
                {form.formState.errors.requested_publish_at?.message ? (
                  <p className="text-xs text-red-600">{form.formState.errors.requested_publish_at.message}</p>
                ) : null}
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
              {upload.isUploading ? (
                <div className="space-y-1">
                  <div className="h-2 overflow-hidden rounded-full bg-slate-200">
                    <div className="h-2 bg-emerald-600 transition-all" style={{ width: `${upload.progress}%` }} />
                  </div>
                  <p className="text-xs text-slate-600">Uploading media... {upload.progress}%</p>
                </div>
              ) : null}
              {form.watch("attached_media_id") ? <p className="text-xs text-slate-600">Asset: {form.watch("attached_media_id")}</p> : null}
              {upload.error ? <p className="text-xs text-red-600">Upload failed. Please retry.</p> : null}
            </div>
          </section>
        ) : null}

        {activeStep === 2 ? (
          <section className="space-y-4 rounded-2xl border border-emerald-200 bg-emerald-50/40 p-4 sm:p-5">
            <header className="space-y-1">
              <h2 className="text-lg font-semibold text-emerald-900">AI Draft</h2>
              <p className="text-sm text-emerald-800">Generate single-platform or multi-platform draft options using your profile context.</p>
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
                Preview mode: AI actions are returning static sample responses.
              </p>
            ) : null}

            <label className="block space-y-1 text-sm">
              <span className="font-medium text-slate-700">AI platform</span>
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
                className="inline-flex items-center gap-1 rounded-lg bg-emerald-700 px-3 py-2 text-xs font-semibold text-white disabled:opacity-60"
              >
                {isGeneratingAI ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Sparkles className="h-3.5 w-3.5" />}
                {isGeneratingAI ? "Generating..." : "Create with AI"}
              </button>

              <button
                type="button"
                onClick={handleBatchGenerate}
                disabled={isBatchGenerating}
                className="inline-flex items-center gap-1 rounded-lg bg-slate-900 px-3 py-2 text-xs font-semibold text-white disabled:opacity-60"
              >
                {isBatchGenerating ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <WandSparkles className="h-3.5 w-3.5" />}
                {isBatchGenerating ? "Generating batch..." : "Generate batch"}
              </button>

              <button
                type="button"
                onClick={handleGenerateWithAI}
                disabled={isGeneratingAI || !contentDraft}
                className="rounded-lg border border-slate-300 px-3 py-2 text-xs font-semibold text-slate-700 disabled:opacity-60"
              >
                Regenerate
              </button>
            </div>

            {isGeneratingAI || isBatchGenerating ? (
              <div className="space-y-2 rounded-xl border border-slate-200 bg-white p-3">
                <SkeletonBlock className="h-4 w-40 rounded" />
                <SkeletonBlock className="h-4 w-full rounded" />
                <SkeletonBlock className="h-4 w-[92%] rounded" />
                <SkeletonBlock className="h-4 w-[85%] rounded" />
                <p className="inline-flex items-center gap-1 text-xs text-slate-500">
                  <Clock3 className="h-3.5 w-3.5" />
                  Preparing draft options...
                </p>
              </div>
            ) : null}

            {aiError ? (
              <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-700">
                <p>{aiError}</p>
                <button type="button" onClick={handleGenerateWithAI} className="mt-2 font-semibold underline">
                  Retry generation
                </button>
              </div>
            ) : null}

            {contentDraft ? (
              <div className="space-y-2 rounded-xl border border-slate-200 bg-white p-3">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Generated draft</p>
                <textarea
                  value={contentDraft}
                  onChange={(event) => setContentDraft(event.target.value)}
                  rows={7}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800"
                  aria-label="Generated draft content"
                />
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={copyResultToClipboard}
                    className="rounded-lg border border-slate-300 px-3 py-2 text-xs font-semibold text-slate-700"
                  >
                    Copy
                  </button>
                  <button
                    type="button"
                    onClick={() => form.setValue("core_message", contentDraft.slice(0, 500), { shouldValidate: true })}
                    className="rounded-lg border border-slate-300 px-3 py-2 text-xs font-semibold text-slate-700"
                  >
                    Use as core message
                  </button>
                </div>
              </div>
            ) : (
              <EmptyStateCard
                title="No draft generated yet"
                description="Generate a draft now, or continue with your own core message in the next step."
                actionLabel="Generate with AI"
                onAction={handleGenerateWithAI}
              />
            )}
          </section>
        ) : null}

        {activeStep === 3 ? (
          <section className="space-y-4 rounded-2xl border border-slate-200 bg-white p-4 sm:p-5">
            <header>
              <h2 className="text-lg font-semibold text-slate-900">Review + Refine</h2>
              <p className="text-sm text-slate-600">Improve tone, run quality checks, and enrich metadata before generation.</p>
            </header>

            {!contentDraft.trim() ? (
              <EmptyStateCard
                title="Draft required for refinement"
                description="Generate a draft in Step 2 or write your own message and continue."
                actionLabel="Go to AI Draft"
                onAction={() => setActiveStep(2)}
              />
            ) : (
              <>
                <label className="block space-y-1 text-sm">
                  <span className="font-medium text-slate-700">Improve instruction</span>
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
                    disabled={isImproving || !contentDraft}
                    className="rounded-lg border border-slate-300 px-3 py-2 text-xs font-semibold text-slate-700 disabled:opacity-60"
                  >
                    {isImproving ? "Improving..." : "Improve content"}
                  </button>

                  <button
                    type="button"
                    onClick={handleAnalyzeContent}
                    disabled={isAnalyzing || !contentDraft}
                    className="rounded-lg border border-slate-300 px-3 py-2 text-xs font-semibold text-slate-700 disabled:opacity-60"
                  >
                    {isAnalyzing ? "Analyzing..." : "Analyze content"}
                  </button>

                  <button
                    type="button"
                    onClick={handleSuggestHashtags}
                    disabled={isSuggestingHashtags || !contentDraft}
                    className="rounded-lg border border-slate-300 px-3 py-2 text-xs font-semibold text-slate-700 disabled:opacity-60"
                  >
                    {isSuggestingHashtags ? "Suggesting..." : "Suggest hashtags"}
                  </button>

                  <button
                    type="button"
                    onClick={handleSuggestTopics}
                    disabled={isSuggestingTopics}
                    className="rounded-lg border border-slate-300 px-3 py-2 text-xs font-semibold text-slate-700 disabled:opacity-60"
                  >
                    {isSuggestingTopics ? "Suggesting..." : "Suggest topics"}
                  </button>
                </div>

                {analysis ? (
                  <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs text-slate-700">
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
                  <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs text-slate-700">
                    <p className="mb-2 font-semibold text-slate-900">Suggested hashtags (click to add as keyword)</p>
                    <div className="flex flex-wrap gap-2">
                      {hashtags.map((tag) => (
                        <button
                          key={tag}
                          type="button"
                          onClick={() => addKeywordSuggestion(tag)}
                          className="rounded-full bg-white px-2 py-1 text-xs text-slate-700 ring-1 ring-slate-200 hover:ring-emerald-300"
                        >
                          #{tag}
                        </button>
                      ))}
                    </div>
                  </div>
                ) : null}

                {topics.length > 0 ? (
                  <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs text-slate-700">
                    <p className="mb-2 font-semibold text-slate-900">Suggested topics</p>
                    <ul className="space-y-1">
                      {topics.map((topic) => (
                        <li key={topic} className="flex items-start justify-between gap-3 rounded-md bg-white px-2 py-1.5">
                          <span>{topic}</span>
                          <button
                            type="button"
                            onClick={() => form.setValue("core_message", topic, { shouldValidate: true })}
                            className="text-[11px] font-semibold text-emerald-700 hover:underline"
                          >
                            Use
                          </button>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}

                {batchResults.length > 0 ? (
                  <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs text-slate-700">
                    <p className="mb-2 font-semibold text-slate-900">Batch generation results</p>
                    <ul className="space-y-1">
                      {batchResults.map((result, index) => (
                        <li key={`${result.platform}-${index}`}>
                          <span className="font-medium capitalize">{result.platform}:</span> {result.success ? "Success" : result.error ?? "Failed"}
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </>
            )}
          </section>
        ) : null}

        {activeStep === 4 ? (
          <section className="space-y-4 rounded-2xl border border-slate-200 bg-white p-4 sm:p-5">
            <header>
              <h2 className="text-lg font-semibold text-slate-900">Confirm + Generate</h2>
              <p className="text-sm text-slate-600">Review your payload before creating the final generated package.</p>
            </header>

            {!IS_STATIC && !UUID_REGEX.test(companyId) ? (
              <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                Company ID is not in expected UUID format. Complete onboarding before generating.
              </div>
            ) : null}

            <div className="grid gap-3 md:grid-cols-2">
              <article className="rounded-xl border border-slate-200 p-3">
                <p className="text-xs uppercase tracking-wide text-slate-500">Intent</p>
                <p className="mt-1 text-sm font-semibold text-slate-900">{form.watch("post_intent")}</p>
              </article>
              <article className="rounded-xl border border-slate-200 p-3">
                <p className="text-xs uppercase tracking-wide text-slate-500">Platforms</p>
                <p className="mt-1 text-sm font-semibold capitalize text-slate-900">{selectedTargets.join(", ") || "None"}</p>
              </article>
              <article className="rounded-xl border border-slate-200 p-3">
                <p className="text-xs uppercase tracking-wide text-slate-500">Core Message Length</p>
                <p className="mt-1 text-sm font-semibold text-slate-900">{coreMessageLength} characters</p>
              </article>
              <article className="rounded-xl border border-slate-200 p-3">
                <p className="text-xs uppercase tracking-wide text-slate-500">Urgency</p>
                <p className="mt-1 text-sm font-semibold text-slate-900">
                  {isScheduled ? `Scheduled for ${requestedPublishAt ? new Date(requestedPublishAt).toLocaleString() : "(missing time)"}` : "Immediate publish"}
                </p>
              </article>
            </div>

            {!canSubmit ? (
              <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">
                Final validation is incomplete. Make sure your core message is long enough, at least one platform is selected,
                and scheduled posts include a publish time.
              </div>
            ) : null}

            <button
              type="submit"
              disabled={generateMutation.isPending || !canSubmit}
              className="inline-flex items-center gap-1 rounded-lg bg-emerald-700 px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
            >
              {generateMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
              {generateMutation.isPending ? "Generating package..." : "Generate post package"}
            </button>
          </section>
        ) : null}

        <footer className="flex flex-wrap items-center justify-between gap-2 rounded-2xl border border-slate-200 bg-slate-50/60 p-3">
          <div className="flex gap-2">
            <button
              type="button"
              disabled={activeStep === 1}
              onClick={() => setActiveStep((prev) => Math.max(1, prev - 1))}
              className="rounded-lg border border-slate-300 px-3 py-2 text-xs font-semibold text-slate-700 disabled:opacity-50"
            >
              Back
            </button>

            {activeStep < 4 ? (
              <button
                type="button"
                onClick={goToNextStep}
                className="rounded-lg bg-slate-900 px-3 py-2 text-xs font-semibold text-white"
              >
                Continue
              </button>
            ) : null}
          </div>

          <button
            type="button"
            onClick={() => setShowResetConfirm(true)}
            className="inline-flex items-center gap-1 rounded-lg border border-slate-300 px-3 py-2 text-xs font-semibold text-slate-700"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            Reset draft
          </button>
        </footer>
      </form>

      <ConfirmDialog
        open={showResetConfirm}
        title="Reset current draft?"
        description="This will clear local draft data, AI output, and current wizard progress."
        confirmLabel="Reset draft"
        onConfirm={clearDraft}
        onCancel={() => setShowResetConfirm(false)}
      />
    </main>
  );
}
