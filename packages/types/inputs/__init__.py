# FILE: packages/types/inputs/__init__.py
from .company_onboarding import CompanyOnboardingProfile, PlatformPresence, PostArchiveReference, PostingFrequencyGoal, TargetMarket
from .performance_feedback import PerformanceFeedback, PerformanceFeedbackBatch
from .post_request import AttachedMedia, PostGenerationRequest

__all__ = [
    "TargetMarket",
    "PlatformPresence",
    "PostingFrequencyGoal",
    "PostArchiveReference",
    "CompanyOnboardingProfile",
    "AttachedMedia",
    "PostGenerationRequest",
    "PerformanceFeedback",
    "PerformanceFeedbackBatch",
]
