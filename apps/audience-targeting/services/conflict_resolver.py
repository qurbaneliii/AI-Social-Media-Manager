# FILE: apps/audience-targeting/services/conflict_resolver.py
from __future__ import annotations


class ConflictResolver:
    def __init__(self) -> None:
        pass

    async def process(self, company_config: dict, llm_inferred: dict) -> tuple[dict, list[str]]:
        """Apply age-range override policy when inferred bounds deviate by more than 10 years."""
        warnings: list[str] = []
        config_age = company_config.get("age_range")
        inferred_age = llm_inferred.get("age_range", {})

        if config_age and inferred_age:
            min_diff = abs(int(config_age.get("min_age", 0)) - int(inferred_age.get("min_age", 0)))
            max_diff = abs(int(config_age.get("max_age", 0)) - int(inferred_age.get("max_age", 0)))
            if min_diff > 10 or max_diff > 10:
                llm_inferred["age_range"] = config_age
                warnings.append("AUDIENCE_OVERRIDE")

        return llm_inferred, warnings
