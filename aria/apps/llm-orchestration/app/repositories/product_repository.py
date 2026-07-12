from __future__ import annotations

import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from ai.approval.schemas import ApprovalAction, ApprovalObjectType, ApprovalStatus
from ai.approval.transitions import validate_transition


def _dict(row: Any) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


def _json(value: Any) -> str:
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    return json.dumps(value, default=str)


def _decode(value: Any, fallback: Any) -> Any:
    if value is None:
        return fallback
    if isinstance(value, str):
        return json.loads(value)
    return value


def _approval_event(row: Any) -> dict[str, Any] | None:
    event = _dict(row)
    if event:
        event["requested_changes"] = _decode(event.get("requested_changes"), [])
        event["metadata"] = _decode(event.get("metadata"), {})
    return event


class ProductRepository:
    def __init__(self, pool: Any) -> None:
        self.pool = pool

    @asynccontextmanager
    async def connection(self) -> AsyncIterator[Any]:
        async with self.pool.acquire() as connection:
            yield connection

    async def ping(self) -> bool:
        async with self.connection() as connection:
            return bool(await connection.fetchval("SELECT true"))

    async def resolve_membership(self, user_id: str, workspace_id: str | None) -> dict[str, Any] | None:
        query = """
        SELECT m.workspace_id, m.user_id, m.role, w.name AS workspace_name, w.timezone,
               b.brand_id, b.name AS brand_name
        FROM ai_workspace_memberships m
        JOIN ai_workspaces w ON w.workspace_id = m.workspace_id
        LEFT JOIN LATERAL (
          SELECT brand_id, name
          FROM ai_brands
          WHERE workspace_id = m.workspace_id
          ORDER BY created_at, brand_id
          LIMIT 1
        ) b ON true
        WHERE m.user_id = $1
          AND ($2::text IS NULL OR m.workspace_id = $2)
        ORDER BY m.created_at, m.workspace_id
        LIMIT 1
        """
        async with self.connection() as connection:
            return _dict(await connection.fetchrow(query, user_id, workspace_id))

    async def get_brand_profile(self, workspace_id: str, brand_id: str | None = None) -> dict[str, Any] | None:
        query = """
        SELECT b.brand_id, b.name, m.brand_profile_json, m.profile_version,
               m.created_at, m.updated_at
        FROM ai_brands b
        LEFT JOIN ai_brand_memory m
          ON m.workspace_id = b.workspace_id AND m.brand_id = b.brand_id
        WHERE b.workspace_id = $1
          AND ($2::text IS NULL OR b.brand_id = $2)
        ORDER BY b.created_at, b.brand_id
        LIMIT 1
        """
        async with self.connection() as connection:
            row = _dict(await connection.fetchrow(query, workspace_id, brand_id))
        if row and row.get("brand_profile_json") is not None:
            row["brand_profile_json"] = _decode(row["brand_profile_json"], {})
        return row

    async def save_brand_profile(
        self,
        *,
        workspace_id: str,
        brand_id: str,
        brand_name: str,
        profile: dict[str, Any],
        expected_version: int | None,
    ) -> dict[str, Any] | None:
        async with self.connection() as connection, connection.transaction():
            brand = await connection.fetchrow(
                "SELECT brand_id FROM ai_brands WHERE workspace_id = $1 AND brand_id = $2 FOR UPDATE",
                workspace_id,
                brand_id,
            )
            if brand is None:
                return None
            current = await connection.fetchrow(
                "SELECT profile_version FROM ai_brand_memory WHERE workspace_id = $1 AND brand_id = $2 FOR UPDATE",
                workspace_id,
                brand_id,
            )
            current_version = int(current["profile_version"]) if current else 0
            if expected_version is not None and expected_version != current_version:
                return {"conflict": True, "profile_version": current_version}
            await connection.execute(
                "UPDATE ai_brands SET name = $3, updated_at = now() WHERE workspace_id = $1 AND brand_id = $2",
                workspace_id,
                brand_id,
                brand_name,
            )
            row = await connection.fetchrow(
                """
                INSERT INTO ai_brand_memory (brand_id, workspace_id, brand_profile_json, profile_version)
                VALUES ($1, $2, $3::jsonb, 1)
                ON CONFLICT (brand_id) DO UPDATE SET
                  workspace_id = EXCLUDED.workspace_id,
                  brand_profile_json = EXCLUDED.brand_profile_json,
                  profile_version = ai_brand_memory.profile_version + 1,
                  updated_at = now()
                WHERE ai_brand_memory.workspace_id = EXCLUDED.workspace_id
                RETURNING brand_id, workspace_id, brand_profile_json, profile_version, created_at, updated_at
                """,
                brand_id,
                workspace_id,
                _json(profile),
            )
            result = _dict(row)
            if result:
                result["brand_profile_json"] = _decode(result["brand_profile_json"], {})
            return result

    async def create_content(
        self,
        *,
        workspace_id: str,
        brand_id: str,
        owner_id: str,
        topic: str,
        content_type: str,
        campaign: str | None,
        packages: list[dict[str, Any]],
        mock_mode: bool,
        model: str | None,
        idempotency_key: str | None,
    ) -> str:
        if not packages:
            raise ValueError("At least one generated package is required.")
        first = packages[0]
        quality = first.get("quality_scores") or {}
        async with self.connection() as connection, connection.transaction():
            if idempotency_key:
                existing = await connection.fetchval(
                    "SELECT draft_id FROM ai_content_drafts WHERE workspace_id = $1 AND idempotency_key = $2",
                    workspace_id,
                    idempotency_key,
                )
                if existing is not None:
                    return str(existing)
            draft_id = await connection.fetchval(
                """
                INSERT INTO ai_content_drafts (
                  workspace_id, brand_id, owner_id, platform, content_type, topic,
                  campaign, content_package_json, approval_status, generation_status,
                  quality_scores_json, audit_metadata_json, prompt_version, model,
                  mock_mode, idempotency_key
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb, 'draft', 'generated',
                        $9::jsonb, $10::jsonb, 'v1', $11, $12, $13)
                RETURNING draft_id
                """,
                workspace_id,
                brand_id,
                owner_id,
                first.get("platform", "unknown"),
                content_type,
                topic,
                campaign,
                _json(first),
                _json(quality),
                _json({"mode": "mock" if mock_mode else "live", "package_count": len(packages)}),
                model if not mock_mode else None,
                mock_mode,
                idempotency_key,
            )
            selected_variant_id = None
            for index, package in enumerate(packages, 1):
                content_text = "\n\n".join(
                    str(package.get(key) or "").strip() for key in ("hook", "caption", "cta") if package.get(key)
                )
                scores = package.get("quality_scores") or {}
                variant_id = await connection.fetchval(
                    """
                    INSERT INTO ai_content_variants (
                      workspace_id, draft_id, platform, variant_order, content_text,
                      package_json, scores_json, is_selected, provider, model, token_usage_json
                    )
                    VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7::jsonb, $8, $9, $10, $11::jsonb)
                    RETURNING variant_id
                    """,
                    workspace_id,
                    draft_id,
                    package.get("platform", "unknown"),
                    index,
                    content_text,
                    _json(package),
                    _json(scores),
                    index == 1,
                    package.get("provider") if not mock_mode else None,
                    package.get("model") if not mock_mode else None,
                    _json(package.get("token_usage")) if package.get("token_usage") else None,
                )
                if index == 1:
                    selected_variant_id = variant_id
            await connection.execute(
                "UPDATE ai_content_drafts SET selected_variant_id = $2 WHERE draft_id = $1",
                draft_id,
                selected_variant_id,
            )
            return str(draft_id)

    async def save_user_draft(
        self,
        *,
        workspace_id: str,
        brand_id: str,
        owner_id: str,
        platform: str,
        content: str,
        topic: str,
        campaign: str | None,
    ) -> str:
        package = {
            "platform": platform,
            "content_type": "post",
            "hook": content.splitlines()[0][:240] if content.splitlines() else content[:240],
            "caption": content,
            "cta": "",
            "hashtags": [],
            "rationale": "User-authored draft.",
            "risks": [],
            "quality_scores": {},
        }
        return await self.create_content(
            workspace_id=workspace_id,
            brand_id=brand_id,
            owner_id=owner_id,
            topic=topic or content[:120],
            content_type="post",
            campaign=campaign,
            packages=[package],
            mock_mode=False,
            model=None,
            idempotency_key=None,
        )

    async def get_content(self, workspace_id: str, draft_id: str) -> dict[str, Any] | None:
        query = """
        SELECT d.*,
          COALESCE(jsonb_agg(
            jsonb_build_object(
              'variant_id', v.variant_id, 'platform', v.platform,
              'variant_order', v.variant_order, 'content_text', v.content_text,
              'package', v.package_json, 'scores', v.scores_json,
              'is_selected', v.is_selected, 'provider', v.provider,
              'model', v.model, 'token_usage', v.token_usage_json
            ) ORDER BY v.platform, v.variant_order
          ) FILTER (WHERE v.variant_id IS NOT NULL), '[]'::jsonb) AS variants
        FROM ai_content_drafts d
        LEFT JOIN ai_content_variants v
          ON v.draft_id = d.draft_id AND v.workspace_id = d.workspace_id
        WHERE d.workspace_id = $1 AND d.draft_id = $2::uuid
        GROUP BY d.draft_id
        """
        async with self.connection() as connection:
            row = _dict(await connection.fetchrow(query, workspace_id, draft_id))
        if row:
            for key, fallback in (
                ("variants", []),
                ("content_package_json", {}),
                ("quality_scores_json", {}),
                ("audit_metadata_json", {}),
            ):
                row[key] = _decode(row.get(key), fallback)
        return row

    async def list_content(
        self,
        *,
        workspace_id: str,
        search: str | None,
        platform: str | None,
        generation_status: str | None,
        approval_status: str | None,
        campaign: str | None,
        date_from: datetime | None,
        date_to: datetime | None,
        sort: str,
        order: str,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]:
        conditions = ["d.workspace_id = $1"]
        args: list[Any] = [workspace_id]
        values = {
            "search": (search, "(d.topic ILIKE ${n} OR d.content_package_json::text ILIKE ${n})", lambda v: f"%{v}%"),
            "platform": (platform, "d.platform = ${n}", str),
            "generation_status": (generation_status, "d.generation_status = ${n}", str),
            "approval_status": (approval_status, "d.approval_status = ${n}", str),
            "campaign": (campaign, "d.campaign = ${n}", str),
            "date_from": (date_from, "d.created_at >= ${n}", lambda v: v),
            "date_to": (date_to, "d.created_at <= ${n}", lambda v: v),
        }
        for value, template, transform in values.values():
            if value is not None and value != "":
                args.append(transform(value))
                conditions.append(template.format(n=len(args)))
        where = " AND ".join(conditions)
        sort_column = {"created_at": "d.created_at", "updated_at": "d.updated_at", "quality": "d.quality_scores_json"}.get(
            sort,
            "d.created_at",
        )
        direction = "ASC" if order.lower() == "asc" else "DESC"
        async with self.connection() as connection:
            total = int(await connection.fetchval(f"SELECT count(*) FROM ai_content_drafts d WHERE {where}", *args))
            page_args = [*args, limit, offset]
            rows = await connection.fetch(
                f"""
                SELECT d.*,
                  COALESCE(jsonb_agg(
                    jsonb_build_object(
                      'variant_id', v.variant_id, 'platform', v.platform,
                      'content_text', v.content_text, 'scores', v.scores_json,
                      'is_selected', v.is_selected, 'provider', v.provider, 'model', v.model
                    ) ORDER BY v.platform, v.variant_order
                  ) FILTER (WHERE v.variant_id IS NOT NULL), '[]'::jsonb) AS variants
                FROM ai_content_drafts d
                LEFT JOIN ai_content_variants v
                  ON v.draft_id = d.draft_id AND v.workspace_id = d.workspace_id
                WHERE {where}
                GROUP BY d.draft_id
                ORDER BY {sort_column} {direction}, d.draft_id {direction}
                LIMIT ${len(args) + 1} OFFSET ${len(args) + 2}
                """,
                *page_args,
            )
        items = [dict(row) for row in rows]
        for item in items:
            item["variants"] = _decode(item.get("variants"), [])
            item["quality_scores_json"] = _decode(item.get("quality_scores_json"), {})
        return items, total

    async def create_calendar_item(
        self,
        *,
        workspace_id: str,
        brand_id: str,
        content_draft_id: str,
        platform: str,
        planned_at: datetime,
        timezone: str,
    ) -> dict[str, Any] | None:
        async with self.connection() as connection, connection.transaction():
            content = await connection.fetchrow(
                "SELECT draft_id, topic, content_type FROM ai_content_drafts WHERE workspace_id = $1 AND draft_id = $2::uuid FOR UPDATE",
                workspace_id,
                content_draft_id,
            )
            if content is None:
                return None
            payload = {
                "content_draft_id": content_draft_id,
                "topic": content["topic"],
                "content_type": content["content_type"],
                "planned_at": planned_at.isoformat(),
                "timezone": timezone,
                "external_scheduling": False,
            }
            row = await connection.fetchrow(
                """
                INSERT INTO ai_calendar_draft_items (
                  workspace_id, brand_id, content_draft_id, platform,
                  scheduled_date, scheduled_time, planned_at, timezone,
                  draft_status, planning_state, approval_status,
                  approval_required, calendar_item_json, audit_metadata_json
                )
                VALUES ($1, $2, $3::uuid, $4, $5::date, $6::time, $7, $8,
                        'draft', 'draft_plan', 'draft', true, $9::jsonb, $10::jsonb)
                RETURNING *
                """,
                workspace_id,
                brand_id,
                content_draft_id,
                platform,
                planned_at.date(),
                planned_at.timetz().replace(tzinfo=None),
                planned_at,
                timezone,
                _json(payload),
                _json({"source": "internal"}),
            )
            await connection.execute(
                "UPDATE ai_content_drafts SET internal_planned_at = $3, updated_at = now() WHERE workspace_id = $1 AND draft_id = $2::uuid",
                workspace_id,
                content_draft_id,
                planned_at,
            )
            return _dict(row)

    async def list_calendar_items(
        self,
        *,
        workspace_id: str,
        date_from: datetime | None,
        date_to: datetime | None,
        platform: str | None,
        planning_state: str | None,
        approval_status: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]:
        conditions = ["c.workspace_id = $1"]
        args: list[Any] = [workspace_id]
        for value, clause in (
            (date_from, "c.planned_at >= ${n}"),
            (date_to, "c.planned_at <= ${n}"),
            (platform, "c.platform = ${n}"),
            (planning_state, "c.planning_state = ${n}"),
            (approval_status, "c.approval_status = ${n}"),
        ):
            if value is not None and value != "":
                args.append(value)
                conditions.append(clause.format(n=len(args)))
        where = " AND ".join(conditions)
        async with self.connection() as connection:
            total = int(await connection.fetchval(f"SELECT count(*) FROM ai_calendar_draft_items c WHERE {where}", *args))
            rows = await connection.fetch(
                f"""
                SELECT c.*, d.topic, d.generation_status, d.owner_id
                FROM ai_calendar_draft_items c
                LEFT JOIN ai_content_drafts d
                  ON d.workspace_id = c.workspace_id AND d.draft_id = c.content_draft_id
                WHERE {where}
                ORDER BY c.planned_at, c.calendar_item_id
                LIMIT ${len(args) + 1} OFFSET ${len(args) + 2}
                """,
                *args,
                limit,
                offset,
            )
        return [dict(row) for row in rows], total

    async def list_unscheduled_content(self, workspace_id: str, limit: int, offset: int) -> tuple[list[dict[str, Any]], int]:
        where = """
        d.workspace_id = $1
        AND d.generation_status IN ('draft', 'generated')
        AND NOT EXISTS (
          SELECT 1 FROM ai_calendar_draft_items c
          WHERE c.workspace_id = d.workspace_id
            AND c.content_draft_id = d.draft_id
            AND c.planning_state NOT IN ('failed')
        )
        """
        async with self.connection() as connection:
            total = int(await connection.fetchval(f"SELECT count(*) FROM ai_content_drafts d WHERE {where}", workspace_id))
            rows = await connection.fetch(
                f"""
                SELECT d.draft_id, d.brand_id, d.platform, d.topic, d.generation_status,
                       d.approval_status, d.quality_scores_json, d.created_at, d.updated_at,
                       v.content_text
                FROM ai_content_drafts d
                LEFT JOIN ai_content_variants v ON v.variant_id = d.selected_variant_id
                WHERE {where}
                ORDER BY d.created_at DESC, d.draft_id DESC
                LIMIT $2 OFFSET $3
                """,
                workspace_id,
                limit,
                offset,
            )
        return [dict(row) for row in rows], total

    async def update_calendar_item(
        self,
        *,
        workspace_id: str,
        item_id: str,
        planned_at: datetime | None,
        timezone: str | None,
        planning_state: str | None,
    ) -> dict[str, Any] | None:
        query = """
        UPDATE ai_calendar_draft_items
        SET planned_at = COALESCE($3, planned_at),
            scheduled_date = COALESCE($3::timestamptz::date, scheduled_date),
            scheduled_time = COALESCE($3::timestamptz::time, scheduled_time),
            timezone = COALESCE($4, timezone),
            planning_state = COALESCE($5, planning_state),
            updated_at = now()
        WHERE workspace_id = $1 AND calendar_item_id = $2::uuid
        RETURNING *
        """
        async with self.connection() as connection:
            return _dict(await connection.fetchrow(query, workspace_id, item_id, planned_at, timezone, planning_state))

    async def delete_calendar_item(self, workspace_id: str, item_id: str) -> bool:
        async with self.connection() as connection, connection.transaction():
            draft_id = await connection.fetchval(
                "DELETE FROM ai_calendar_draft_items WHERE workspace_id = $1 AND calendar_item_id = $2::uuid RETURNING content_draft_id",
                workspace_id,
                item_id,
            )
            if draft_id is None:
                return False
            await connection.execute(
                "UPDATE ai_content_drafts SET internal_planned_at = NULL, updated_at = now() WHERE workspace_id = $1 AND draft_id = $2",
                workspace_id,
                draft_id,
            )
            return True

    async def overview(self, workspace_id: str) -> dict[str, Any]:
        query = """
        SELECT
          (SELECT count(*) FROM ai_content_drafts WHERE workspace_id = $1 AND generation_status = 'draft') AS drafts,
          (SELECT count(*) FROM ai_content_drafts WHERE workspace_id = $1 AND approval_status = 'in_review') AS pending_approval,
          (SELECT count(*) FROM ai_content_drafts WHERE workspace_id = $1 AND approval_status = 'changes_requested') AS changes_requested,
          (SELECT count(*) FROM ai_calendar_draft_items WHERE workspace_id = $1 AND planning_state IN ('approved_internal','ready_for_scheduling')) AS approved_internal_plans,
          (SELECT count(*) FROM ai_content_drafts WHERE workspace_id = $1 AND generation_status = 'failed') AS failed_generations
        """
        async with self.connection() as connection:
            summary = _dict(await connection.fetchrow(query, workspace_id)) or {}
            recent = await connection.fetch(
                """
                SELECT d.draft_id, d.topic, d.platform, d.generation_status, d.approval_status,
                       d.created_at, v.content_text
                FROM ai_content_drafts d
                LEFT JOIN ai_content_variants v ON v.variant_id = d.selected_variant_id
                WHERE d.workspace_id = $1
                ORDER BY d.created_at DESC LIMIT 6
                """,
                workspace_id,
            )
            upcoming = await connection.fetch(
                """
                SELECT calendar_item_id, content_draft_id, platform, planned_at, timezone,
                       planning_state, approval_status
                FROM ai_calendar_draft_items
                WHERE workspace_id = $1 AND planned_at >= now()
                ORDER BY planned_at LIMIT 6
                """,
                workspace_id,
            )
        return {"summary": summary, "recent_content": [dict(row) for row in recent], "upcoming_plans": [dict(row) for row in upcoming]}

    async def insights(self, workspace_id: str, date_from: datetime | None, date_to: datetime | None) -> dict[str, Any]:
        conditions = ["workspace_id = $1"]
        args: list[Any] = [workspace_id]
        if date_from:
            args.append(date_from)
            conditions.append(f"created_at >= ${len(args)}")
        if date_to:
            args.append(date_to)
            conditions.append(f"created_at <= ${len(args)}")
        where = " AND ".join(conditions)
        async with self.connection() as connection:
            volume = int(await connection.fetchval(f"SELECT count(*) FROM ai_content_drafts WHERE {where}", *args))
            failures = int(
                await connection.fetchval(
                    f"SELECT count(*) FROM ai_content_drafts WHERE {where} AND generation_status = 'failed'",
                    *args,
                )
            )
            approvals = await connection.fetch(
                f"SELECT approval_status, count(*) AS count FROM ai_content_drafts WHERE {where} GROUP BY approval_status ORDER BY approval_status",
                *args,
            )
            platforms = await connection.fetch(
                f"SELECT platform, count(*) AS count FROM ai_content_drafts WHERE {where} GROUP BY platform ORDER BY platform",
                *args,
            )
            quality = await connection.fetchrow(
                f"""
                SELECT count(*) FILTER (WHERE (quality_scores_json->>'engagement_potential_score')::numeric >= 0.8) AS high,
                       count(*) FILTER (WHERE (quality_scores_json->>'engagement_potential_score')::numeric >= 0.5
                                         AND (quality_scores_json->>'engagement_potential_score')::numeric < 0.8) AS medium,
                       count(*) FILTER (WHERE (quality_scores_json->>'engagement_potential_score')::numeric < 0.5) AS low
                FROM ai_content_drafts WHERE {where}
                """,
                *args,
            )
        return {
            "content_generated": volume,
            "failed_generations": failures,
            "approval_distribution": [dict(row) for row in approvals],
            "platform_distribution": [dict(row) for row in platforms],
            "quality_distribution": _dict(quality) or {"high": 0, "medium": 0, "low": 0},
        }

    async def list_audit(self, workspace_id: str, limit: int, offset: int) -> list[dict[str, Any]]:
        query = """
        SELECT actor_user_id AS actor, action, object_type AS resource_type, created_at
        FROM ai_approval_audit_events
        WHERE workspace_id = $1
        ORDER BY created_at DESC
        LIMIT $2 OFFSET $3
        """
        async with self.connection() as connection:
            return [dict(row) for row in await connection.fetch(query, workspace_id, limit, offset)]

    async def list_approval_queue(
        self,
        *,
        workspace_id: str,
        brand_id: str | None,
        status: str | None,
        object_type: str | None,
        platform: str | None,
        created_after: datetime | None,
        created_before: datetime | None,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]:
        args: list[Any] = [workspace_id]
        common = ["workspace_id = $1"]
        for value, column, operator in (
            (brand_id, "brand_id", "="),
            (status, "approval_status", "="),
            (created_after, "created_at", ">="),
            (created_before, "created_at", "<="),
        ):
            if value is None or value == "":
                continue
            args.append(value)
            common.append(f"{column} {operator} ${len(args)}")
        where = " AND ".join(common)
        selected_types = {object_type} if object_type else {item.value for item in ApprovalObjectType}
        selects: list[str] = []
        if ApprovalObjectType.CONTENT_DRAFT.value in selected_types:
            platform_filter = ""
            if platform:
                args.append(platform)
                platform_filter = f" AND platform = ${len(args)}"
            selects.append(
                f"SELECT draft_id::text AS object_id, 'content_draft' AS object_type, brand_id, approval_status, "
                f"created_at, updated_at, platform, to_jsonb(ai_content_drafts) AS payload "
                f"FROM ai_content_drafts WHERE {where}{platform_filter}"
            )
        if ApprovalObjectType.CALENDAR_DRAFT.value in selected_types:
            platform_filter = ""
            if platform:
                args.append(platform)
                platform_filter = f" AND platform = ${len(args)}"
            selects.append(
                f"SELECT calendar_item_id::text, 'calendar_draft', brand_id, approval_status, created_at, updated_at, "
                f"platform, to_jsonb(ai_calendar_draft_items) FROM ai_calendar_draft_items WHERE {where}{platform_filter}"
            )
        if not platform and ApprovalObjectType.COMMUNITY_REPLY.value in selected_types:
            selects.append(
                f"SELECT reply_draft_id::text, 'community_reply', brand_id, approval_status, created_at, updated_at, "
                f"NULL::varchar, to_jsonb(ai_community_reply_drafts) FROM ai_community_reply_drafts WHERE {where}"
            )
        if not platform and ApprovalObjectType.REPORT_DRAFT.value in selected_types:
            selects.append(
                f"SELECT report_draft_id::text, 'report_draft', brand_id, approval_status, created_at, updated_at, "
                f"NULL::varchar, to_jsonb(ai_report_drafts) FROM ai_report_drafts WHERE {where}"
            )
        if not selects:
            return [], 0
        union = " UNION ALL ".join(selects)
        async with self.connection() as connection:
            total = int(await connection.fetchval(f"WITH queue AS ({union}) SELECT count(*) FROM queue", *args))
            rows = await connection.fetch(
                f"WITH queue AS ({union}) SELECT * FROM queue ORDER BY created_at DESC, object_id DESC "
                f"LIMIT ${len(args) + 1} OFFSET ${len(args) + 2}",
                *args,
                limit,
                offset,
            )
        items = [dict(row) for row in rows]
        for item in items:
            item["payload"] = _decode(item.get("payload"), {})
        return items, total

    async def get_approval_detail(
        self,
        workspace_id: str,
        object_type: ApprovalObjectType,
        object_id: str,
    ) -> tuple[dict[str, Any], list[dict[str, Any]]] | None:
        table, id_column = self._approval_table(object_type)
        async with self.connection() as connection:
            row = _dict(
                await connection.fetchrow(
                    f"SELECT * FROM {table} WHERE workspace_id = $1 AND {id_column} = $2::uuid",
                    workspace_id,
                    object_id,
                )
            )
            if row is None:
                return None
            events = await connection.fetch(
                """
                SELECT event_id, object_id, object_type, previous_status, new_status, action,
                       actor_user_id AS reviewer_id, actor_role AS reviewer_role, reason,
                       requested_changes, decision_timestamp AS timestamp, metadata_json AS metadata
                FROM ai_approval_audit_events
                WHERE workspace_id = $1 AND object_type = $2 AND object_id = $3
                ORDER BY created_at ASC, event_id ASC
                """,
                workspace_id,
                object_type.value,
                object_id,
            )
        return row, [_approval_event(event) or {} for event in events]

    async def apply_approval_decision(
        self,
        *,
        workspace_id: str,
        object_type: ApprovalObjectType,
        object_id: str,
        action: ApprovalAction,
        new_status: ApprovalStatus,
        actor_user_id: str,
        actor_role: str,
        reason: str,
        requested_changes: list[str],
        metadata: dict[str, Any],
    ) -> dict[str, Any] | None:
        table, id_column = self._approval_table(object_type)
        async with self.connection() as connection, connection.transaction():
            record = _dict(
                await connection.fetchrow(
                    f"SELECT * FROM {table} WHERE workspace_id = $1 AND {id_column} = $2::uuid FOR UPDATE",
                    workspace_id,
                    object_id,
                )
            )
            if record is None:
                return None
            previous_status = ApprovalStatus(str(record["approval_status"]))
            if previous_status == new_status:
                event = _approval_event(
                    await connection.fetchrow(
                        """
                        SELECT event_id, object_id, object_type, previous_status, new_status, action,
                               actor_user_id AS reviewer_id, actor_role AS reviewer_role, reason,
                               requested_changes, decision_timestamp AS timestamp, metadata_json AS metadata
                        FROM ai_approval_audit_events
                        WHERE workspace_id = $1 AND object_type = $2 AND object_id = $3 AND new_status = $4
                        ORDER BY created_at DESC LIMIT 1
                        """,
                        workspace_id,
                        object_type.value,
                        object_id,
                        new_status.value,
                    )
                )
                if event:
                    return {"record": record, "event": event, "idempotent": True}
            validate_transition(object_type, previous_status, new_status)
            record = _dict(
                await connection.fetchrow(
                    f"UPDATE {table} SET approval_status = $3, updated_at = now() "
                    f"WHERE workspace_id = $1 AND {id_column} = $2::uuid AND approval_status = $4 RETURNING *",
                    workspace_id,
                    object_id,
                    new_status.value,
                    previous_status.value,
                )
            )
            if record is None:
                return None
            if object_type == ApprovalObjectType.CALENDAR_DRAFT and new_status == ApprovalStatus.READY_FOR_SCHEDULING:
                await connection.execute(
                    "UPDATE ai_calendar_draft_items SET planning_state = 'ready_for_scheduling' "
                    "WHERE workspace_id = $1 AND calendar_item_id = $2::uuid",
                    workspace_id,
                    object_id,
                )
            event = _approval_event(
                await connection.fetchrow(
                    """
                    INSERT INTO ai_approval_audit_events (
                      workspace_id, object_id, object_type, previous_status, new_status, action,
                      reviewer_id, reviewer_role, actor_user_id, actor_role, reason,
                      requested_changes, decision_timestamp, metadata_json
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $7, $8, $9, $10::jsonb, now(), $11::jsonb)
                    RETURNING event_id, object_id, object_type, previous_status, new_status, action,
                              actor_user_id AS reviewer_id, actor_role AS reviewer_role, reason,
                              requested_changes, decision_timestamp AS timestamp, metadata_json AS metadata
                    """,
                    workspace_id,
                    object_id,
                    object_type.value,
                    previous_status.value,
                    new_status.value,
                    action.value,
                    actor_user_id,
                    actor_role,
                    reason,
                    _json(requested_changes),
                    _json(metadata),
                )
            )
            return {"record": record, "event": event, "idempotent": False}

    @staticmethod
    def _approval_table(object_type: ApprovalObjectType) -> tuple[str, str]:
        return {
            ApprovalObjectType.CONTENT_DRAFT: ("ai_content_drafts", "draft_id"),
            ApprovalObjectType.CALENDAR_DRAFT: ("ai_calendar_draft_items", "calendar_item_id"),
            ApprovalObjectType.COMMUNITY_REPLY: ("ai_community_reply_drafts", "reply_draft_id"),
            ApprovalObjectType.REPORT_DRAFT: ("ai_report_drafts", "report_draft_id"),
        }[object_type]
