# FILE: packages/decision-engine/tests/test_posting_time.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from packages.decision_engine.functions.posting_time import select_posting_time
from packages.decision_engine.models import (
    ManualOverride,
    Platform,
    ScheduleContext,
    TimeWindow,
)


@pytest.fixture
def now() -> datetime:
    return datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def make_window(now):
    def _make(
        *,
        start_in_hours: float,
        confidence: float,
        rank: int,
        queue_utilization: float = 0.4,
    ) -> TimeWindow:
        start = now + timedelta(hours=start_in_hours)
        end = start + timedelta(minutes=30)
        return TimeWindow(
            start_utc=start,
            end_utc=end,
            rank=rank,
            confidence=confidence,
            queue_utilization=queue_utilization,
            reason_codes=[],
        )

    return _make


def _context(
    *,
    now: datetime,
    windows: list[TimeWindow],
    platform: Platform = Platform.linkedin,
    last_posted_utc: datetime | None = None,
    campaign_deadline_utc: datetime | None = None,
    manual_override: ManualOverride | None = None,
    audience_region_weights: dict[str, float] | None = None,
) -> ScheduleContext:
    return ScheduleContext(
        platform=platform,
        ranked_windows=windows,
        last_posted_utc=last_posted_utc,
        campaign_deadline_utc=campaign_deadline_utc,
        manual_override=manual_override,
        audience_region_weights=audience_region_weights or {},
        current_utc=now,
    )


def test_valid_manual_override_returned_immediately(now, make_window):
    windows = [make_window(start_in_hours=2, confidence=0.7, rank=1)]
    override = ManualOverride(requested_utc=now + timedelta(hours=3), timezone="UTC")

    result = select_posting_time(
        _context(
            now=now,
            windows=windows,
            platform=Platform.linkedin,
            last_posted_utc=now - timedelta(hours=24),
            campaign_deadline_utc=now + timedelta(days=1),
            manual_override=override,
        )
    )

    assert result.was_override_used is True
    assert result.was_fallback_used is False


def test_invalid_manual_override_past_time_rejected(now, make_window):
    windows = [make_window(start_in_hours=2, confidence=0.7, rank=1)]
    override = ManualOverride(requested_utc=now - timedelta(minutes=1), timezone="UTC")

    result = select_posting_time(_context(now=now, windows=windows, manual_override=override))

    assert result.was_override_used is False
    assert result.override_rejection_reason is not None


def test_invalid_manual_override_violates_cooldown(now, make_window):
    windows = [make_window(start_in_hours=14, confidence=0.7, rank=1)]
    override = ManualOverride(requested_utc=now + timedelta(hours=3), timezone="UTC")

    result = select_posting_time(
        _context(
            now=now,
            windows=windows,
            platform=Platform.linkedin,
            last_posted_utc=now - timedelta(hours=2),
            manual_override=override,
        )
    )

    assert result.was_override_used is False
    assert result.override_rejection_reason is not None


def test_deadline_filter_removes_late_windows(now, make_window):
    windows = [
        make_window(start_in_hours=1, confidence=0.8, rank=1),
        make_window(start_in_hours=3, confidence=0.9, rank=2),
    ]

    result = select_posting_time(
        _context(
            now=now,
            windows=windows,
            campaign_deadline_utc=now + timedelta(hours=2),
        )
    )

    assert result.selected_window.start_utc < now + timedelta(hours=2)


def test_deadline_safety_buffer_applied(now, make_window):
    windows = [make_window(start_in_hours=10 / 60, confidence=0.7, rank=1)]

    result = select_posting_time(
        _context(
            now=now,
            windows=windows,
            campaign_deadline_utc=now + timedelta(minutes=35),
        )
    )

    assert result.was_fallback_used is True


def test_queue_filter_not_applied_if_only_one_window(now, make_window):
    windows = [make_window(start_in_hours=2, confidence=0.7, rank=1, queue_utilization=0.95)]

    result = select_posting_time(_context(now=now, windows=windows))

    assert result.selected_window.queue_utilization == pytest.approx(0.95)


def test_cooldown_filter_removes_too_early_windows(now, make_window):
    windows = [
        make_window(start_in_hours=4, confidence=0.9, rank=1),
        make_window(start_in_hours=7, confidence=0.8, rank=2),
    ]

    result = select_posting_time(
        _context(
            now=now,
            windows=windows,
            platform=Platform.instagram,
            last_posted_utc=now,
        )
    )

    assert result.cooldown_enforced is True
    assert result.selected_window.start_utc >= now + timedelta(hours=6)


def test_fallback_used_when_no_high_confidence_windows(now, make_window):
    windows = [
        make_window(start_in_hours=2, confidence=0.40, rank=1),
        make_window(start_in_hours=3, confidence=0.45, rank=2),
    ]

    result = select_posting_time(_context(now=now, windows=windows))

    assert result.was_fallback_used is True
    assert result.selected_window is not None


def test_no_windows_after_all_filters_returns_original_best(now, make_window):
    windows = [
        make_window(start_in_hours=3, confidence=0.90, rank=1, queue_utilization=0.9),
        make_window(start_in_hours=4, confidence=0.80, rank=2, queue_utilization=0.95),
    ]

    result = select_posting_time(
        _context(
            now=now,
            windows=windows,
            platform=Platform.linkedin,
            last_posted_utc=now,
            campaign_deadline_utc=now + timedelta(minutes=31),
        )
    )

    assert result.was_fallback_used is True
    assert result.selected_window.confidence == pytest.approx(0.90)


def test_global_score_adjustment_applied(now, make_window):
    window = make_window(start_in_hours=2, confidence=0.80, rank=1)

    result = select_posting_time(
        _context(
            now=now,
            windows=[window],
            audience_region_weights={"US_EST": 1.0},
        )
    )

    assert result.selected_window.confidence != pytest.approx(0.80)
