"use client";

import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import Link from "next/link";
import {
  BarChart3,
  Brain,
  CalendarDays,
  CheckCircle2,
  ClipboardList,
  Compass,
  FileText,
  MessageSquareText,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  UsersRound,
  type LucideIcon
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { Textarea } from "@/components/ui/textarea";
import {
  AIWorkspaceApiError,
  analyzeCommunityMessage,
  analyzeCompetitors,
  createBrandStrategy,
  createContentCalendar,
  defaultBrandProfile,
  generateContentPackage,
  generateReportInsights,
  generateVisualConcept,
  getBrandProfile,
  getWorkspaceContext,
  recommendHashtags,
  researchTrends,
  reviewContentQuality,
  upsertBrandProfile,
  validateBrandProfile,
  type AIQualityReview,
  type BrandProfile,
  type BrandProfileValidationResult,
  type CommunityMessageAnalysis,
  type CompetitorInsightReport,
  type ContentCalendarPlan,
  type GeneratedContentPackage,
  type HashtagRecommendation,
  type ProductContext,
  type ReportingInsightReport,
  type TrendInsightReport,
  type VisualConceptPackage,
  type BrandStrategyPlan
} from "@/lib/api/ai-workspace";

type WorkspaceMode =
  | "home"
  | "brand"
  | "content"
  | "strategy"
  | "trends"
  | "competitors"
  | "analyst"
  | "calendar"
  | "community"
  | "reports";

interface AIWorkspacePanelProps {
  mode: WorkspaceMode;
}

const moduleLinks = [
  { href: "/dashboard/ai", label: "AI Workspace", icon: Sparkles, description: "Command center for ARIA modules." },
  { href: "/dashboard/brand-brain", label: "Brand Brain", icon: Brain, description: "Configure reusable brand context." },
  { href: "/dashboard/content-studio", label: "Content Studio", icon: FileText, description: "Create drafts, hashtags, and visual briefs." },
  { href: "/dashboard/strategy", label: "Strategy", icon: Compass, description: "Plan positioning, competitors, and trends." },
  { href: "/dashboard/trends", label: "Trends", icon: TrendingUp, description: "Research provided trend and keyword signals." },
  { href: "/dashboard/competitors", label: "Competitors", icon: UsersRound, description: "Analyze manually provided competitor examples." },
  { href: "/dashboard/ai-analyst", label: "AI Analyst", icon: BarChart3, description: "Turn manual metrics into insight." },
  { href: "/dashboard/calendar-ai", label: "Calendar AI", icon: CalendarDays, description: "Create draft calendar plans only." },
  { href: "/dashboard/community-ai", label: "Community AI", icon: MessageSquareText, description: "Classify messages and draft replies." },
  { href: "/dashboard/reports-ai", label: "Reports AI", icon: ClipboardList, description: "Generate report recommendations." },
  { href: "/dashboard/approval", label: "Approval Queue", icon: ShieldCheck, description: "Review draft lifecycle decisions." }
] as const;

function parseList(value: string): string[] {
  return value
    .split(/\r?\n|,/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function toLines(values: string[]): string {
  return values.join("\n");
}

function today(offsetDays = 0): string {
  const date = new Date();
  date.setDate(date.getDate() + offsetDays);
  return date.toISOString().slice(0, 10);
}

function readableError(error: unknown): string {
  if (error instanceof AIWorkspaceApiError) {
    return `${error.status}: ${error.message}`;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Request failed.";
}

function SafetyBanner() {
  return (
    <div className="rounded-lg border border-emerald-500/25 bg-emerald-500/10 p-3 text-sm text-emerald-800">
      AI suggestions require human review. Nothing is published automatically. Community replies are not sent automatically. Calendar drafts are not scheduled to real platforms.
    </div>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="space-y-1.5">
      <Label className="text-xs font-semibold uppercase tracking-wide text-[var(--text-muted)]">{label}</Label>
      {children}
    </div>
  );
}

function ListBlock({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="rounded-lg border border-[var(--border)] p-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-[var(--text-muted)]">{title}</p>
      {items.length ? (
        <ul className="mt-2 space-y-1 text-sm text-[var(--text-secondary)]">
          {items.map((item) => (
            <li key={item}>- {item}</li>
          ))}
        </ul>
      ) : (
        <p className="mt-2 text-sm text-[var(--text-muted)]">No items yet.</p>
      )}
    </div>
  );
}

function ErrorNotice({ message }: { message: string }) {
  return <div className="rounded-lg border border-red-500/25 bg-red-500/10 p-3 text-sm text-red-700">{message}</div>;
}

function BrandStatus({
  validation,
  loading,
  error
}: {
  validation: BrandProfileValidationResult | null;
  loading: boolean;
  error: string;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Brain className="h-4 w-4" />
          Brand context
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {loading ? <p className="text-sm text-[var(--text-muted)]">Loading brand context...</p> : null}
        {error ? <ErrorNotice message={error} /> : null}
        {validation ? (
          <>
            <div className="flex items-center justify-between">
              <span className="text-sm text-[var(--text-secondary)]">Completeness</span>
              <Badge variant={validation.is_complete ? "default" : "outline"}>{validation.completeness_score}%</Badge>
            </div>
            <Progress value={validation.completeness_score} />
            {validation.missing_required_fields.length ? (
              <ListBlock title="Missing fields" items={validation.missing_required_fields} />
            ) : (
              <div className="flex items-center gap-2 rounded-lg border border-emerald-500/25 bg-emerald-500/10 p-3 text-sm text-emerald-800">
                <CheckCircle2 className="h-4 w-4" />
                Brand Brain has the required workflow context.
              </div>
            )}
            {validation.using_default_context ? (
              <ErrorNotice message="AI workflows are using default/mock brand context until a real BrandProfile is saved." />
            ) : null}
          </>
        ) : null}
      </CardContent>
    </Card>
  );
}

function useBrandWorkspace() {
  const [profile, setProfile] = useState<BrandProfile>(defaultBrandProfile);
  const [validation, setValidation] = useState<BrandProfileValidationResult | null>(null);
  const [context, setContext] = useState<ProductContext | null>(null);
  const [loadingBrand, setLoadingBrand] = useState(false);
  const [brandError, setBrandError] = useState("");

  useEffect(() => {
    let active = true;
    setLoadingBrand(true);
    Promise.allSettled([getWorkspaceContext(), getBrandProfile(defaultBrandProfile.brand_id)])
      .then(async ([contextResult, profileResult]) => {
        if (!active) {
          return;
        }
        if (contextResult.status === "fulfilled") {
          setContext(contextResult.value);
        }
        if (profileResult.status === "fulfilled") {
          setProfile(profileResult.value.profile);
          setValidation(profileResult.value.validation);
          setBrandError("");
          return;
        }
        const fallbackValidation = await validateBrandProfile(defaultBrandProfile, true).catch(() => null);
        if (!active) {
          return;
        }
        setValidation(fallbackValidation);
        setBrandError(readableError(profileResult.reason));
      })
      .finally(() => {
        if (active) {
          setLoadingBrand(false);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  return { profile, setProfile, validation, setValidation, context, loadingBrand, brandError, setBrandError };
}

export function AIWorkspacePanel({ mode }: AIWorkspacePanelProps) {
  const workspace = useBrandWorkspace();

  if (mode === "brand") {
    return <BrandBrainPanel {...workspace} />;
  }
  if (mode === "content") {
    return <ContentStudioPanel {...workspace} />;
  }
  if (mode === "strategy") {
    return <StrategyPanel {...workspace} />;
  }
  if (mode === "trends") {
    return <TrendsPanel {...workspace} />;
  }
  if (mode === "competitors") {
    return <CompetitorsPanel {...workspace} />;
  }
  if (mode === "analyst" || mode === "reports") {
    return <ReportsPanel {...workspace} title={mode === "analyst" ? "AI Analyst" : "Reports AI"} />;
  }
  if (mode === "calendar") {
    return <CalendarPanel {...workspace} />;
  }
  if (mode === "community") {
    return <CommunityPanel {...workspace} />;
  }
  return <AIWorkspaceHome {...workspace} />;
}

type WorkspaceState = ReturnType<typeof useBrandWorkspace>;

function PageHeader({ title, description, icon: Icon }: { title: string; description: string; icon: LucideIcon }) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 className="flex items-center gap-2">
          <Icon className="h-6 w-6 text-[var(--brand-primary)]" />
          {title}
        </h1>
        <p className="mt-1 text-sm text-[var(--text-secondary)]">{description}</p>
      </div>
    </div>
  );
}

function AIWorkspaceHome({ validation, context, loadingBrand, brandError }: WorkspaceState) {
  return (
    <div className="space-y-6">
      <PageHeader title="AI Workspace" description="ARIA is your approval-based AI Social Media Manager and Brand Manager workspace." icon={Sparkles} />
      <SafetyBanner />
      <div className="grid gap-4 xl:grid-cols-[1fr_320px]">
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {moduleLinks.map((item) => {
            const Icon = item.icon;
            return (
              <Link key={item.href} href={item.href} className="rounded-lg border border-[var(--border)] bg-[var(--bg-surface)] p-4 transition hover:bg-[var(--bg-elevated)]">
                <Icon className="h-5 w-5 text-[var(--brand-primary)]" />
                <p className="mt-3 font-semibold">{item.label}</p>
                <p className="mt-1 text-sm text-[var(--text-secondary)]">{item.description}</p>
              </Link>
            );
          })}
        </div>
        <BrandStatus validation={validation} loading={loadingBrand} error={brandError} />
      </div>
      <Card>
        <CardHeader>
          <CardTitle>System-known context</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-2">
          <ListBlock title="Capabilities" items={context?.supported_capabilities ?? []} />
          <ListBlock title="Automation boundaries" items={context?.automation_boundaries ?? []} />
        </CardContent>
      </Card>
    </div>
  );
}

function BrandBrainPanel({ profile, setProfile, validation, setValidation, loadingBrand, brandError, setBrandError }: WorkspaceState) {
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  function update<K extends keyof BrandProfile>(key: K, value: BrandProfile[K]) {
    setProfile({ ...profile, [key]: value });
  }

  async function saveProfile() {
    setSaving(true);
    setMessage("");
    setBrandError("");
    try {
      const result = await upsertBrandProfile(profile);
      setProfile(result.profile);
      setValidation(result.validation);
      setMessage("Brand Brain saved. AI modules will reuse this profile automatically.");
    } catch (error) {
      setBrandError(readableError(error));
    } finally {
      setSaving(false);
    }
  }

  async function validateProfile() {
    setSaving(true);
    setMessage("");
    try {
      const result = await validateBrandProfile(profile, false);
      setValidation(result);
    } catch (error) {
      setBrandError(readableError(error));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Brand Brain" description="Configure brand-specific memory once. ARIA reuses it across every AI workflow." icon={Brain} />
      <SafetyBanner />
      <div className="grid gap-4 xl:grid-cols-[1fr_320px]">
        <Card>
          <CardContent className="grid gap-4 pt-6 md:grid-cols-2">
            <Field label="Brand ID"><Input value={profile.brand_id} onChange={(event) => update("brand_id", event.target.value)} /></Field>
            <Field label="Brand name"><Input value={profile.brand_name} onChange={(event) => update("brand_name", event.target.value)} /></Field>
            <Field label="Industry"><Input value={profile.industry} onChange={(event) => update("industry", event.target.value)} /></Field>
            <Field label="Description"><Textarea value={profile.description} onChange={(event) => update("description", event.target.value)} /></Field>
            <Field label="Products or services"><Textarea value={toLines(profile.products_or_services)} onChange={(event) => update("products_or_services", parseList(event.target.value))} /></Field>
            <Field label="Target audience"><Textarea value={toLines(profile.target_audience)} onChange={(event) => update("target_audience", parseList(event.target.value))} /></Field>
            <Field label="Tone of voice"><Textarea value={toLines(profile.tone_of_voice)} onChange={(event) => update("tone_of_voice", parseList(event.target.value))} /></Field>
            <Field label="Brand values"><Textarea value={toLines(profile.brand_values)} onChange={(event) => update("brand_values", parseList(event.target.value))} /></Field>
            <Field label="Approved claims"><Textarea value={toLines(profile.approved_claims)} onChange={(event) => update("approved_claims", parseList(event.target.value))} /></Field>
            <Field label="Forbidden words"><Textarea value={toLines(profile.forbidden_words)} onChange={(event) => update("forbidden_words", parseList(event.target.value))} /></Field>
            <Field label="Forbidden topics"><Textarea value={toLines(profile.forbidden_topics)} onChange={(event) => update("forbidden_topics", parseList(event.target.value))} /></Field>
            <Field label="Competitors"><Textarea value={toLines(profile.competitors)} onChange={(event) => update("competitors", parseList(event.target.value))} /></Field>
            <Field label="Platforms"><Textarea value={toLines(profile.platforms)} onChange={(event) => update("platforms", parseList(event.target.value))} /></Field>
            <Field label="Business goals"><Textarea value={toLines(profile.business_goals)} onChange={(event) => update("business_goals", parseList(event.target.value))} /></Field>
            <Field label="Language preferences"><Textarea value={toLines(profile.language_preferences)} onChange={(event) => update("language_preferences", parseList(event.target.value))} /></Field>
          </CardContent>
          <div className="flex flex-wrap gap-2 px-6 pb-6">
            <Button onClick={saveProfile} disabled={saving}>{saving ? "Saving..." : "Save Brand Brain"}</Button>
            <Button variant="outline" onClick={validateProfile} disabled={saving}>Validate completeness</Button>
          </div>
        </Card>
        <div className="space-y-4">
          <BrandStatus validation={validation} loading={loadingBrand} error={brandError} />
          {message ? <div className="rounded-lg border border-emerald-500/25 bg-emerald-500/10 p-3 text-sm text-emerald-800">{message}</div> : null}
          {validation?.warnings.length ? <ListBlock title="Warnings" items={validation.warnings} /> : null}
        </div>
      </div>
    </div>
  );
}

function ContentStudioPanel({ profile, validation, loadingBrand, brandError }: WorkspaceState) {
  const [platform, setPlatform] = useState(profile.platforms[0] ?? "linkedin");
  const [topic, setTopic] = useState("approval-based AI content");
  const [objective, setObjective] = useState("build trust");
  const [pillar, setPillar] = useState("education");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [content, setContent] = useState<GeneratedContentPackage | null>(null);
  const [hashtags, setHashtags] = useState<HashtagRecommendation | null>(null);
  const [visual, setVisual] = useState<VisualConceptPackage | null>(null);
  const [review, setReview] = useState<AIQualityReview | null>(null);

  useEffect(() => {
    setPlatform(profile.platforms[0] ?? "linkedin");
  }, [profile.platforms]);

  async function runContentStudio() {
    setLoading(true);
    setError("");
    try {
      const request = {
        brand_profile: profile,
        platform_context: { platform, content_type: "post", objective, hashtag_limit: 8 },
        campaign_objective: objective,
        topic,
        content_pillar: pillar,
        language: profile.language_preferences[0] ?? "en",
        number_of_variants: 1,
        extra_context: { workflow: "phase_8_content_studio" }
      };
      const generated = await generateContentPackage(request);
      const [tagResult, visualResult, reviewResult] = await Promise.all([
        recommendHashtags({ brand_profile: profile, platform_context: request.platform_context, topic, max_hashtags: 12 }),
        generateVisualConcept({ brand_profile: profile, platform_context: request.platform_context, topic, content_pillar: pillar, campaign_objective: objective }),
        reviewContentQuality({ request, package: generated })
      ]);
      setContent(generated);
      setHashtags(tagResult);
      setVisual(visualResult);
      setReview(reviewResult);
    } catch (caught) {
      setError(readableError(caught));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Content Studio" description="Generate draft packages, hashtags, visual concepts, and quality reviews for approval." icon={FileText} />
      <SafetyBanner />
      <div className="grid gap-4 xl:grid-cols-[1fr_320px]">
        <Card>
          <CardContent className="grid gap-4 pt-6 md:grid-cols-2">
            <Field label="Platform"><Input value={platform} onChange={(event) => setPlatform(event.target.value)} /></Field>
            <Field label="Topic"><Input value={topic} onChange={(event) => setTopic(event.target.value)} /></Field>
            <Field label="Campaign objective"><Input value={objective} onChange={(event) => setObjective(event.target.value)} /></Field>
            <Field label="Content pillar"><Input value={pillar} onChange={(event) => setPillar(event.target.value)} /></Field>
          </CardContent>
          <div className="px-6 pb-6"><Button onClick={runContentStudio} disabled={loading}>{loading ? "Generating..." : "Generate draft package"}</Button></div>
        </Card>
        <BrandStatus validation={validation} loading={loadingBrand} error={brandError} />
      </div>
      {error ? <ErrorNotice message={error} /> : null}
      <div className="grid gap-4 xl:grid-cols-2">
        {content ? (
          <Card>
            <CardHeader><CardTitle>Draft preview</CardTitle></CardHeader>
            <CardContent className="space-y-3 text-sm">
              <p className="font-semibold">{content.hook}</p>
              <p className="text-[var(--text-secondary)]">{content.caption}</p>
              <p className="text-[var(--text-secondary)]">CTA: {content.cta}</p>
              <ListBlock title="Risks" items={content.risks} />
            </CardContent>
          </Card>
        ) : null}
        {hashtags ? <ListBlock title="Hashtag recommendations" items={[...hashtags.niche_hashtags, ...hashtags.branded_hashtags, ...hashtags.trend_based_hashtags]} /> : null}
        {visual ? <ListBlock title="Visual concept" items={[visual.visual_brief, visual.scene, visual.layout]} /> : null}
        {review ? <ListBlock title="Quality review" items={[`Approval status: ${review.approval_status}`, ...review.improvement_notes]} /> : null}
      </div>
    </div>
  );
}

function StrategyPanel({ profile, validation, loadingBrand, brandError }: WorkspaceState) {
  const [goal, setGoal] = useState("increase trust in approval-based AI workflows");
  const [competitors, setCompetitors] = useState("Manual spreadsheet workflow\nGeneric AI caption tool");
  const [trends, setTrends] = useState("AI content governance\nHuman-in-the-loop marketing");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [strategy, setStrategy] = useState<BrandStrategyPlan | null>(null);
  const [competitorReport, setCompetitorReport] = useState<CompetitorInsightReport | null>(null);
  const [trendReport, setTrendReport] = useState<TrendInsightReport | null>(null);

  async function runStrategy() {
    setLoading(true);
    setError("");
    try {
      const competitorRows = parseList(competitors).map((name) => ({
        competitor_name: name,
        platform: profile.platforms[0] ?? "linkedin",
        content_type: "provided_sample",
        caption: `${name} sample provided manually by reviewer.`
      }));
      const trendRows = parseList(trends).map((keyword) => ({ keyword, source: "manual" }));
      const [strategyResult, competitorResult, trendResult] = await Promise.all([
        createBrandStrategy({ brand_profile: profile, business_goal: goal, platforms: profile.platforms }),
        analyzeCompetitors({ brand_profile: profile, competitors: competitorRows, business_goal: goal, platforms: profile.platforms }),
        researchTrends({ brand_profile: profile, trends: trendRows, business_goal: goal, platforms: profile.platforms })
      ]);
      setStrategy(strategyResult);
      setCompetitorReport(competitorResult);
      setTrendReport(trendResult);
    } catch (caught) {
      setError(readableError(caught));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Strategy" description="Use provided market inputs to shape positioning, competitor insights, and trend opportunities." icon={Compass} />
      <SafetyBanner />
      <div className="grid gap-4 xl:grid-cols-[1fr_320px]">
        <Card>
          <CardContent className="grid gap-4 pt-6">
            <Field label="Business goal"><Input value={goal} onChange={(event) => setGoal(event.target.value)} /></Field>
            <Field label="Manual competitor data"><Textarea value={competitors} onChange={(event) => setCompetitors(event.target.value)} /></Field>
            <Field label="Manual trend keywords"><Textarea value={trends} onChange={(event) => setTrends(event.target.value)} /></Field>
          </CardContent>
          <div className="px-6 pb-6"><Button onClick={runStrategy} disabled={loading}>{loading ? "Analyzing..." : "Generate strategy intelligence"}</Button></div>
        </Card>
        <BrandStatus validation={validation} loading={loadingBrand} error={brandError} />
      </div>
      {error ? <ErrorNotice message={error} /> : null}
      <div className="grid gap-4 xl:grid-cols-3">
        {strategy ? <ListBlock title="Strategic recommendations" items={[strategy.positioning_statement, ...strategy.strategic_recommendations]} /> : null}
        {competitorReport ? <ListBlock title="Competitor opportunities" items={competitorReport.strategic_opportunities.concat(competitorReport.content_gaps)} /> : null}
        {trendReport ? <ListBlock title="Trend opportunities" items={trendReport.trend_opportunities.concat(trendReport.relevant_topics)} /> : null}
      </div>
    </div>
  );
}

function TrendsPanel({ profile, validation, loadingBrand, brandError }: WorkspaceState) {
  const [goal, setGoal] = useState("find approval-safe content opportunities");
  const [keywords, setKeywords] = useState("AI content governance\nHuman-in-the-loop marketing\nbrand safety");
  const [examples, setExamples] = useState("teams want faster content review\nmarketers need safer AI drafts");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [report, setReport] = useState<TrendInsightReport | null>(null);

  async function runTrends() {
    setLoading(true);
    setError("");
    try {
      const trendRows = parseList(keywords).map((keyword) => ({
        keyword,
        source: "manual",
        platform: profile.platforms[0] ?? "linkedin",
        examples: parseList(examples)
      }));
      setReport(
        await researchTrends({
          brand_profile: profile,
          trends: trendRows,
          platforms: profile.platforms,
          business_goal: goal
        })
      );
    } catch (caught) {
      setError(readableError(caught));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Trends" description="Research manually provided trend signals. ARIA does not scrape or browse for trends in this phase." icon={TrendingUp} />
      <SafetyBanner />
      <div className="grid gap-4 xl:grid-cols-[1fr_320px]">
        <Card>
          <CardContent className="grid gap-4 pt-6">
            <Field label="Business goal"><Input value={goal} onChange={(event) => setGoal(event.target.value)} /></Field>
            <Field label="Manual trend keywords"><Textarea value={keywords} onChange={(event) => setKeywords(event.target.value)} /></Field>
            <Field label="Manual trend examples"><Textarea value={examples} onChange={(event) => setExamples(event.target.value)} /></Field>
          </CardContent>
          <div className="px-6 pb-6"><Button onClick={runTrends} disabled={loading}>{loading ? "Researching..." : "Research provided trends"}</Button></div>
        </Card>
        <BrandStatus validation={validation} loading={loadingBrand} error={brandError} />
      </div>
      {error ? <ErrorNotice message={error} /> : null}
      {report ? (
        <div className="grid gap-4 xl:grid-cols-3">
          <ListBlock title="Relevant topics" items={report.relevant_topics} />
          <ListBlock title="Trend opportunities" items={report.trend_opportunities} />
          <ListBlock title="Risk and source limits" items={report.risk_notes.concat(report.source_limitations)} />
        </div>
      ) : null}
    </div>
  );
}

function CompetitorsPanel({ profile, validation, loadingBrand, brandError }: WorkspaceState) {
  const [goal, setGoal] = useState("differentiate ARIA's approval-based workflow");
  const [samples, setSamples] = useState("Generic AI caption tool | linkedin | Announces instant captions without review controls\nManual spreadsheet workflow | linkedin | Shows a calendar process but no AI assistance");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [report, setReport] = useState<CompetitorInsightReport | null>(null);

  async function runCompetitors() {
    setLoading(true);
    setError("");
    try {
      const competitorRows = parseList(samples).map((line) => {
        const [name = "Manual competitor", platform = profile.platforms[0] ?? "linkedin", caption = line] = line
          .split("|")
          .map((part) => part.trim());
        return {
          competitor_name: name,
          platform,
          content_type: "manual_sample",
          caption,
          metadata: { input_type: "manual_phase_8_workspace" }
        };
      });
      setReport(
        await analyzeCompetitors({
          brand_profile: profile,
          competitors: competitorRows,
          business_goal: goal,
          platforms: profile.platforms
        })
      );
    } catch (caught) {
      setError(readableError(caught));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Competitors" description="Analyze competitor examples that you provide manually. No scraping or platform integrations are used." icon={UsersRound} />
      <SafetyBanner />
      <div className="grid gap-4 xl:grid-cols-[1fr_320px]">
        <Card>
          <CardContent className="grid gap-4 pt-6">
            <Field label="Business goal"><Input value={goal} onChange={(event) => setGoal(event.target.value)} /></Field>
            <Field label="Manual competitor samples"><Textarea value={samples} onChange={(event) => setSamples(event.target.value)} /></Field>
          </CardContent>
          <div className="px-6 pb-6"><Button onClick={runCompetitors} disabled={loading}>{loading ? "Analyzing..." : "Analyze provided competitors"}</Button></div>
        </Card>
        <BrandStatus validation={validation} loading={loadingBrand} error={brandError} />
      </div>
      {error ? <ErrorNotice message={error} /> : null}
      {report ? (
        <div className="grid gap-4 xl:grid-cols-3">
          <ListBlock title="Hook and theme patterns" items={report.hook_patterns.concat(report.recurring_themes)} />
          <ListBlock title="Content gaps" items={report.content_gaps} />
          <ListBlock title="Strategic opportunities" items={report.strategic_opportunities} />
        </div>
      ) : null}
    </div>
  );
}

function ReportsPanel({ profile, validation, loadingBrand, brandError, title }: WorkspaceState & { title: string }) {
  const [period, setPeriod] = useState("last_30_days");
  const [metrics, setMetrics] = useState("reach: 12000\nengagement_rate: 4.7\nbest_platform: linkedin");
  const [goals, setGoals] = useState("increase qualified engagement\nimprove approval quality");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [report, setReport] = useState<ReportingInsightReport | null>(null);

  const analyticsData = useMemo(() => {
    return Object.fromEntries(
      parseList(metrics).map((line) => {
        const [key, ...rest] = line.split(":");
        return [key.trim(), rest.join(":").trim()];
      })
    );
  }, [metrics]);

  async function runReport() {
    setLoading(true);
    setError("");
    try {
      setReport(
        await generateReportInsights({
          brand_profile: profile,
          reporting_period: period,
          platforms: profile.platforms,
          analytics_data: analyticsData,
          campaign_goals: parseList(goals)
        })
      );
    } catch (caught) {
      setError(readableError(caught));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader title={title} description="Convert manually provided analytics into recommendations and next experiments." icon={BarChart3} />
      <SafetyBanner />
      <div className="grid gap-4 xl:grid-cols-[1fr_320px]">
        <Card>
          <CardContent className="grid gap-4 pt-6">
            <Field label="Reporting period"><Input value={period} onChange={(event) => setPeriod(event.target.value)} /></Field>
            <Field label="Manual analytics metrics"><Textarea value={metrics} onChange={(event) => setMetrics(event.target.value)} /></Field>
            <Field label="Campaign goals"><Textarea value={goals} onChange={(event) => setGoals(event.target.value)} /></Field>
          </CardContent>
          <div className="px-6 pb-6"><Button onClick={runReport} disabled={loading}>{loading ? "Generating..." : "Generate report insights"}</Button></div>
        </Card>
        <BrandStatus validation={validation} loading={loadingBrand} error={brandError} />
      </div>
      {error ? <ErrorNotice message={error} /> : null}
      {report ? (
        <div className="grid gap-4 xl:grid-cols-3">
          <ListBlock title="Summary" items={[report.summary]} />
          <ListBlock title="Recommended changes" items={report.recommended_changes} />
          <ListBlock title="Next experiments" items={report.next_experiments} />
        </div>
      ) : null}
    </div>
  );
}

function CalendarPanel({ profile, validation, loadingBrand, brandError }: WorkspaceState) {
  const [startDate, setStartDate] = useState(today());
  const [endDate, setEndDate] = useState(today(14));
  const [objective, setObjective] = useState("educate buyers");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [plan, setPlan] = useState<ContentCalendarPlan | null>(null);

  async function runCalendar() {
    setLoading(true);
    setError("");
    try {
      setPlan(
        await createContentCalendar({
          brand_profile: profile,
          start_date: startDate,
          end_date: endDate,
          platforms: profile.platforms,
          content_pillars: profile.business_goals.length ? profile.business_goals : ["education"],
          campaign_objectives: [objective],
          posting_frequency_per_week: 3,
          preferred_content_types: ["post", "carousel"],
          timezone: "UTC"
        })
      );
    } catch (caught) {
      setError(readableError(caught));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Calendar AI" description="Create draft calendar plans only. Readiness never schedules to a real platform." icon={CalendarDays} />
      <SafetyBanner />
      <div className="grid gap-4 xl:grid-cols-[1fr_320px]">
        <Card>
          <CardContent className="grid gap-4 pt-6 md:grid-cols-3">
            <Field label="Start date"><Input type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} /></Field>
            <Field label="End date"><Input type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} /></Field>
            <Field label="Objective"><Input value={objective} onChange={(event) => setObjective(event.target.value)} /></Field>
          </CardContent>
          <div className="px-6 pb-6"><Button onClick={runCalendar} disabled={loading}>{loading ? "Planning..." : "Create draft calendar"}</Button></div>
        </Card>
        <BrandStatus validation={validation} loading={loadingBrand} error={brandError} />
      </div>
      {error ? <ErrorNotice message={error} /> : null}
      {plan ? (
        <Card>
          <CardHeader><CardTitle>Draft calendar items</CardTitle></CardHeader>
          <CardContent className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {plan.items.map((item) => (
              <div key={`${item.date}-${item.time}-${item.topic}`} className="rounded-lg border border-[var(--border)] p-3 text-sm">
                <p className="font-semibold">{item.date} {item.time}</p>
                <p className="mt-1 text-[var(--text-secondary)]">{item.platform} - {item.topic}</p>
                <p className="mt-2 text-xs text-[var(--text-muted)]">{item.rationale}</p>
                <Badge className="mt-3" variant="outline">Draft only</Badge>
              </div>
            ))}
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}

function CommunityPanel({ profile, validation, loadingBrand, brandError }: WorkspaceState) {
  const [platform, setPlatform] = useState(profile.platforms[0] ?? "linkedin");
  const [message, setMessage] = useState("Can your team help us review AI social content before it goes live?");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [analysis, setAnalysis] = useState<CommunityMessageAnalysis | null>(null);

  async function runCommunity() {
    setLoading(true);
    setError("");
    try {
      setAnalysis(await analyzeCommunityMessage({ brand_profile: profile, platform, message_text: message }));
    } catch (caught) {
      setError(readableError(caught));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Community AI" description="Classify messages and create human-reviewed reply drafts. Replies are never sent automatically." icon={MessageSquareText} />
      <SafetyBanner />
      <div className="grid gap-4 xl:grid-cols-[1fr_320px]">
        <Card>
          <CardContent className="grid gap-4 pt-6">
            <Field label="Platform"><Input value={platform} onChange={(event) => setPlatform(event.target.value)} /></Field>
            <Field label="Community message"><Textarea value={message} onChange={(event) => setMessage(event.target.value)} /></Field>
          </CardContent>
          <div className="px-6 pb-6"><Button onClick={runCommunity} disabled={loading}>{loading ? "Analyzing..." : "Analyze message"}</Button></div>
        </Card>
        <BrandStatus validation={validation} loading={loadingBrand} error={brandError} />
      </div>
      {error ? <ErrorNotice message={error} /> : null}
      {analysis ? (
        <Card>
          <CardHeader><CardTitle>Reply draft</CardTitle></CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2">
            <ListBlock title="Classification" items={[`Sentiment: ${analysis.sentiment}`, `Intent: ${analysis.intent}`, `Urgency: ${analysis.urgency}`, `Auto reply allowed: ${String(analysis.auto_reply_allowed)}`]} />
            <ListBlock title="Suggested reply" items={[analysis.suggested_reply]} />
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
