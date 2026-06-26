"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Archive,
  CalendarCheck,
  CheckCircle2,
  Clock3,
  FileText,
  Filter,
  History,
  Loader2,
  MessageSquareWarning,
  RefreshCw,
  Send,
  ShieldAlert,
  ShieldCheck,
  XCircle
} from "lucide-react";

import {
  ApprovalActionRequest,
  ApprovalApiError,
  ApprovalAuditEvent,
  ApprovalDetail,
  ApprovalObjectType,
  ApprovalQueueFilters,
  ApprovalQueueItem,
  ApprovalStatus,
  approveDraft,
  archiveDraft,
  escalateCommunityReply,
  getApprovalDetail,
  listApprovalQueue,
  listCalendarApprovalQueue,
  listCommunityApprovalQueue,
  listContentApprovalQueue,
  listReportApprovalQueue,
  markCalendarReadyForScheduling,
  rejectDraft,
  requestDraftChanges,
  submitForReview
} from "@/lib/api/approval";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from "@/components/ui/select";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

type ApprovalTab = "all" | ApprovalObjectType;
type DialogAction = "reject" | "request_changes" | null;

interface ApprovalDashboardProps {
  initialType?: ApprovalTab;
}

const tabs: Array<{ value: ApprovalTab; label: string; href: string }> = [
  { value: "all", label: "All", href: "/dashboard/approval" },
  { value: "content_draft", label: "Content", href: "/dashboard/approval/content" },
  { value: "calendar_draft", label: "Calendar", href: "/dashboard/approval/calendar" },
  { value: "community_reply", label: "Community", href: "/dashboard/approval/community" },
  { value: "report_draft", label: "Reports", href: "/dashboard/approval/reports" }
];

const statusOptions: Array<{ value: "all" | ApprovalStatus; label: string }> = [
  { value: "all", label: "All statuses" },
  { value: "draft", label: "Draft" },
  { value: "in_review", label: "In review" },
  { value: "approved", label: "Approved" },
  { value: "rejected", label: "Rejected" },
  { value: "changes_requested", label: "Changes requested" },
  { value: "ready_for_scheduling", label: "Ready for scheduling" },
  { value: "escalated", label: "Escalated" },
  { value: "archived", label: "Archived" }
];

const objectLabels: Record<ApprovalObjectType, string> = {
  content_draft: "Content draft",
  calendar_draft: "Calendar item",
  community_reply: "Community reply",
  report_draft: "Report draft"
};

const safetyLabels = [
  "Approval does not publish",
  "Calendar readiness does not create a platform schedule",
  "Community reply approval does not send a reply",
  "All AI outputs require human control"
] as const;

const statusLabels: Record<ApprovalStatus, string> = {
  draft: "Draft",
  in_review: "In review",
  approved: "Approved",
  rejected: "Rejected",
  changes_requested: "Changes requested",
  ready_for_scheduling: "Ready for scheduling",
  escalated: "Escalated",
  archived: "Archived"
};

function objectIcon(objectType: ApprovalObjectType) {
  if (objectType === "calendar_draft") return CalendarCheck;
  if (objectType === "community_reply") return MessageSquareWarning;
  if (objectType === "report_draft") return FileText;
  return ShieldCheck;
}

function badgeVariant(status: ApprovalStatus) {
  if (status === "approved" || status === "ready_for_scheduling") return "success";
  if (status === "rejected" || status === "escalated") return "danger";
  if (status === "changes_requested" || status === "in_review") return "warning";
  if (status === "archived") return "outline";
  return "info";
}

function formatDate(value?: string | null) {
  if (!value) return "No timestamp";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  }).format(date);
}

function itemTitle(item: ApprovalQueueItem) {
  if (item.object_type === "content_draft") return item.topic || item.caption_preview || "Untitled content draft";
  if (item.object_type === "calendar_draft") return item.topic || item.objective || "Untitled calendar item";
  if (item.object_type === "community_reply") return item.original_message_preview || "Community reply draft";
  return item.report_type || "Report draft";
}

function itemSubtitle(item: ApprovalQueueItem) {
  if (item.object_type === "content_draft") return `${item.platform} - ${item.content_type}`;
  if (item.object_type === "calendar_draft") return `${item.platform} - ${item.planned_date || "No date"} ${item.planned_time || ""}`.trim();
  if (item.object_type === "community_reply") return `${item.sentiment} - ${item.intent} - urgency ${item.urgency}`;
  return item.date_range || "No date range";
}

function itemPreview(item: ApprovalQueueItem) {
  if (item.object_type === "content_draft") return item.caption_preview || item.hook_preview;
  if (item.object_type === "calendar_draft") return item.objective || item.content_pillar;
  if (item.object_type === "community_reply") return item.suggested_reply_preview;
  return item.summary_preview;
}

function getErrorMessage(error: unknown) {
  if (error instanceof ApprovalApiError) {
    return `${error.status}: ${error.message}`;
  }
  if (error instanceof Error) return error.message;
  return "Approval request failed";
}

function makeActionPayload(item: ApprovalQueueItem, reason = "", requestedChanges: string[] = []): ApprovalActionRequest {
  return {
    object_id: item.object_id,
    object_type: item.object_type,
    reason,
    requested_changes: requestedChanges,
    metadata: {
      source: "frontend_approval_dashboard"
    }
  };
}

export function ApprovalDashboard({ initialType = "all" }: ApprovalDashboardProps) {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<ApprovalTab>(initialType);
  const [items, setItems] = useState<ApprovalQueueItem[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<ApprovalDetail | null>(null);
  const [auditEvents, setAuditEvents] = useState<ApprovalAuditEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [auditLoading, setAuditLoading] = useState(false);
  const [acting, setActing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [brandFilter, setBrandFilter] = useState("");
  const [platformFilter, setPlatformFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | ApprovalStatus>("all");
  const [dialogAction, setDialogAction] = useState<DialogAction>(null);
  const [reason, setReason] = useState("");
  const [requestedChanges, setRequestedChanges] = useState("");
  const [dialogError, setDialogError] = useState<string | null>(null);

  useEffect(() => {
    setActiveTab(initialType);
  }, [initialType]);

  const selectedItem = useMemo(
    () => items.find((item) => item.object_id === selectedId) ?? items[0] ?? null,
    [items, selectedId]
  );

  const filters = useMemo<ApprovalQueueFilters>(
    () => ({
      brand_id: brandFilter.trim() || undefined,
      platform: platformFilter.trim() || undefined,
      status: statusFilter === "all" ? undefined : statusFilter,
      object_type: activeTab === "all" ? undefined : activeTab,
      limit: 50,
      offset: 0
    }),
    [activeTab, brandFilter, platformFilter, statusFilter]
  );

  const loadQueue = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response =
        activeTab === "content_draft"
          ? await listContentApprovalQueue(filters)
          : activeTab === "calendar_draft"
            ? await listCalendarApprovalQueue(filters)
            : activeTab === "community_reply"
              ? await listCommunityApprovalQueue(filters)
              : activeTab === "report_draft"
                ? await listReportApprovalQueue(filters)
                : await listApprovalQueue(filters);

      setItems(response.items);
      setSelectedId((current) => {
        if (current && response.items.some((item) => item.object_id === current)) {
          return current;
        }
        return response.items[0]?.object_id ?? null;
      });
    } catch (queueError) {
      setItems([]);
      setSelectedId(null);
      setError(getErrorMessage(queueError));
    } finally {
      setLoading(false);
    }
  }, [activeTab, filters]);

  useEffect(() => {
    void loadQueue();
  }, [loadQueue]);

  useEffect(() => {
    if (!selectedItem) {
      setDetail(null);
      setAuditEvents([]);
      return;
    }

    setDetailLoading(true);
    setAuditLoading(true);
    getApprovalDetail(selectedItem.object_type, selectedItem.object_id)
      .then((loadedDetail) => {
        setDetail(loadedDetail);
        setAuditEvents(loadedDetail.latest_audit_events);
      })
      .catch((detailError) => {
        setDetail(null);
        setAuditEvents([]);
        setError(getErrorMessage(detailError));
      })
      .finally(() => {
        setDetailLoading(false);
        setAuditLoading(false);
      });
  }, [selectedItem]);

  const counts = useMemo(() => {
    return items.reduce<Record<ApprovalStatus, number>>(
      (accumulator, item) => {
        accumulator[item.approval_status] += 1;
        return accumulator;
      },
      {
        draft: 0,
        in_review: 0,
        approved: 0,
        rejected: 0,
        changes_requested: 0,
        ready_for_scheduling: 0,
        escalated: 0,
        archived: 0
      }
    );
  }, [items]);

  const changeTab = (value: string) => {
    const next = tabs.find((tab) => tab.value === value);
    if (!next) return;
    setActiveTab(next.value);
    router.push(next.href);
  };

  const performAction = async (
    item: ApprovalQueueItem,
    action: "submit" | "approve" | "archive" | "reject" | "request_changes" | "ready" | "escalate",
    actionReason = "",
    changes: string[] = []
  ) => {
    setActing(true);
    setError(null);
    setNotice(null);
    try {
      const payload = makeActionPayload(item, actionReason, changes);
      if (action === "submit") await submitForReview(payload);
      if (action === "approve") await approveDraft(payload);
      if (action === "archive") await archiveDraft(payload);
      if (action === "reject") await rejectDraft(payload);
      if (action === "request_changes") {
        await requestDraftChanges({
          ...payload,
          reason: actionReason,
          requested_changes: changes
        });
      }
      if (action === "ready") await markCalendarReadyForScheduling(payload);
      if (action === "escalate") await escalateCommunityReply(payload);

      setNotice("Approval status updated.");
      await loadQueue();
    } catch (actionError) {
      setError(getErrorMessage(actionError));
    } finally {
      setActing(false);
    }
  };

  const submitDialog = async () => {
    if (!selectedItem || !dialogAction) return;
    const changes = requestedChanges
      .split("\n")
      .map((change) => change.trim())
      .filter(Boolean);

    if (dialogAction === "request_changes") {
      if (!reason.trim()) {
        setDialogError("Reason is required for requested changes.");
        return;
      }
      if (changes.length === 0) {
        setDialogError("Add at least one requested change.");
        return;
      }
    }

    setDialogError(null);
    await performAction(selectedItem, dialogAction, reason, changes);
    setDialogAction(null);
    setReason("");
    setRequestedChanges("");
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-sm font-medium uppercase tracking-wide text-[var(--text-muted)]">AI approval</p>
          <h1 className="text-2xl font-semibold text-[var(--text-primary)] md:text-3xl">Approval queue</h1>
        </div>
        <div className="flex flex-wrap gap-2 text-xs text-[var(--text-secondary)]">
          {safetyLabels.map((label) => (
            <Badge key={label} variant="outline">
              {label}
            </Badge>
          ))}
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={changeTab}>
        <TabsList className="flex h-auto w-full flex-wrap justify-start gap-1 p-1 md:w-auto">
          {tabs.map((tab) => (
            <TabsTrigger key={tab.value} value={tab.value} className="min-w-20">
              {tab.label}
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <Filter className="h-4 w-4" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-[1fr_1fr_180px_auto]">
            <Input
              value={brandFilter}
              onChange={(event) => setBrandFilter(event.target.value)}
              placeholder="Brand ID"
              aria-label="Brand ID"
            />
            <Input
              value={platformFilter}
              onChange={(event) => setPlatformFilter(event.target.value)}
              placeholder="Platform"
              aria-label="Platform"
            />
            <Select value={statusFilter} onValueChange={(value) => setStatusFilter(value as "all" | ApprovalStatus)}>
              <SelectTrigger aria-label="Approval status">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {statusOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button variant="outline" onClick={() => void loadQueue()} disabled={loading}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
              Refresh
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <StatusMetric label="Drafts" value={counts.draft} icon={Clock3} />
        <StatusMetric label="In review" value={counts.in_review} icon={ShieldAlert} />
        <StatusMetric label="Approved" value={counts.approved + counts.ready_for_scheduling} icon={CheckCircle2} />
        <StatusMetric label="Needs work" value={counts.rejected + counts.changes_requested + counts.escalated} icon={XCircle} />
      </div>

      {error ? (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-700">{error}</div>
      ) : null}
      {notice ? (
        <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-700">
          {notice}
        </div>
      ) : null}

      <div className="grid gap-4 xl:grid-cols-[minmax(0,0.92fr)_minmax(420px,1.08fr)]">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Queue ({items.length})</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {loading ? (
              <div className="flex min-h-48 items-center justify-center text-sm text-[var(--text-secondary)]">
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Loading approval queue
              </div>
            ) : items.length === 0 ? (
              <div className="min-h-48 rounded-lg border border-dashed border-[var(--border)] p-6 text-sm text-[var(--text-secondary)]">
                No approval drafts match the current filters.
              </div>
            ) : (
              items.map((item) => (
                <QueueRow
                  key={`${item.object_type}:${item.object_id}`}
                  item={item}
                  active={selectedItem?.object_id === item.object_id}
                  onSelect={() => setSelectedId(item.object_id)}
                />
              ))
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Draft details</CardTitle>
          </CardHeader>
          <CardContent>
            {selectedItem ? (
              <div className="space-y-5">
                <DraftDetail item={selectedItem} detail={detail} loading={detailLoading} />
                <ActionBar
                  item={selectedItem}
                  acting={acting}
                  onSubmit={() => void performAction(selectedItem, "submit", "Submitted for human review.")}
                  onApprove={() => void performAction(selectedItem, "approve", "Approved after review.")}
                  onReject={() => {
                    setDialogError(null);
                    setDialogAction("reject");
                  }}
                  onRequestChanges={() => {
                    setDialogError(null);
                    setDialogAction("request_changes");
                  }}
                  onArchive={() => void performAction(selectedItem, "archive", "Archived from the approval queue.")}
                  onReady={() =>
                    void performAction(
                      selectedItem,
                      "ready",
                      "Marked ready for scheduling review. No platform scheduling is performed."
                    )
                  }
                  onEscalate={() =>
                    void performAction(
                      selectedItem,
                      "escalate",
                      "Escalated for manual handling. No reply is sent."
                    )
                  }
                />
                <AuditTrail events={auditEvents} loading={auditLoading} />
              </div>
            ) : (
              <div className="min-h-48 rounded-lg border border-dashed border-[var(--border)] p-6 text-sm text-[var(--text-secondary)]">
                Select a draft to review approval metadata and audit history.
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Dialog
        open={dialogAction !== null}
        onOpenChange={(open) => {
          if (!open) {
            setDialogAction(null);
            setDialogError(null);
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{dialogAction === "reject" ? "Reject draft" : "Request changes"}</DialogTitle>
            <DialogDescription>
              This records a review decision and audit event. It does not publish, schedule, or send anything.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            {dialogError ? (
              <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-700">
                {dialogError}
              </div>
            ) : null}
            <Textarea
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              placeholder="Reason"
              aria-label="Reason"
            />
            {dialogAction === "request_changes" ? (
              <Textarea
                value={requestedChanges}
                onChange={(event) => setRequestedChanges(event.target.value)}
                placeholder="Requested changes, one per line"
                aria-label="Requested changes"
              />
            ) : null}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogAction(null)} disabled={acting}>
              Cancel
            </Button>
            <Button
              variant={dialogAction === "reject" ? "destructive" : "default"}
              onClick={() => void submitDialog()}
              disabled={acting}
            >
              {acting ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
              Save decision
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function StatusMetric({
  label,
  value,
  icon: Icon
}: {
  label: string;
  value: number;
  icon: typeof ShieldCheck;
}) {
  return (
    <Card>
      <CardContent className="flex items-center justify-between p-4">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-[var(--text-muted)]">{label}</p>
          <p className="text-2xl font-semibold text-[var(--text-primary)]">{value}</p>
        </div>
        <Icon className="h-5 w-5 text-[var(--brand-primary)]" />
      </CardContent>
    </Card>
  );
}

function QueueRow({
  item,
  active,
  onSelect
}: {
  item: ApprovalQueueItem;
  active: boolean;
  onSelect: () => void;
}) {
  const Icon = objectIcon(item.object_type);
  return (
    <button
      type="button"
      onClick={onSelect}
      className={cn(
        "w-full rounded-lg border p-3 text-left transition hover:border-[var(--brand-primary)] hover:bg-[var(--bg-elevated)]",
        active ? "border-[var(--brand-primary)] bg-[var(--bg-elevated)]" : "border-[var(--border)] bg-transparent"
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 gap-3">
          <span className="mt-1 inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-[var(--bg-elevated)] text-[var(--brand-primary)]">
            <Icon className="h-4 w-4" />
          </span>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-[var(--text-primary)]">{itemTitle(item)}</p>
            <p className="truncate text-xs text-[var(--text-secondary)]">{itemSubtitle(item)}</p>
            <p className="mt-1 line-clamp-2 text-xs text-[var(--text-muted)]">{itemPreview(item)}</p>
          </div>
        </div>
        <Badge variant={badgeVariant(item.approval_status)} className="shrink-0">
          {statusLabels[item.approval_status]}
        </Badge>
      </div>
    </button>
  );
}

function DraftDetail({
  item,
  detail,
  loading
}: {
  item: ApprovalQueueItem;
  detail: ApprovalDetail | null;
  loading: boolean;
}) {
  const activeDetail = detail?.object_type === item.object_type ? detail : null;
  const Icon = objectIcon(item.object_type);
  const title = activeDetail ? detailTitle(activeDetail) : itemTitle(item);
  const objectId = activeDetail ? detailObjectId(activeDetail) : item.object_id;
  const createdAt = activeDetail?.created_at ?? item.created_at;
  const updatedAt = activeDetail?.updated_at ?? item.updated_at;
  const status = activeDetail?.approval_status ?? item.approval_status;
  const platform = detailPlatformValue(activeDetail, item);

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div className="flex gap-3">
          <span className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[var(--bg-elevated)] text-[var(--brand-primary)]">
            <Icon className="h-5 w-5" />
          </span>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-lg font-semibold text-[var(--text-primary)]">{title}</h2>
              <Badge variant={badgeVariant(status)}>{statusLabels[status]}</Badge>
            </div>
            <p className="text-sm text-[var(--text-secondary)]">{objectLabels[item.object_type]}</p>
          </div>
        </div>
        <div className="text-xs text-[var(--text-muted)]">
          <p>Created {formatDate(createdAt)}</p>
          <p>Updated {formatDate(updatedAt)}</p>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center rounded-lg border border-[var(--border)] px-4 py-3 text-sm text-[var(--text-secondary)]">
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          Loading full review detail
        </div>
      ) : null}

      <div className="grid gap-3 md:grid-cols-2">
        <DetailField label="Object ID" value={objectId} />
        <DetailField label="Brand ID" value={activeDetail?.brand_id ?? item.brand_id} />
        {platform ? <DetailField label="Platform" value={platform} /> : null}
        {item.object_type === "content_draft" ? (
          <DetailField label="Content type" value={(activeDetail?.object_type === "content_draft" ? activeDetail.content_type : item.content_type) || "Not set"} />
        ) : null}
        {item.object_type === "calendar_draft" ? (
          <DetailField
            label="Planned time"
            value={
              activeDetail?.object_type === "calendar_draft"
                ? `${activeDetail.planned_date || ""} ${activeDetail.planned_time || ""}`.trim() || "Not set"
                : `${item.planned_date || ""} ${item.planned_time || ""}`.trim() || "Not set"
            }
          />
        ) : null}
        {item.object_type === "report_draft" ? (
          <DetailField label="Report type" value={activeDetail?.object_type === "report_draft" ? activeDetail.report_type : item.report_type} />
        ) : null}
      </div>

      {activeDetail ? <SafeDetailBody detail={activeDetail} /> : <PreviewBlock value={itemPreview(item)} />}

      {activeDetail?.last_requested_changes.length ? (
        <ListBlock title="Latest requested changes" items={activeDetail.last_requested_changes} />
      ) : null}

      {activeDetail?.last_review_reason ? (
        <DetailSection title="Last review reason" value={activeDetail.last_review_reason} />
      ) : null}

      {activeDetail?.object_type === "content_draft" ? <ContentDetailSafety detail={activeDetail} /> : null}
      {!activeDetail && item.object_type === "content_draft" ? <ContentSafety item={item} /> : null}
      {activeDetail?.object_type === "community_reply" ? <CommunityDetailSafety detail={activeDetail} /> : null}
      {!activeDetail && item.object_type === "community_reply" ? <CommunitySafety item={item} /> : null}
      {item.object_type === "calendar_draft" ? (
        <SafetyPanel
          title="Scheduling safety"
          rows={[
            ["Readiness", activeDetail?.object_type === "calendar_draft" ? activeDetail.readiness_status || "Draft" : item.readiness_status || "Draft"],
            ["Safety", "Approval does not create a platform schedule."]
          ]}
        />
      ) : null}
    </div>
  );
}

function detailObjectId(detail: ApprovalDetail) {
  if (detail.object_type === "content_draft") return detail.draft_id;
  if (detail.object_type === "calendar_draft") return detail.item_id;
  if (detail.object_type === "community_reply") return detail.reply_draft_id;
  return detail.report_id;
}

function detailTitle(detail: ApprovalDetail) {
  if (detail.object_type === "content_draft") return detail.topic || detail.caption || "Untitled content draft";
  if (detail.object_type === "calendar_draft") return detail.topic || detail.objective || "Untitled calendar item";
  if (detail.object_type === "community_reply") return detail.original_message_text || "Community reply draft";
  return detail.report_type || "Report draft";
}

function detailPlatformValue(detail: ApprovalDetail | null, item: ApprovalQueueItem) {
  if (detail?.object_type === "content_draft" || detail?.object_type === "calendar_draft") {
    return detail.platform;
  }
  if ("platform" in item) {
    return item.platform;
  }
  return "";
}

function DetailField({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-[var(--border)] px-3 py-2">
      <p className="text-xs text-[var(--text-muted)]">{label}</p>
      <p className="break-words text-sm font-medium text-[var(--text-primary)]">{value || "Not set"}</p>
    </div>
  );
}

function PreviewBlock({ value }: { value: string }) {
  return <DetailSection title="Preview" value={value || "No preview available."} />;
}

function DetailSection({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded-lg border border-[var(--border)] p-4">
      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--text-muted)]">{title}</p>
      <p className="whitespace-pre-wrap text-sm text-[var(--text-primary)]">{value || "Not reported."}</p>
    </div>
  );
}

function ListBlock({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="rounded-lg border border-[var(--border)] p-4">
      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--text-muted)]">{title}</p>
      {items.length ? (
        <ul className="list-inside list-disc space-y-1 text-sm text-[var(--text-primary)]">
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-[var(--text-secondary)]">None reported.</p>
      )}
    </div>
  );
}

function RecordBlock({ title, data }: { title: string; data: Record<string, string | number | boolean | null> }) {
  const rows = Object.entries(data);
  return (
    <div className="rounded-lg border border-[var(--border)] p-4">
      <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-[var(--text-muted)]">{title}</p>
      {rows.length ? (
        <div className="grid gap-2 md:grid-cols-2">
          {rows.map(([key, value]) => (
            <div key={key} className="text-sm">
              <span className="text-[var(--text-muted)]">{key.replaceAll("_", " ")}: </span>
              <span className="font-medium text-[var(--text-primary)]">{String(value)}</span>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-[var(--text-secondary)]">None reported.</p>
      )}
    </div>
  );
}

function SafeDetailBody({ detail }: { detail: ApprovalDetail }) {
  if (detail.object_type === "content_draft") {
    return (
      <div className="space-y-3">
        <DetailSection title="Hook" value={detail.hook} />
        <DetailSection title="Caption" value={detail.caption} />
        <DetailSection title="CTA" value={detail.cta} />
        <ListBlock title="Hashtags" items={detail.hashtags} />
        <DetailSection title="Visual brief summary" value={detail.visual_brief_summary} />
        <DetailSection title="Video script summary" value={detail.video_script_summary} />
        <ListBlock title="Carousel structure summary" items={detail.carousel_structure_summary} />
        <DetailSection title="Rationale" value={detail.rationale} />
        <RecordBlock title="Posting recommendation" data={detail.posting_recommendation} />
      </div>
    );
  }

  if (detail.object_type === "calendar_draft") {
    return (
      <div className="space-y-3">
        <DetailSection title="Topic" value={detail.topic} />
        <DetailSection title="Objective" value={detail.objective} />
        <DetailSection title="Content pillar" value={detail.content_pillar} />
        <DetailSection title="Content type" value={detail.content_type} />
        <DetailSection title="Rationale" value={detail.rationale} />
      </div>
    );
  }

  if (detail.object_type === "community_reply") {
    return (
      <div className="space-y-3">
        <DetailSection title="Original message" value={detail.original_message_text} />
        <DetailSection title="Suggested reply" value={detail.suggested_reply} />
        <SafetyPanel
          title="Message classification"
          rows={[
            ["Sentiment", detail.sentiment],
            ["Intent", detail.intent],
            ["Urgency", detail.urgency],
            ["Confidence", detail.confidence.toFixed(2)]
          ]}
        />
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <DetailSection title="Summary" value={detail.summary} />
      <ListBlock title="Key insights" items={detail.key_insights} />
      <ListBlock title="Recommendations" items={detail.recommendations} />
    </div>
  );
}

function ContentSafety({ item }: { item: Extract<ApprovalQueueItem, { object_type: "content_draft" }> }) {
  const scoreRows = Object.entries(item.quality_score_summary).map(([key, value]) => [
    key.replaceAll("_", " "),
    String(value)
  ]);
  return (
    <SafetyPanel
      title="Quality and risk metadata"
      rows={[
        ["Human review", item.requires_human_review ? "Required" : "Optional"],
        ["Model", item.model || "Not reported"],
        ["Mock mode", item.mock_mode === null || item.mock_mode === undefined ? "Not reported" : item.mock_mode ? "Yes" : "No"],
        ...scoreRows,
        ...item.risk_summary.map((risk) => ["Risk", risk])
      ]}
    />
  );
}

function ContentDetailSafety({ detail }: { detail: Extract<ApprovalDetail, { object_type: "content_draft" }> }) {
  const scoreRows = Object.entries(detail.quality_score_summary).map(([key, value]) => [
    key.replaceAll("_", " "),
    String(value)
  ]);
  return (
    <SafetyPanel
      title="Quality and risk metadata"
      rows={[
        ["Human review", detail.requires_human_review ? "Required" : "Optional"],
        ["Prompt version", detail.prompt_version || "Not reported"],
        ["Model", detail.model || "Not reported"],
        ["Mock mode", detail.mock_mode === null || detail.mock_mode === undefined ? "Not reported" : detail.mock_mode ? "Yes" : "No"],
        ...scoreRows,
        ...detail.risk_summary.map((risk) => ["Risk", risk])
      ]}
    />
  );
}

function CommunitySafety({ item }: { item: Extract<ApprovalQueueItem, { object_type: "community_reply" }> }) {
  return (
    <SafetyPanel
      title="Community safety"
      rows={[
        ["Human review", item.requires_human_review ? "Required" : "Optional"],
        ["Auto reply allowed", item.auto_reply_allowed ? "Unexpected true" : "False"],
        ["Toxicity risk", item.toxicity_risk.toFixed(2)],
        ["Crisis risk", item.crisis_risk.toFixed(2)],
        ["Escalation", item.escalation_reason || "Not escalated"]
      ]}
    />
  );
}

function CommunityDetailSafety({ detail }: { detail: Extract<ApprovalDetail, { object_type: "community_reply" }> }) {
  return (
    <SafetyPanel
      title="Community safety"
      rows={[
        ["Human review", detail.requires_human_review ? "Required" : "Optional"],
        ["Auto reply allowed", detail.auto_reply_allowed ? "Unexpected true" : "False"],
        ["Toxicity risk", detail.toxicity_risk.toFixed(2)],
        ["Crisis risk", detail.crisis_risk.toFixed(2)],
        ["Escalation", detail.escalation_reason || "Not escalated"]
      ]}
    />
  );
}

function SafetyPanel({ title, rows }: { title: string; rows: string[][] }) {
  return (
    <div className="rounded-lg border border-[var(--border)] p-4">
      <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-[var(--text-muted)]">{title}</p>
      <div className="grid gap-2 md:grid-cols-2">
        {rows.length === 0 ? (
          <p className="text-sm text-[var(--text-secondary)]">No metadata reported.</p>
        ) : (
          rows.map(([label, value], index) => (
            <div key={`${label}-${index}`} className="text-sm">
              <span className="text-[var(--text-muted)]">{label}: </span>
              <span className="font-medium text-[var(--text-primary)]">{value}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function ActionBar({
  item,
  acting,
  onSubmit,
  onApprove,
  onReject,
  onRequestChanges,
  onArchive,
  onReady,
  onEscalate
}: {
  item: ApprovalQueueItem;
  acting: boolean;
  onSubmit: () => void;
  onApprove: () => void;
  onReject: () => void;
  onRequestChanges: () => void;
  onArchive: () => void;
  onReady: () => void;
  onEscalate: () => void;
}) {
  const status = item.approval_status;
  const archiveAllowed = ["approved", "rejected", "ready_for_scheduling", "escalated"].includes(status);

  return (
    <div className="flex flex-wrap gap-2 rounded-lg border border-[var(--border)] p-3">
      <Button size="sm" variant="outline" onClick={onSubmit} disabled={acting || status !== "draft"}>
        <Send className="h-4 w-4" />
        Submit
      </Button>
      <Button size="sm" onClick={onApprove} disabled={acting || !["draft", "in_review"].includes(status)}>
        <CheckCircle2 className="h-4 w-4" />
        Approve
      </Button>
      <Button size="sm" variant="outline" onClick={onRequestChanges} disabled={acting || !["draft", "in_review"].includes(status)}>
        <ShieldAlert className="h-4 w-4" />
        Changes
      </Button>
      <Button size="sm" variant="destructive" onClick={onReject} disabled={acting || !["draft", "in_review"].includes(status)}>
        <XCircle className="h-4 w-4" />
        Reject
      </Button>
      {item.object_type === "calendar_draft" ? (
        <Button size="sm" variant="secondary" onClick={onReady} disabled={acting || status !== "approved"}>
          <CalendarCheck className="h-4 w-4" />
          Ready
        </Button>
      ) : null}
      {item.object_type === "community_reply" ? (
        <Button size="sm" variant="secondary" onClick={onEscalate} disabled={acting || status !== "in_review"}>
          <MessageSquareWarning className="h-4 w-4" />
          Escalate
        </Button>
      ) : null}
      <Button size="sm" variant="ghost" onClick={onArchive} disabled={acting || !archiveAllowed}>
        <Archive className="h-4 w-4" />
        Archive
      </Button>
    </div>
  );
}

function AuditTrail({ events, loading }: { events: ApprovalAuditEvent[]; loading: boolean }) {
  return (
    <div className="rounded-lg border border-[var(--border)] p-4">
      <div className="mb-3 flex items-center justify-between">
        <p className="flex items-center gap-2 text-sm font-semibold text-[var(--text-primary)]">
          <History className="h-4 w-4" />
          Audit history
        </p>
        {loading ? <Loader2 className="h-4 w-4 animate-spin text-[var(--text-muted)]" /> : null}
      </div>
      {events.length === 0 ? (
        <p className="text-sm text-[var(--text-secondary)]">No audit events recorded for this object.</p>
      ) : (
        <div className="space-y-3">
          {events.map((event, index) => (
            <div key={event.event_id ?? `${event.object_id}-${event.timestamp}-${index}`} className="border-l border-[var(--border)] pl-3">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant={badgeVariant(event.new_status)}>{statusLabels[event.new_status]}</Badge>
                <span className="text-xs text-[var(--text-muted)]">{formatDate(event.timestamp)}</span>
              </div>
              {(event.reviewer_id || event.reviewer_role) ? (
                <p className="mt-1 text-xs text-[var(--text-muted)]">
                  {[event.reviewer_id, event.reviewer_role].filter(Boolean).join(" / ")}
                </p>
              ) : null}
              <p className="mt-1 text-sm text-[var(--text-primary)]">{event.reason || event.action.replaceAll("_", " ")}</p>
              {event.requested_changes.length ? (
                <ul className="mt-1 list-inside list-disc text-xs text-[var(--text-secondary)]">
                  {event.requested_changes.map((change) => (
                    <li key={change}>{change}</li>
                  ))}
                </ul>
              ) : null}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
