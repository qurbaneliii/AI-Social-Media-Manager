# FILE: apps/scheduler/services/core_logic.py
from __future__ import annotations

import structlog

from config import Settings
from models.input import WebhookInput, WorkflowRunInput
from models.output import WebhookOutput, WorkflowRunOutput
from services.dead_letter_writer import DeadLetterWriter
from services.metrics_normalizer import MetricsNormalizer
from services.oauth_refresh import OAuthRefreshService
from services.webhook_validator import WebhookValidator
from services.workflow_runner import WorkflowRunner

log = structlog.get_logger(__name__)


class SchedulerService:
    def __init__(self, settings: Settings, db_pool: object, llm_client: object) -> None:
        self.settings = settings
        self.oauth = OAuthRefreshService(llm_client, settings.llm_proxy_url)
        self.runner = WorkflowRunner(settings)
        self.validator = WebhookValidator(db_pool)
        self.normalizer = MetricsNormalizer()
        self.dead_letter = DeadLetterWriter(db_pool)

    async def run_workflow(self, payload: WorkflowRunInput) -> WorkflowRunOutput:
        """Run scheduler workflows with pre-publish OAuth refresh check."""
        refreshed = await self.oauth.process(payload.oauth_token_expires_at)
        if refreshed:
            log.info("step_completed", step="oauth_refresh", schedule_id=str(payload.schedule_id))
        return await self.runner.process(payload)

    async def handle_webhook(self, payload: WebhookInput, kms_secret: str, company_id) -> WebhookOutput:
        """Validate and normalize webhook payload before persistence."""
        valid = await self.validator.process(company_id, payload.platform.value, payload.payload, payload.signature, kms_secret)
        if not valid:
            log.error("webhook_rejected", platform=payload.platform.value)
            return WebhookOutput(status="rejected", event_type="signature_mismatch")

        _ = await self.normalizer.process(company_id, company_id, payload.platform.value, payload.payload)
        log.info("step_completed", step="metrics_normalization", platform=payload.platform.value)
        return WebhookOutput(status="accepted", event_type=str(payload.payload.get("event_type", "unknown")))

    async def write_dead_letter(self, schedule_id, company_id, payload: dict) -> dict:
        """Write dead-letter record and emit canonical dead-letter event body."""
        return await self.dead_letter.process(schedule_id, company_id, payload)
