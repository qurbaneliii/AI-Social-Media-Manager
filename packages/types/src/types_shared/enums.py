# FILE: packages/types/src/types_shared/enums.py
from __future__ import annotations

from enum import Enum


class Platform(str, Enum):
    instagram = "instagram"
    linkedin = "linkedin"
    facebook = "facebook"
    x = "x"
    tiktok = "tiktok"
    pinterest = "pinterest"


class PostIntent(str, Enum):
    announce = "announce"
    educate = "educate"
    promote = "promote"
    engage = "engage"
    inspire = "inspire"
    crisis_response = "crisis_response"


class ApprovalMode(str, Enum):
    human = "human"
    auto = "auto"
