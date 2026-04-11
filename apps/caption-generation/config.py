# FILE: apps/caption-generation/config.py
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

    engagement_predicted_weight: float = Field(0.30, alias="ENGAGEMENT_PREDICTED_WEIGHT")
    tone_match_weight: float = Field(0.25, alias="TONE_MATCH_WEIGHT")
    cta_presence_weight: float = Field(0.15, alias="CTA_PRESENCE_WEIGHT")
    keyword_inclusion_weight: float = Field(0.15, alias="KEYWORD_INCLUSION_WEIGHT")
    platform_compliance_weight: float = Field(0.15, alias="PLATFORM_COMPLIANCE_WEIGHT")


def get_settings() -> Settings:
    return Settings()
