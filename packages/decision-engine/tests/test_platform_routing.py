# FILE: packages/decision-engine/tests/test_platform_routing.py
from __future__ import annotations

from packages.decision_engine.functions.platform_routing import route_platforms
from packages.decision_engine.models import (
    MediaAsset,
    Platform,
    PlatformCaptionState,
    PlatformRoutingInput,
)


def _hashtag_set() -> dict:
    return {
        "broad": [
            {"tag": "broad1", "score": 0.90},
            {"tag": "broad2", "score": 0.85},
            {"tag": "broad3", "score": 0.80},
        ],
        "niche": [
            {"tag": "niche1", "score": 0.95},
            {"tag": "niche2", "score": 0.92},
            {"tag": "niche3", "score": 0.88},
            {"tag": "niche4", "score": 0.84},
            {"tag": "niche5", "score": 0.82},
        ],
        "micro": [
            {"tag": "micro1", "score": 0.89},
            {"tag": "micro2", "score": 0.87},
            {"tag": "micro3", "score": 0.86},
            {"tag": "micro4", "score": 0.83},
            {"tag": "micro5", "score": 0.81},
        ],
    }


def _input(
    *,
    target_platforms: list[Platform],
    style_distance: float,
    media_asset: MediaAsset | None = None,
    caption_states: list[PlatformCaptionState] | None = None,
) -> PlatformRoutingInput:
    return PlatformRoutingInput(
        target_platforms=target_platforms,
        style_distance=style_distance,
        media_asset=media_asset,
        caption_states=caption_states or [],
        hashtag_set=_hashtag_set(),
    )


def _decision(plan, platform: Platform):
    return next(item for item in plan.decisions if item.platform == platform)


def test_high_style_distance_sets_per_platform_strategy():
    plan = route_platforms(_input(target_platforms=[Platform.instagram], style_distance=0.30))
    assert plan.global_strategy == "per_platform"


def test_low_style_distance_sets_shared_base_strategy():
    plan = route_platforms(_input(target_platforms=[Platform.instagram], style_distance=0.15))
    assert plan.global_strategy == "shared_base"


def test_x_hashtag_max_3_enforced():
    plan = route_platforms(_input(target_platforms=[Platform.x], style_distance=0.15))
    decision = _decision(plan, Platform.x)
    assert len(decision.hashtag_selection) <= 3


def test_x_hashtag_prefers_niche_and_micro():
    plan = route_platforms(_input(target_platforms=[Platform.x], style_distance=0.15))
    decision = _decision(plan, Platform.x)

    assert all(tag in {"#niche1", "#niche2", "#niche3", "#niche4", "#niche5", "#micro1", "#micro2", "#micro3", "#micro4", "#micro5"} for tag in decision.hashtag_selection)


def test_instagram_uses_all_tiers_up_to_13():
    plan = route_platforms(_input(target_platforms=[Platform.instagram], style_distance=0.15))
    decision = _decision(plan, Platform.instagram)
    assert len(decision.hashtag_selection) <= 13


def test_media_transform_required_for_large_mismatch():
    media = MediaAsset(media_id="m1", width_px=1600, height_px=900, mime_type="image/jpeg")
    plan = route_platforms(_input(target_platforms=[Platform.instagram], style_distance=0.15, media_asset=media))
    decision = _decision(plan, Platform.instagram)

    assert decision.requires_media_transform is True


def test_media_transform_not_required_for_small_mismatch():
    media = MediaAsset(media_id="m2", width_px=1000, height_px=1000, mime_type="image/jpeg")
    plan = route_platforms(_input(target_platforms=[Platform.instagram], style_distance=0.15, media_asset=media))
    decision = _decision(plan, Platform.instagram)

    assert decision.requires_media_transform is False


def test_caption_use_as_is_when_no_overflow():
    states = [
        PlatformCaptionState(
            platform=Platform.linkedin,
            current_char_count=100,
            char_limit=300,
            overflow_ratio=0.0,
        )
    ]
    plan = route_platforms(_input(target_platforms=[Platform.linkedin], style_distance=0.15, caption_states=states))
    decision = _decision(plan, Platform.linkedin)

    assert decision.caption_action == "use_as_is"


def test_caption_semantic_truncate_within_soft_max():
    states = [
        PlatformCaptionState(
            platform=Platform.linkedin,
            current_char_count=345,
            char_limit=300,
            overflow_ratio=0.15,
        )
    ]
    plan = route_platforms(_input(target_platforms=[Platform.linkedin], style_distance=0.15, caption_states=states))
    decision = _decision(plan, Platform.linkedin)

    assert decision.caption_action == "semantic_truncate"


def test_caption_regenerate_above_soft_max():
    states = [
        PlatformCaptionState(
            platform=Platform.linkedin,
            current_char_count=405,
            char_limit=300,
            overflow_ratio=0.35,
        )
    ]
    plan = route_platforms(_input(target_platforms=[Platform.linkedin], style_distance=0.15, caption_states=states))
    decision = _decision(plan, Platform.linkedin)

    assert decision.caption_action == "regenerate"


def test_no_media_skips_transform_check():
    plan = route_platforms(_input(target_platforms=[Platform.instagram, Platform.x], style_distance=0.10, media_asset=None))
    assert all(decision.requires_media_transform is False for decision in plan.decisions)
