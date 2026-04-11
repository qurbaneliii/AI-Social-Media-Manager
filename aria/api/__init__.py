# filename: api/__init__.py
# purpose: API router package exports.
# dependencies: api modules

from api.media import router as media_router
from api.oauth import router as oauth_router
from api.onboarding import router as onboarding_router
from api.posts import router as posts_router
from api.schedules import router as schedules_router, webhooks_router

__all__ = [
    "onboarding_router",
    "posts_router",
    "schedules_router",
    "webhooks_router",
    "media_router",
    "oauth_router",
]
