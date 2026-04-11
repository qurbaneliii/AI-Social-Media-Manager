from decision_logic.functions import (
    AudienceConfig,
    AudienceProfile,
    BrandProfile,
    HashtagCandidate,
    PlatformConstraints,
    PostRequest,
    ScheduleContext,
    TimeWindow,
    ToneFingerprint,
    adapt_tone,
    resolve_audience,
    route_platforms,
    select_hashtags,
    select_posting_time,
)


def test_select_hashtags_dedup_and_limit():
    out = select_hashtags(
        [
            HashtagCandidate("#a", 0.9, 0.1),
            HashtagCandidate("#a", 0.8, 0.2),
            HashtagCandidate("#b", 0.7, 0.5),
        ],
        platform="instagram",
        constraints=PlatformConstraints(max_hashtags=2, allow_duplicates=False),
    )
    assert out.selected == ["#a", "#b"]


def test_resolve_audience_locked():
    resolved = resolve_audience(AudienceConfig(["B2B"], True), AudienceProfile(["B2C"], 0.9))
    assert resolved.segments == ["B2B"]


def test_resolve_audience_low_confidence_fallback():
    resolved = resolve_audience(AudienceConfig(["D2C"], False), AudienceProfile(["B2C"], 0.2))
    assert resolved.segments == ["D2C"]
    assert resolved.confidence == 0.55


def test_resolve_audience_use_llm():
    inferred = AudienceProfile(["B2C"], 0.8)
    resolved = resolve_audience(AudienceConfig(["D2C"], False), inferred)
    assert resolved == inferred


def test_select_posting_time_force_window():
    windows = [TimeWindow("2026-01-01T10:00:00Z", 0.1), TimeWindow("2026-01-01T11:00:00Z", 0.9)]
    selected = select_posting_time(windows, ScheduleContext(force_window=True, minimum_confidence=0.8))
    assert selected == windows[0]


def test_select_posting_time_threshold():
    windows = [TimeWindow("2026-01-01T10:00:00Z", 0.6), TimeWindow("2026-01-01T11:00:00Z", 0.85)]
    selected = select_posting_time(windows, ScheduleContext(force_window=False, minimum_confidence=0.8))
    assert selected == windows[1]


def test_select_posting_time_fallback_best():
    windows = [TimeWindow("2026-01-01T10:00:00Z", 0.2), TimeWindow("2026-01-01T11:00:00Z", 0.4)]
    selected = select_posting_time(windows, ScheduleContext(force_window=False, minimum_confidence=0.8))
    assert selected == windows[1]


def test_select_posting_time_empty_raises():
    try:
        select_posting_time([], ScheduleContext(force_window=False, minimum_confidence=0.8))
    except ValueError as exc:
        assert "cannot be empty" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_adapt_tone_bounds():
    out = adapt_tone(ToneFingerprint(0.95, 0.95, 0.95), "inspire")
    assert out.warmth <= 1.0
    assert out.authority <= 1.0
    assert out.playfulness <= 1.0


def test_route_platforms_immediate_cap():
    req = PostRequest(["instagram", "linkedin", "facebook", "x"], "immediate")
    profiles = {k: BrandProfile(True) for k in ["instagram", "linkedin", "facebook", "x"]}
    plan = route_platforms(req, profiles)
    assert len(plan.selected_platforms) == 3


def test_route_platforms_none_raises():
    req = PostRequest(["instagram"], "scheduled")
    profiles = {"instagram": BrandProfile(False)}
    try:
        route_platforms(req, profiles)
    except ValueError as exc:
        assert "No eligible" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
