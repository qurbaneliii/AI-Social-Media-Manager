# FILE: packages/decision-engine/functions/platform_routing.py
from __future__ import annotations

from packages.decision_engine.constants import (
    PLATFORM_HASHTAG_STRATEGY,
    PLATFORM_PREFERRED_ASPECT_RATIOS,
    ROUTING_ASPECT_MISMATCH_THRESHOLD,
    ROUTING_OVERFLOW_SOFT_MAX,
    ROUTING_STYLE_DISTANCE_THRESHOLD,
)
from packages.decision_engine.models import (
    Platform,
    PlatformRoutingDecision,
    PlatformRoutingInput,
    PlatformRoutingPlan,
)


def _extract_tier_entries(hashtag_set: dict, tier: str) -> list[dict]:
    entries = hashtag_set.get(tier, [])
    normalized: list[dict] = []
    for entry in entries:
        if hasattr(entry, "model_dump"):
            normalized.append(entry.model_dump(mode="python"))
        elif isinstance(entry, dict):
            normalized.append(entry)
    return normalized


def _collect_hashtags_for_platform(platform: Platform, hashtag_set: dict) -> list[str]:
    strategy = PLATFORM_HASHTAG_STRATEGY[str(platform)]
    max_tags = int(strategy["max"])
    preferred_tiers = list(strategy["preferred_tiers"])

    selected: list[str] = []
    seen: set[str] = set()

    for tier in preferred_tiers:
        for entry in _extract_tier_entries(hashtag_set, tier):
            tag_value = str(entry.get("tag", "")).strip().lstrip("#")
            if not tag_value or tag_value in seen:
                continue
            selected.append(f"#{tag_value}")
            seen.add(tag_value)
            if len(selected) >= max_tags:
                return selected[:max_tags]

    remaining_tiers = [tier for tier in ("broad", "niche", "micro") if tier not in preferred_tiers]
    fallback_entries: list[tuple[float, str]] = []
    for tier in remaining_tiers:
        for entry in _extract_tier_entries(hashtag_set, tier):
            tag_value = str(entry.get("tag", "")).strip().lstrip("#")
            if not tag_value or tag_value in seen:
                continue
            fallback_entries.append((float(entry.get("score", 0.0)), tag_value))

    for _, tag_value in sorted(fallback_entries, key=lambda item: item[0], reverse=True):
        if len(selected) >= max_tags:
            break
        if tag_value in seen:
            continue
        selected.append(f"#{tag_value}")
        seen.add(tag_value)

    return selected[:max_tags]


def route_platforms(input: PlatformRoutingInput) -> PlatformRoutingPlan:
    """
    Implements Section 5.5 Platform Routing Logic.

    Decision made:
    Produces per-platform routing decisions for caption strategy, hashtag selection,
    media transform requirements, and caption overflow actions.

    Spec section:
    Section 5.5.

    Rule priority order:
    1. Choose global caption strategy from style distance threshold.
    2. For each target platform:
       a) inherit global caption strategy,
       b) choose hashtags via platform tier strategy,
       c) assess media aspect-ratio mismatch,
       d) choose caption overflow action.
    3. Return an assembled routing plan.

    Edge cases handled:
    - Missing media asset skips transform checks.
    - Empty preferred ratio list yields zero mismatch.
    - Missing caption state defaults to use_as_is.
    - Duplicate tags are de-duplicated while preserving tier-priority order.
    """
    # 1. DETERMINE GLOBAL CAPTION STRATEGY
    if input.style_distance > ROUTING_STYLE_DISTANCE_THRESHOLD:
        global_strategy = "per_platform"
    else:
        global_strategy = "shared_base"

    # 2. BUILD DECISIONS PER PLATFORM
    decisions: list[PlatformRoutingDecision] = []
    for platform in input.target_platforms:
        # 2a. CAPTION STRATEGY
        caption_strategy = global_strategy

        # 2b. HASHTAG SELECTION
        hashtag_selection = _collect_hashtags_for_platform(platform, input.hashtag_set)

        # 2c. MEDIA TRANSFORM CHECK
        if input.media_asset is None:
            requires_media_transform = False
            media_transform_reason = None
        else:
            asset_ratio = input.media_asset.width_px / input.media_asset.height_px
            preferred = PLATFORM_PREFERRED_ASPECT_RATIOS.get(str(platform), [])
            min_mismatch = compute_aspect_ratio_mismatch(asset_ratio, preferred)
            if min_mismatch > ROUTING_ASPECT_MISMATCH_THRESHOLD:
                requires_media_transform = True
                best_ratio = preferred[0] if preferred else (1, 1)
                media_transform_reason = (
                    f"Asset ratio {asset_ratio:.2f} deviates "
                    f"{min_mismatch * 100:.1f}% from preferred "
                    f"{best_ratio[0]}:{best_ratio[1]}"
                )
            else:
                requires_media_transform = False
                media_transform_reason = None

        # 2d. CAPTION OVERFLOW CHECK
        caption_state = next(
            (state for state in input.caption_states if state.platform == platform),
            None,
        )
        if caption_state is None:
            caption_action = "use_as_is"
            caption_action_reason = None
        else:
            overflow_ratio = caption_state.overflow_ratio
            if overflow_ratio <= 0:
                caption_action = "use_as_is"
                caption_action_reason = None
            elif overflow_ratio <= ROUTING_OVERFLOW_SOFT_MAX:
                caption_action = "semantic_truncate"
                caption_action_reason = (
                    f"Caption exceeds limit by {overflow_ratio * 100:.1f}% "
                    "- within soft truncation range"
                )
            else:
                caption_action = "regenerate"
                caption_action_reason = (
                    f"Caption exceeds limit by {overflow_ratio * 100:.1f}% "
                    "- exceeds soft truncation range, full regeneration required"
                )

        decisions.append(
            PlatformRoutingDecision(
                platform=platform,
                caption_strategy=caption_strategy,
                hashtag_selection=hashtag_selection,
                requires_media_transform=requires_media_transform,
                media_transform_reason=media_transform_reason,
                caption_action=caption_action,
                caption_action_reason=caption_action_reason,
            )
        )

    # 3. ASSEMBLE AND RETURN
    return PlatformRoutingPlan(decisions=decisions, global_strategy=global_strategy)


def compute_aspect_ratio_mismatch(
    asset_ratio: float,
    preferred_ratios: list[tuple[int, int]],
) -> float:
    """
    Return the minimum relative mismatch between an asset ratio and preferred ratios.

    Returns 0.0 when no preferred ratios are provided.
    """
    if not preferred_ratios:
        return 0.0

    mismatches = []
    for width, height in preferred_ratios:
        preferred_ratio = width / height
        mismatches.append(abs(asset_ratio - preferred_ratio) / preferred_ratio)
    return min(mismatches)
