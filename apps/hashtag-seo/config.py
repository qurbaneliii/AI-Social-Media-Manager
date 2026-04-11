# FILE: apps/hashtag-seo/config.py
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

    relevance_cosine_weight: float = Field(0.35, alias="RELEVANCE_COSINE_WEIGHT")
    engagement_uplift_weight: float = Field(0.35, alias="ENGAGEMENT_UPLIFT_WEIGHT")
    recency_trend_weight: float = Field(0.20, alias="RECENCY_TREND_WEIGHT")
    brand_fit_weight: float = Field(0.10, alias="BRAND_FIT_WEIGHT")

    broad_threshold: int = Field(500000, alias="BROAD_THRESHOLD")
    niche_lower: int = Field(50000, alias="NICHE_LOWER")
    niche_upper: int = Field(499999, alias="NICHE_UPPER")
    micro_upper: int = Field(49999, alias="MICRO_UPPER")

    broad_quota: int = Field(3, alias="BROAD_QUOTA")
    niche_quota: int = Field(5, alias="NICHE_QUOTA")
    micro_quota: int = Field(5, alias="MICRO_QUOTA")

    borrow_penalty: float = Field(0.85, alias="BORROW_PENALTY")
    primary_kw_density_min: float = Field(0.015, alias="PRIMARY_KW_DENSITY_MIN")
    primary_kw_density_max: float = Field(0.025, alias="PRIMARY_KW_DENSITY_MAX")


def get_settings() -> Settings:
    return Settings()
