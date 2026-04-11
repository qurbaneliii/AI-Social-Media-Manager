# FILE: packages/types/inputs/company_onboarding.py
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..enums import CTAType, MarketSegment, PostArchiveFormat

ISO_ALPHA2_CODES = frozenset(
    {
        "AD","AE","AF","AG","AI","AL","AM","AO","AQ","AR","AS","AT","AU","AW","AX","AZ","BA","BB","BD","BE","BF","BG","BH","BI","BJ","BL","BM","BN","BO","BQ","BR","BS","BT","BV","BW","BY","BZ","CA","CC","CD","CF","CG","CH","CI","CK","CL","CM","CN","CO","CR","CU","CV","CW","CX","CY","CZ","DE","DJ","DK","DM","DO","DZ","EC","EE","EG","EH","ER","ES","ET","FI","FJ","FK","FM","FO","FR","GA","GB","GD","GE","GF","GG","GH","GI","GL","GM","GN","GP","GQ","GR","GS","GT","GU","GW","GY","HK","HM","HN","HR","HT","HU","ID","IE","IL","IM","IN","IO","IQ","IR","IS","IT","JE","JM","JO","JP","KE","KG","KH","KI","KM","KN","KP","KR","KW","KY","KZ","LA","LB","LC","LI","LK","LR","LS","LT","LU","LV","LY","MA","MC","MD","ME","MF","MG","MH","MK","ML","MM","MN","MO","MP","MQ","MR","MS","MT","MU","MV","MW","MX","MY","MZ","NA","NC","NE","NF","NG","NI","NL","NO","NP","NR","NU","NZ","OM","PA","PE","PF","PG","PH","PK","PL","PM","PN","PR","PS","PT","PW","PY","QA","RE","RO","RS","RU","RW","SA","SB","SC","SD","SE","SG","SH","SI","SJ","SK","SL","SM","SN","SO","SR","SS","ST","SV","SX","SY","SZ","TC","TD","TF","TG","TH","TJ","TK","TL","TM","TN","TO","TR","TT","TV","TW","TZ","UA","UG","UM","US","UY","UZ","VA","VC","VE","VG","VI","VN","VU","WF","WS","YE","YT","ZA","ZM","ZW"
    }
)
S3_URI_PATTERN = r"^s3://[a-z0-9.-]+/.+$"


class TargetMarket(BaseModel):
    """Implements Section 3.1.1 Input A nested target market model."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        populate_by_name=True,
        use_enum_values=True,
    )

    regions: Annotated[list[Annotated[str, Field(min_length=2, max_length=2)]], Field(min_length=1)]
    segments: Annotated[list[MarketSegment], Field(min_length=1)]
    persona_summary: Annotated[str, Field(max_length=500)] | None = None

    @field_validator("regions")
    @classmethod
    def validate_regions_iso_alpha2(cls, value: list[str]) -> list[str]:
        """Ensures each region is a valid ISO 3166-1 alpha-2 country code."""
        invalid = [region for region in value if region not in ISO_ALPHA2_CODES]
        if invalid:
            raise ValueError(f"Invalid ISO 3166-1 alpha-2 region codes: {invalid}")
        return value


class PlatformPresence(BaseModel):
    """Implements Section 3.1.1 Input A nested platform presence flags."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        populate_by_name=True,
        use_enum_values=True,
    )

    instagram: bool = False
    linkedin: bool = False
    facebook: bool = False
    x: bool = False
    tiktok: bool = False
    pinterest: bool = False

    @model_validator(mode="after")
    def validate_at_least_one_platform(self) -> "PlatformPresence":
        """Requires at least one enabled platform in presence flags."""
        if not any([self.instagram, self.linkedin, self.facebook, self.x, self.tiktok, self.pinterest]):
            raise ValueError("At least one platform must be enabled in platform_presence")
        return self


class PostingFrequencyGoal(BaseModel):
    """Implements Section 3.1.1 Input A nested posting frequency goals."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        populate_by_name=True,
        use_enum_values=True,
    )

    instagram: int = Field(ge=0, le=21)
    linkedin: int = Field(ge=0, le=14)
    facebook: int = Field(ge=0, le=21)
    x: int = Field(ge=0, le=70)
    tiktok: int = Field(ge=0, le=21)
    pinterest: int = Field(ge=0, le=35)


class PostArchiveReference(BaseModel):
    """Implements Section 3.1.1 Input A nested previous post archive reference."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        populate_by_name=True,
        use_enum_values=True,
    )

    format: PostArchiveFormat
    s3_uri: Annotated[str, Field(pattern=S3_URI_PATTERN)] | None = None


class CompanyOnboardingProfile(BaseModel):
    """Implements Section 3.1.1 Input A CompanyOnboardingProfile."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        populate_by_name=True,
        use_enum_values=True,
    )

    company_name: Annotated[str, Field(min_length=2, max_length=120)]
    industry_vertical: Annotated[str, Field(min_length=2, max_length=100)]
    target_market: TargetMarket
    brand_positioning_statement: Annotated[str, Field(min_length=30, max_length=500)]
    tone_of_voice_descriptors: Annotated[
        list[Annotated[str, Field(min_length=2, max_length=50)]],
        Field(min_length=3, max_length=20),
    ]
    competitor_list: Annotated[list[Annotated[str, Field(min_length=1, max_length=120)]], Field(min_length=1, max_length=20)]
    platform_presence: PlatformPresence
    posting_frequency_goal: PostingFrequencyGoal
    primary_cta_types: Annotated[list[CTAType], Field(min_length=1)]
    brand_color_hex_codes: Annotated[list[Annotated[str, Field(min_length=7, max_length=7)]], Field(min_length=1, max_length=10)]
    approved_vocabulary_list: list[Annotated[str, Field(min_length=1, max_length=50)]] = Field(default_factory=list)
    banned_vocabulary_list: list[Annotated[str, Field(min_length=1, max_length=50)]] = Field(default_factory=list)
    previous_post_archive: PostArchiveReference | None = None
    brand_guidelines_pdf: Annotated[str, Field(pattern=S3_URI_PATTERN)] | None = None
    logo_file: UUID | None = None
    sample_post_images: Annotated[list[UUID], Field(max_length=50)] = Field(default_factory=list)

    @field_validator("brand_color_hex_codes")
    @classmethod
    def validate_hex_colors(cls, value: list[str]) -> list[str]:
        """Validates hex colors in #RRGGBB format."""
        import re

        invalid = [item for item in value if re.fullmatch(r"^#[0-9A-Fa-f]{6}$", item) is None]
        if invalid:
            raise ValueError(f"Invalid hex colors: {invalid}")
        return value

    @model_validator(mode="after")
    def validate_approved_banned_disjoint(self) -> "CompanyOnboardingProfile":
        """Ensures approved and banned vocab lists do not overlap."""
        approved = {item.casefold() for item in self.approved_vocabulary_list}
        banned = {item.casefold() for item in self.banned_vocabulary_list}
        overlap = sorted(approved.intersection(banned))
        if overlap:
            raise ValueError(f"Vocabulary terms cannot be both approved and banned: {overlap}")
        return self

    @model_validator(mode="after")
    def validate_frequency_for_enabled_platforms(self) -> "CompanyOnboardingProfile":
        """Ensures inactive platforms have zero posting frequency goals."""
        pairs = {
            "instagram": (self.platform_presence.instagram, self.posting_frequency_goal.instagram),
            "linkedin": (self.platform_presence.linkedin, self.posting_frequency_goal.linkedin),
            "facebook": (self.platform_presence.facebook, self.posting_frequency_goal.facebook),
            "x": (self.platform_presence.x, self.posting_frequency_goal.x),
            "tiktok": (self.platform_presence.tiktok, self.posting_frequency_goal.tiktok),
            "pinterest": (self.platform_presence.pinterest, self.posting_frequency_goal.pinterest),
        }
        violations = [platform for platform, (enabled, frequency) in pairs.items() if (not enabled and frequency != 0)]
        if violations:
            raise ValueError(f"Inactive platforms must have zero frequency: {violations}")
        return self
