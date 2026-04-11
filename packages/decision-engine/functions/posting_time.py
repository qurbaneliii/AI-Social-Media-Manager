# FILE: packages/decision-engine/functions/posting_time.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from packages.decision_engine.constants import (
    POSTING_COOLDOWN_HOURS,
    POSTING_DEADLINE_SAFETY_BUFFER_MINUTES,
    POSTING_GLOBAL_SCORE_BASE_MULTIPLIER,
    POSTING_GLOBAL_SCORE_SCALE,
    POSTING_MIN_CONFIDENCE,
    POSTING_OVERRIDE_WINDOW_DURATION_MINUTES,
    POSTING_QUEUE_UTILIZATION_MAX,
    POSTING_REGION_HOURLY_ENGAGEMENT_PRIORS,
    POSTING_REGION_UTC_OFFSETS,
)
from packages.decision_engine.models import PostingTimeResult, ScheduleContext, TimeWindow


def _to_utc(dt: datetime, timezone_name: str | None = None) -> datetime:
    if dt.tzinfo is None:
        if timezone_name:
            localized = dt.replace(tzinfo=ZoneInfo(timezone_name))
            return localized.astimezone(timezone.utc)
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _window_to_utc(window: TimeWindow) -> TimeWindow:
    return window.model_copy(
        update={
            "start_utc": _to_utc(window.start_utc),
            "end_utc": _to_utc(window.end_utc),
        }
    )


def _is_cooldown_valid(
    requested_utc: datetime,
    last_posted_utc: datetime | None,
    cooldown_hours: int,
) -> bool:
    if last_posted_utc is None:
        return True
    gap = requested_utc - _to_utc(last_posted_utc)
    min_gap = timedelta(hours=cooldown_hours)
    return gap >= min_gap


def _is_deadline_valid(requested_utc: datetime, campaign_deadline_utc: datetime | None) -> bool:
    if campaign_deadline_utc is None:
        return True
    safety_deadline = _to_utc(campaign_deadline_utc) - timedelta(
        minutes=POSTING_DEADLINE_SAFETY_BUFFER_MINUTES
    )
    return requested_utc <= safety_deadline


def _region_hour_prior(region: str, hour: int) -> float:
    priors = POSTING_REGION_HOURLY_ENGAGEMENT_PRIORS.get(region)
    if not priors:
        return 0.0
    if hour in priors:
        return priors[hour]

    nearest_hour = min(
        priors,
        key=lambda anchor: min(abs(hour - anchor), 24 - abs(hour - anchor)),
    )
    return priors[nearest_hour]


def _adjust_confidence_by_regions(window: TimeWindow, audience_region_weights: dict[str, float]) -> TimeWindow:
    weighted_sum = 0.0
    weight_total = 0.0

    for region, weight in audience_region_weights.items():
        offset = POSTING_REGION_UTC_OFFSETS.get(region)
        if offset is None or weight <= 0.0:
            continue
        local_hour = (window.start_utc.hour + offset) % 24
        prior = _region_hour_prior(region, local_hour)
        weighted_sum += prior * weight
        weight_total += weight

    if weight_total == 0.0:
        global_score = 0.0
    else:
        global_score = weighted_sum / weight_total

    multiplier = POSTING_GLOBAL_SCORE_BASE_MULTIPLIER + (POSTING_GLOBAL_SCORE_SCALE * global_score)
    adjusted_confidence = max(0.0, min(1.0, window.confidence * multiplier))
    return window.model_copy(update={"confidence": adjusted_confidence})


def _best_window(windows: list[TimeWindow]) -> TimeWindow:
    return max(windows, key=lambda item: (item.confidence, -item.rank))


def select_posting_time(context: ScheduleContext) -> PostingTimeResult:
    """
    Implements Section 5.3 Posting Time Selection Logic.

    Decision made:
    Chooses the final publish time window based on manual override validity,
    deadlines, queue utilization, cooldown constraints, and audience-region weighting.

    Spec section:
    Section 5.3.

    Rule priority order:
    1. Validate and prefer manual override when safe.
    2. Apply deadline filter with safety buffer.
    3. Apply queue capacity filter only when alternatives remain.
    4. Apply platform cooldown filter.
    5. Adjust confidence using audience-region local-time priors.
    6. Select best confidence window above threshold, else fallback.
    7. If all filters remove windows, fall back to original best window.

    Edge cases handled:
    - Naive datetimes are safely interpreted and converted to UTC.
    - Invalid overrides return deterministic rejection reasons.
    - Queue filter is skipped when it would remove all options.
    - Unknown audience regions are ignored in global score adjustment.
    - Empty post-filter windows return the original best-ranked confidence option.
    """
    current_utc = _to_utc(context.current_utc)
    cooldown_hours = POSTING_COOLDOWN_HOURS[str(context.platform)]

    original_windows = [_window_to_utc(window) for window in context.ranked_windows]
    windows = list(original_windows)

    was_override_used = False
    was_fallback_used = False
    cooldown_enforced = False
    override_rejection_reason: str | None = None

    # 1. MANUAL OVERRIDE CHECK
    if context.manual_override is not None:
        requested_utc = _to_utc(
            context.manual_override.requested_utc,
            context.manual_override.timezone,
        )

        valid_future = requested_utc > current_utc
        valid_cooldown = _is_cooldown_valid(requested_utc, context.last_posted_utc, cooldown_hours)
        valid_deadline = _is_deadline_valid(requested_utc, context.campaign_deadline_utc)

        if valid_future and valid_cooldown and valid_deadline:
            override_window = TimeWindow(
                start_utc=requested_utc,
                end_utc=requested_utc + timedelta(minutes=POSTING_OVERRIDE_WINDOW_DURATION_MINUTES),
                rank=1,
                confidence=1.0,
                queue_utilization=0.0,
                reason_codes=["MANUAL_OVERRIDE_VALID"],
            )
            return PostingTimeResult(
                selected_window=override_window,
                was_override_used=True,
                was_fallback_used=False,
                override_rejection_reason=None,
                cooldown_enforced=False,
            )

        if not valid_future:
            override_rejection_reason = "Manual override must be in the future"
        elif not valid_cooldown:
            override_rejection_reason = "Manual override violates cooldown window"
        else:
            override_rejection_reason = "Manual override violates campaign deadline safety buffer"

        nearest_valid_window = next(
            (
                window
                for window in original_windows
                if window.start_utc > current_utc
                and _is_cooldown_valid(window.start_utc, context.last_posted_utc, cooldown_hours)
                and _is_deadline_valid(window.start_utc, context.campaign_deadline_utc)
            ),
            None,
        )
        if nearest_valid_window is not None:
            windows = [nearest_valid_window, *windows]

    # 2. DEADLINE FILTER
    if context.campaign_deadline_utc is not None:
        safety_deadline = _to_utc(context.campaign_deadline_utc) - timedelta(
            minutes=POSTING_DEADLINE_SAFETY_BUFFER_MINUTES
        )
        windows = [window for window in windows if window.start_utc <= safety_deadline]

    # 3. QUEUE CAPACITY FILTER
    queue_filtered = [
        window for window in windows if window.queue_utilization <= POSTING_QUEUE_UTILIZATION_MAX
    ]
    if queue_filtered:
        windows = queue_filtered
    else:
        windows = [
            window.model_copy(
                update={"reason_codes": [*window.reason_codes, "QUEUE_FILTER_SKIPPED_NO_ALTERNATIVE"]}
            )
            for window in windows
        ]

    # 4. COOLDOWN FILTER
    if context.last_posted_utc is not None:
        before_count = len(windows)
        last_posted_utc = _to_utc(context.last_posted_utc)
        min_gap = timedelta(hours=cooldown_hours)
        windows = [
            window
            for window in windows
            if (window.start_utc - last_posted_utc) >= min_gap
        ]
        cooldown_enforced = len(windows) < before_count

    # 5. GLOBAL SCORE ADJUSTMENT
    if context.audience_region_weights:
        windows = [
            _adjust_confidence_by_regions(window, context.audience_region_weights)
            for window in windows
        ]

    # 7. EDGE CASE
    if not windows:
        return PostingTimeResult(
            selected_window=_best_window(original_windows),
            was_override_used=False,
            was_fallback_used=True,
            override_rejection_reason=override_rejection_reason,
            cooldown_enforced=cooldown_enforced,
        )

    # 6. SELECT BEST WINDOW
    qualified = [window for window in windows if window.confidence >= POSTING_MIN_CONFIDENCE]
    if qualified:
        selected = _best_window(qualified)
        was_fallback_used = False
    else:
        selected = _best_window(windows)
        was_fallback_used = True

    return PostingTimeResult(
        selected_window=selected,
        was_override_used=was_override_used,
        was_fallback_used=was_fallback_used,
        override_rejection_reason=override_rejection_reason,
        cooldown_enforced=cooldown_enforced,
    )
