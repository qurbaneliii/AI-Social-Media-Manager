CONTENT_GENERATION_PROMPT_V1 = """
Generate one structured content package for the request.
Return valid JSON with: platform, content_type, hook, caption, cta, hashtags, visual_brief,
video_script, carousel_structure, posting_recommendation, rationale, risks.
The package must match brand tone, include reasoning, avoid generic AI-sounding phrases,
avoid spammy hashtags, and list any factual or brand-safety risks.
""".strip()

QUALITY_REVIEW_PROMPT_V1 = """
Review the generated content package before it is shown to the user.
Return valid JSON with brand_consistency_score, platform_fit_score, clarity_score,
cta_strength_score, originality_score, factual_risk_score, safety_risk_score,
engagement_potential_score, approval_status, and improvement_notes.
Use approval_status=requires_human_review when content has factual, safety, compliance,
political, medical, legal, financial, crisis, or competitor-defamation risk.
""".strip()

BRAND_STRATEGY_PROMPT_V1 = """
Create a structured brand strategy plan from the provided brand profile, business goal,
platforms, and market context. Return valid JSON with positioning_statement,
audience_hypotheses, content_pillars, campaign_angles, platform_recommendations,
strategic_recommendations, risks, and approval_required. Keep recommendations
human-reviewable and avoid unsupported claims.
""".strip()

COMPETITOR_ANALYSIS_PROMPT_V1 = """
Analyze only the provided competitor/post data. Do not infer that browsing, scraping, or
external social API data was used. Return valid JSON with top_performing_content_types,
hook_patterns, recurring_themes, hashtag_patterns, tone_patterns, posting_patterns,
content_gaps, strategic_opportunities, risk_notes, and source_limitations.
""".strip()

TREND_RESEARCH_PROMPT_V1 = """
Analyze only the provided trends, keywords, topics, and examples. Do not browse or scrape.
Return valid JSON with relevant_topics, recommended_hashtags, content_formats,
trend_opportunities, platform_notes, risk_notes, and source_limitations.
""".strip()

HASHTAG_RECOMMENDATION_PROMPT_V1 = """
Generate a structured, non-spammy hashtag recommendation. Return valid JSON with
niche_hashtags, broad_hashtags, branded_hashtags, campaign_hashtags, location_hashtags,
trend_based_hashtags, risk_notes, and rationale. Avoid irrelevant stuffing and respect
platform hashtag limits.
""".strip()

VISUAL_CONCEPT_PROMPT_V1 = """
Generate a visual concept package only. Do not generate images. Return valid JSON with
visual_brief, carousel_concepts, short_form_video_concepts, image_generation_prompts,
design_direction, mood, scene, layout, creative_constraints, and risk_notes.
""".strip()

CALENDAR_PLANNING_PROMPT_V1 = """
Create an approval-based content calendar draft. Return valid JSON with items, rationale,
risk_notes, and approval_required. Balance pillars, campaign objectives, platform mix,
posting frequency, content types, and suggested posting times. Every item remains draft
status and requires human approval before publishing.
""".strip()

COMMUNITY_MANAGEMENT_PROMPT_V1 = """
Classify the provided comment or DM and draft a brand-safe reply. Do not auto-reply.
Return valid JSON with message_text, sentiment, intent, urgency, toxicity_risk,
crisis_risk, complaint_type, buying_intent, faq_intent, suggested_reply, confidence,
requires_human_review, escalation_reason, and auto_reply_allowed. auto_reply_allowed
must always be false.
""".strip()

REPORTING_INSIGHT_PROMPT_V1 = """
Convert the provided analytics data into readable performance insights. Return valid JSON
with summary, what_worked, what_failed, recommended_changes, next_experiments,
risk_notes, and chart_ready_data. Explain uncertainty when data is incomplete.
""".strip()
