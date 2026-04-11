# FILE: apps/scheduler/config.py
from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = Field(..., alias="DATABASE_URL")
    redis_url: str = Field(..., alias="REDIS_URL")
    s3_bucket: str = Field(..., alias="S3_BUCKET")
    llm_proxy_url: str = Field(..., alias="LLM_PROXY_URL")
    service_name: str = Field(..., alias="SERVICE_NAME")
    service_version: str = Field(..., alias="SERVICE_VERSION")
    otlp_endpoint: str = Field(..., alias="OTLP_ENDPOINT")
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    aws_region: str = Field(..., alias="AWS_REGION")
    kms_key_id: str = Field(..., alias="KMS_KEY_ID")

    temporal_address: str = Field("temporal:7233", alias="TEMPORAL_ADDRESS")
    temporal_namespace: str = Field("default", alias="TEMPORAL_NAMESPACE")
    temporal_task_queue: str = Field("aria-task-queue", alias="TEMPORAL_TASK_QUEUE")


def get_settings() -> Settings:
    return Settings()
