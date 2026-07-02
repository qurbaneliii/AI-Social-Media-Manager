insert into public.prompt_templates (
  module_name,
  version,
  provider,
  model,
  system_prompt,
  user_prompt_template,
  schema_json,
  active
)
values
  (
    'caption_generation',
    1,
    'openai',
    'gpt-4o-mini',
    'You are ARIA, an expert social media manager. Write platform-native content that follows brand vocabulary and safety constraints.',
    'Create a {{platform}} post for {{company_name}} about {{topic}} with tone {{tone}} and CTA {{cta}}.',
    '{"type":"object","required":["body","hashtags"],"properties":{"body":{"type":"string"},"hashtags":{"type":"array","items":{"type":"string"}}}}'::jsonb,
    true
  ),
  (
    'hashtag_suggestions',
    1,
    'openai',
    'gpt-4o-mini',
    'You generate relevant broad, niche, and micro hashtag sets for social campaigns.',
    'Suggest hashtags for {{platform}} content about {{topic}} in {{industry_vertical}}.',
    '{"type":"object","required":["broad","niche","micro"],"properties":{"broad":{"type":"array"},"niche":{"type":"array"},"micro":{"type":"array"}}}'::jsonb,
    true
  )
on conflict (module_name, version) do update set
  provider = excluded.provider,
  model = excluded.model,
  system_prompt = excluded.system_prompt,
  user_prompt_template = excluded.user_prompt_template,
  schema_json = excluded.schema_json,
  active = excluded.active;
