from __future__ import annotations

import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from ai.approval.schemas import ApprovalDecision
from ai.schemas.brand import BrandProfile
from ai.schemas.calendar import ContentCalendarPlan
from ai.schemas.community import CommunityMessageAnalysis
from ai.schemas.content import ContentRequest, GeneratedContentPackage
from ai.schemas.evaluation import AIQualityReview


class PersistenceAuditMetadata(BaseModel):
    prompt_version: str = "v1"
    model: str
    mock_mode: bool
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    quality_scores: dict[str, Any] = Field(default_factory=dict)
    token_usage: dict[str, int] = Field(default_factory=dict)
    extra: dict[str, Any] = Field(default_factory=dict)


def _json(value: Any) -> str:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    return json.dumps(value, default=str)


def _to_dict(row: Any) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


class AIPersistenceRepository:
    """Postgres-ready persistence adapter for AI drafts, reviews, calendars, and brand memory."""

    def __init__(self, pool: Any) -> None:
        self.pool = pool

    async def _resolve_workspace_id(self, conn: Any, *, workspace_id: str, brand_id: str) -> str:
        if not hasattr(conn, "fetchval"):
            return workspace_id
        existing = await conn.fetchval(
            """
            SELECT workspace_id
            FROM ai_brands
            WHERE brand_id = $1
            UNION ALL
            SELECT workspace_id
            FROM ai_brand_memory
            WHERE brand_id = $1
            LIMIT 1
            """,
            brand_id,
        )
        return str(existing) if existing else workspace_id

    async def _ensure_workspace_brand(
        self,
        conn: Any,
        *,
        workspace_id: str,
        brand_id: str,
        brand_name: str | None = None,
    ) -> None:
        if not hasattr(conn, "execute"):
            return
        workspace_id = await self._resolve_workspace_id(conn, workspace_id=workspace_id, brand_id=brand_id)
        await conn.execute(
            """
            INSERT INTO ai_workspaces (workspace_id, name)
            VALUES ($1, $2)
            ON CONFLICT (workspace_id) DO NOTHING
            """,
            workspace_id,
            brand_name or workspace_id,
        )
        await conn.execute(
            """
            INSERT INTO ai_brands (brand_id, workspace_id, name)
            VALUES ($1, $2, $3)
            ON CONFLICT (brand_id) DO UPDATE
            SET name = EXCLUDED.name,
                updated_at = now()
            """,
            brand_id,
            workspace_id,
            brand_name or brand_id,
        )

    @asynccontextmanager
    async def _connection(self) -> AsyncIterator[Any]:
        acquired = self.pool.acquire()
        if hasattr(acquired, "__aenter__"):
            async with acquired as conn:
                yield conn
            return
        conn = await acquired
        try:
            yield conn
        finally:
            release = getattr(self.pool, "release", None)
            if release is not None:
                await release(conn)

    async def save_brand_profile(self, profile: BrandProfile) -> dict[str, Any]:
        query = """
        INSERT INTO ai_brand_memory (brand_id, workspace_id, brand_profile_json)
        VALUES ($1, $2, $3::jsonb)
        ON CONFLICT (brand_id)
        DO UPDATE SET
            workspace_id = EXCLUDED.workspace_id,
            brand_profile_json = EXCLUDED.brand_profile_json,
            updated_at = now()
        RETURNING *
        """
        async with self._connection() as conn:
            workspace_id = await self._resolve_workspace_id(
                conn,
                workspace_id=profile.brand_id,
                brand_id=profile.brand_id,
            )
            await self._ensure_workspace_brand(
                conn,
                workspace_id=workspace_id,
                brand_id=profile.brand_id,
                brand_name=profile.brand_name,
            )
            row = await conn.fetchrow(query, profile.brand_id, workspace_id, _json(profile))
            return _to_dict(row) or {}

    async def load_brand_profile(self, brand_id: str) -> BrandProfile | None:
        query = "SELECT brand_profile_json FROM ai_brand_memory WHERE brand_id = $1"
        async with self._connection() as conn:
            row = await conn.fetchrow(query, brand_id)
        data = _to_dict(row)
        if not data:
            return None
        profile_json = data["brand_profile_json"]
        if isinstance(profile_json, str):
            profile_json = json.loads(profile_json)
        return BrandProfile.model_validate(profile_json)

    async def save_content_draft(
        self,
        request: ContentRequest,
        package: GeneratedContentPackage,
        audit_metadata: PersistenceAuditMetadata,
    ) -> dict[str, Any]:
        review = package.quality_scores
        approval_status = "draft"
        quality_scores = review.model_dump(mode="json") if review else {}
        query = """
        INSERT INTO ai_content_drafts (
            workspace_id, brand_id, platform, content_type, topic, content_package_json,
            approval_status, quality_scores_json, audit_metadata_json,
            prompt_version, model, mock_mode
        )
        VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7, $8::jsonb, $9::jsonb, $10, $11, $12)
        RETURNING *
        """
        workspace_id = request.brand_profile.brand_id
        args = (
            workspace_id,
            request.brand_profile.brand_id,
            package.platform,
            package.content_type,
            request.topic,
            _json(package),
            approval_status,
            _json(quality_scores),
            _json(audit_metadata),
            audit_metadata.prompt_version,
            audit_metadata.model,
            audit_metadata.mock_mode,
        )
        async with self._connection() as conn:
            await self._ensure_workspace_brand(
                conn,
                workspace_id=workspace_id,
                brand_id=request.brand_profile.brand_id,
                brand_name=request.brand_profile.brand_name,
            )
            row = await conn.fetchrow(query, *args)
            return _to_dict(row) or {}

    async def get_content_draft_by_id(self, draft_id: str) -> dict[str, Any] | None:
        query = "SELECT * FROM ai_content_drafts WHERE draft_id = $1::uuid"
        async with self._connection() as conn:
            row = await conn.fetchrow(query, draft_id)
            return _to_dict(row)

    async def update_content_draft_approval_status(self, draft_id: str, status: str) -> dict[str, Any]:
        query = """
        UPDATE ai_content_drafts
        SET approval_status = $2,
            updated_at = now()
        WHERE draft_id = $1::uuid
        RETURNING *
        """
        async with self._connection() as conn:
            row = await conn.fetchrow(query, draft_id, status)
            return _to_dict(row) or {}

    async def list_content_drafts(
        self,
        brand_id: str | None = None,
        status: str | None = None,
        platform: str | None = None,
        limit: int = 100,
        offset: int = 0,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
    ) -> list[dict[str, Any]]:
        conditions: list[str] = []
        args: list[Any] = []
        if brand_id:
            args.append(brand_id)
            conditions.append(f"brand_id = ${len(args)}")
        if status:
            args.append(status)
            conditions.append(f"approval_status = ${len(args)}")
        if platform:
            args.append(platform)
            conditions.append(f"platform = ${len(args)}")
        if created_after:
            args.append(created_after)
            conditions.append(f"created_at >= ${len(args)}")
        if created_before:
            args.append(created_before)
            conditions.append(f"created_at <= ${len(args)}")
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        args.extend([limit, offset])
        query = f"SELECT * FROM ai_content_drafts {where} ORDER BY created_at DESC LIMIT ${len(args) - 1} OFFSET ${len(args)}"
        async with self._connection() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]

    async def save_quality_review(
        self,
        *,
        draft_id: str | None,
        brand_id: str,
        review: AIQualityReview,
        audit_metadata: PersistenceAuditMetadata,
    ) -> dict[str, Any]:
        query = """
        INSERT INTO ai_quality_reviews (
            draft_id, brand_id, approval_status, quality_scores_json,
            improvement_notes, audit_metadata_json, model, mock_mode
        )
        VALUES ($1::uuid, $2, $3, $4::jsonb, $5::text[], $6::jsonb, $7, $8)
        RETURNING *
        """
        args = (
            draft_id,
            brand_id,
            review.approval_status,
            _json(review),
            review.improvement_notes,
            _json(audit_metadata),
            audit_metadata.model,
            audit_metadata.mock_mode,
        )
        async with self._connection() as conn:
            await self._ensure_workspace_brand(conn, workspace_id=brand_id, brand_id=brand_id)
            row = await conn.fetchrow(query, *args)
            return _to_dict(row) or {}

    async def save_calendar_draft_items(
        self,
        *,
        brand_id: str,
        plan: ContentCalendarPlan,
        audit_metadata: PersistenceAuditMetadata,
    ) -> list[dict[str, Any]]:
        query = """
        INSERT INTO ai_calendar_draft_items (
            workspace_id, brand_id, platform, scheduled_date, scheduled_time, draft_status,
            approval_required, calendar_item_json, audit_metadata_json
        )
        VALUES ($1, $2, $3, $4::date, $5::time, $6, $7, $8::jsonb, $9::jsonb)
        RETURNING *
        """
        rows: list[dict[str, Any]] = []
        workspace_id = brand_id
        async with self._connection() as conn:
            await self._ensure_workspace_brand(conn, workspace_id=workspace_id, brand_id=brand_id)
            for item in plan.items:
                row = await conn.fetchrow(
                    query,
                    workspace_id,
                    brand_id,
                    item.platform,
                    item.date,
                    item.time,
                    item.draft_status,
                    item.approval_required,
                    _json(item),
                    _json(audit_metadata),
                )
                rows.append(_to_dict(row) or {})
        return rows

    async def get_calendar_draft_item_by_id(self, calendar_item_id: str) -> dict[str, Any] | None:
        query = "SELECT * FROM ai_calendar_draft_items WHERE calendar_item_id = $1::uuid"
        async with self._connection() as conn:
            row = await conn.fetchrow(query, calendar_item_id)
            return _to_dict(row)

    async def update_calendar_draft_approval_status(self, calendar_item_id: str, status: str) -> dict[str, Any]:
        query = """
        UPDATE ai_calendar_draft_items
        SET approval_status = $2,
            draft_status = $2,
            updated_at = now()
        WHERE calendar_item_id = $1::uuid
        RETURNING *
        """
        async with self._connection() as conn:
            row = await conn.fetchrow(query, calendar_item_id, status)
            return _to_dict(row) or {}

    async def list_calendar_drafts(
        self,
        brand_id: str | None = None,
        status: str | None = None,
        platform: str | None = None,
        limit: int = 100,
        offset: int = 0,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
    ) -> list[dict[str, Any]]:
        conditions: list[str] = []
        args: list[Any] = []
        if brand_id:
            args.append(brand_id)
            conditions.append(f"brand_id = ${len(args)}")
        if status:
            args.append(status)
            conditions.append(f"approval_status = ${len(args)}")
        if platform:
            args.append(platform)
            conditions.append(f"platform = ${len(args)}")
        if created_after:
            args.append(created_after)
            conditions.append(f"created_at >= ${len(args)}")
        if created_before:
            args.append(created_before)
            conditions.append(f"created_at <= ${len(args)}")
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        args.extend([limit, offset])
        query = f"SELECT * FROM ai_calendar_draft_items {where} ORDER BY scheduled_date, scheduled_time LIMIT ${len(args) - 1} OFFSET ${len(args)}"
        async with self._connection() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]

    async def save_community_reply_draft(
        self,
        *,
        brand_id: str,
        analysis: CommunityMessageAnalysis,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        query = """
        INSERT INTO ai_community_reply_drafts (
            workspace_id, brand_id, original_message_text, sentiment, intent, urgency,
            toxicity_risk, crisis_risk, suggested_reply, confidence,
            requires_human_review, escalation_reason, auto_reply_allowed,
            approval_status, metadata_json
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, false, 'draft', $13::jsonb)
        RETURNING *
        """
        workspace_id = brand_id
        args = (
            workspace_id,
            brand_id,
            analysis.message_text,
            analysis.sentiment,
            analysis.intent,
            analysis.urgency,
            analysis.toxicity_risk,
            analysis.crisis_risk,
            analysis.suggested_reply,
            analysis.confidence,
            analysis.requires_human_review,
            analysis.escalation_reason,
            _json(metadata or {}),
        )
        async with self._connection() as conn:
            await self._ensure_workspace_brand(conn, workspace_id=workspace_id, brand_id=brand_id)
            row = await conn.fetchrow(query, *args)
            return _to_dict(row) or {}

    async def get_community_reply_draft_by_id(self, reply_draft_id: str) -> dict[str, Any] | None:
        query = "SELECT * FROM ai_community_reply_drafts WHERE reply_draft_id = $1::uuid"
        async with self._connection() as conn:
            row = await conn.fetchrow(query, reply_draft_id)
            return _to_dict(row)

    async def update_community_reply_approval_status(self, reply_draft_id: str, status: str) -> dict[str, Any]:
        query = """
        UPDATE ai_community_reply_drafts
        SET approval_status = $2,
            auto_reply_allowed = false,
            updated_at = now()
        WHERE reply_draft_id = $1::uuid
        RETURNING *
        """
        async with self._connection() as conn:
            row = await conn.fetchrow(query, reply_draft_id, status)
            return _to_dict(row) or {}

    async def list_community_reply_drafts(
        self,
        brand_id: str | None = None,
        status: str | None = None,
        platform: str | None = None,
        limit: int = 100,
        offset: int = 0,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
    ) -> list[dict[str, Any]]:
        conditions: list[str] = []
        args: list[Any] = []
        if brand_id:
            args.append(brand_id)
            conditions.append(f"brand_id = ${len(args)}")
        if status:
            args.append(status)
            conditions.append(f"approval_status = ${len(args)}")
        if platform:
            args.append(platform)
            conditions.append(f"metadata_json->>'platform' = ${len(args)}")
        if created_after:
            args.append(created_after)
            conditions.append(f"created_at >= ${len(args)}")
        if created_before:
            args.append(created_before)
            conditions.append(f"created_at <= ${len(args)}")
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        args.extend([limit, offset])
        query = f"SELECT * FROM ai_community_reply_drafts {where} ORDER BY created_at DESC LIMIT ${len(args) - 1} OFFSET ${len(args)}"
        async with self._connection() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]

    async def save_report_draft(
        self,
        *,
        brand_id: str,
        report_type: str,
        date_range: str,
        insight_payload: dict[str, Any],
        recommendations: list[str],
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        query = """
        INSERT INTO ai_report_drafts (
            workspace_id, brand_id, report_type, date_range, insight_payload_json,
            recommendations_json, approval_status, metadata_json
        )
        VALUES ($1, $2, $3, $4, $5::jsonb, $6::jsonb, 'draft', $7::jsonb)
        RETURNING *
        """
        workspace_id = brand_id
        async with self._connection() as conn:
            await self._ensure_workspace_brand(conn, workspace_id=workspace_id, brand_id=brand_id)
            row = await conn.fetchrow(
                query,
                workspace_id,
                brand_id,
                report_type,
                date_range,
                _json(insight_payload),
                _json(recommendations),
                _json(metadata or {}),
            )
            return _to_dict(row) or {}

    async def get_report_draft_by_id(self, report_draft_id: str) -> dict[str, Any] | None:
        query = "SELECT * FROM ai_report_drafts WHERE report_draft_id = $1::uuid"
        async with self._connection() as conn:
            row = await conn.fetchrow(query, report_draft_id)
            return _to_dict(row)

    async def update_report_draft_approval_status(self, report_draft_id: str, status: str) -> dict[str, Any]:
        query = """
        UPDATE ai_report_drafts
        SET approval_status = $2,
            updated_at = now()
        WHERE report_draft_id = $1::uuid
        RETURNING *
        """
        async with self._connection() as conn:
            row = await conn.fetchrow(query, report_draft_id, status)
            return _to_dict(row) or {}

    async def list_report_drafts(
        self,
        brand_id: str | None = None,
        status: str | None = None,
        platform: str | None = None,
        limit: int = 100,
        offset: int = 0,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
    ) -> list[dict[str, Any]]:
        conditions: list[str] = []
        args: list[Any] = []
        if brand_id:
            args.append(brand_id)
            conditions.append(f"brand_id = ${len(args)}")
        if status:
            args.append(status)
            conditions.append(f"approval_status = ${len(args)}")
        if platform:
            args.append(platform)
            conditions.append(f"metadata_json->>'platform' = ${len(args)}")
        if created_after:
            args.append(created_after)
            conditions.append(f"created_at >= ${len(args)}")
        if created_before:
            args.append(created_before)
            conditions.append(f"created_at <= ${len(args)}")
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        args.extend([limit, offset])
        query = f"SELECT * FROM ai_report_drafts {where} ORDER BY created_at DESC LIMIT ${len(args) - 1} OFFSET ${len(args)}"
        async with self._connection() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]

    async def store_approval_audit_event(self, decision: ApprovalDecision) -> dict[str, Any]:
        workspace_id, brand_id = await self._audit_scope(decision)
        query = """
        INSERT INTO ai_approval_audit_events (
            workspace_id, object_id, object_type, previous_status, new_status, action,
            reviewer_id, reviewer_role, reason, requested_changes,
            decision_timestamp, metadata_json
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10::jsonb, $11, $12::jsonb)
        RETURNING *
        """
        args = (
            workspace_id,
            decision.object_id,
            decision.object_type.value,
            decision.previous_status.value if decision.previous_status else None,
            decision.new_status.value,
            decision.action.value,
            decision.reviewer_id,
            decision.reviewer_role,
            decision.reason,
            _json(decision.requested_changes),
            decision.timestamp,
            _json(decision.metadata),
        )
        async with self._connection() as conn:
            if not hasattr(conn, "execute"):
                legacy_row = await conn.fetchrow(
                    query,
                    decision.object_id,
                    decision.object_type.value,
                    decision.previous_status.value if decision.previous_status else None,
                    decision.new_status.value,
                    decision.action.value,
                    decision.reviewer_id,
                    decision.reviewer_role,
                    decision.reason,
                    _json(decision.requested_changes),
                    decision.timestamp,
                    _json(decision.metadata),
                )
                return self._approval_event_from_row(_to_dict(legacy_row) or {})
            await self._ensure_workspace_brand(conn, workspace_id=workspace_id, brand_id=brand_id)
            row = await conn.fetchrow(query, *args)
            data = _to_dict(row) or {}
            return self._approval_event_from_row(data)

    async def list_approval_audit_events(self, object_type: str, object_id: str) -> list[dict[str, Any]]:
        query = """
        SELECT *
        FROM ai_approval_audit_events
        WHERE object_type = $1 AND object_id = $2
        ORDER BY created_at ASC
        """
        async with self._connection() as conn:
            rows = await conn.fetch(query, object_type, object_id)
            return [self._approval_event_from_row(dict(row)) for row in rows]

    def _approval_event_from_row(self, row: dict[str, Any]) -> dict[str, Any]:
        requested_changes = row.get("requested_changes") or []
        metadata = row.get("metadata_json") or {}
        if isinstance(requested_changes, str):
            requested_changes = json.loads(requested_changes)
        if isinstance(metadata, str):
            metadata = json.loads(metadata)
        return {
            "event_id": str(row.get("event_id")) if row.get("event_id") is not None else None,
            "object_id": row.get("object_id"),
            "object_type": row.get("object_type"),
            "previous_status": row.get("previous_status"),
            "new_status": row.get("new_status"),
            "action": row.get("action"),
            "reviewer_id": row.get("reviewer_id"),
            "reviewer_role": row.get("reviewer_role"),
            "reason": row.get("reason") or "",
            "requested_changes": requested_changes,
            "timestamp": row.get("decision_timestamp") or row.get("created_at") or datetime.now(UTC),
            "metadata": metadata,
        }

    async def _audit_scope(self, decision: ApprovalDecision) -> tuple[str, str]:
        metadata_workspace_id = decision.metadata.get("workspace_id")
        metadata_brand_id = decision.metadata.get("brand_id")
        if metadata_workspace_id and metadata_brand_id:
            return str(metadata_workspace_id), str(metadata_brand_id)

        query_map = {
            "content_draft": ("ai_content_drafts", "draft_id"),
            "calendar_draft": ("ai_calendar_draft_items", "calendar_item_id"),
            "community_reply": ("ai_community_reply_drafts", "reply_draft_id"),
            "report_draft": ("ai_report_drafts", "report_draft_id"),
        }
        table, id_column = query_map[decision.object_type.value]
        query = f"SELECT workspace_id, brand_id FROM {table} WHERE {id_column} = $1::uuid"
        async with self._connection() as conn:
            row = await conn.fetchrow(query, decision.object_id)
        record = _to_dict(row)
        if record and record.get("workspace_id") and record.get("brand_id"):
            return str(record["workspace_id"]), str(record["brand_id"])

        fallback = str(metadata_workspace_id or metadata_brand_id or decision.object_id)
        return fallback, str(metadata_brand_id or fallback)
