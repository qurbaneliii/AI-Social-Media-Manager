create extension if not exists pgcrypto;
create extension if not exists citext;
create extension if not exists vector with schema extensions;

create type public.app_role as enum ('agency_admin', 'brand_manager', 'content_creator', 'analyst');
create type public.post_status as enum ('draft', 'generating', 'generated', 'scheduled', 'published', 'failed');
create type public.schedule_status as enum ('queued', 'awaiting_approval', 'publishing', 'published', 'failed', 'dead_letter');
create type public.social_platform as enum ('linkedin', 'twitter', 'instagram', 'facebook', 'tiktok', 'pinterest');

create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email citext not null unique,
  full_name text,
  default_role public.app_role not null default 'brand_manager',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.companies (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  industry_vertical text not null,
  target_market jsonb not null default '{}'::jsonb,
  timezone text not null default 'UTC',
  plan_tier text not null default 'starter',
  created_by uuid references public.profiles(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.memberships (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references public.companies(id) on delete cascade,
  user_id uuid not null references public.profiles(id) on delete cascade,
  role public.app_role not null,
  created_at timestamptz not null default now(),
  unique (company_id, user_id)
);

create table public.brand_profiles (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null unique references public.companies(id) on delete cascade,
  positioning_statement text,
  tone_descriptors text[] not null default '{}',
  tone_fingerprint jsonb not null default '{}'::jsonb,
  visual_style jsonb not null default '{}'::jsonb,
  approved_vocabulary text[] not null default '{}',
  banned_vocabulary text[] not null default '{}',
  confidence numeric(4,3),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.campaigns (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references public.companies(id) on delete cascade,
  name text not null,
  description text,
  starts_at timestamptz,
  ends_at timestamptz,
  created_by uuid references public.profiles(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.posts (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references public.companies(id) on delete cascade,
  campaign_id uuid references public.campaigns(id) on delete set null,
  intent text not null,
  core_message text not null,
  topic text,
  status public.post_status not null default 'draft',
  platform_targets public.social_platform[] not null default '{}',
  context_snapshot jsonb not null default '{}'::jsonb,
  generated_package jsonb,
  selected_content_id uuid,
  quality_score numeric(5,2),
  created_by uuid references public.profiles(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.generated_content (
  id uuid primary key default gen_random_uuid(),
  post_id uuid not null references public.posts(id) on delete cascade,
  company_id uuid not null references public.companies(id) on delete cascade,
  platform public.social_platform not null,
  variant_order smallint not null check (variant_order between 1 and 5),
  body text not null,
  hashtags text[] not null default '{}',
  scores jsonb not null default '{}'::jsonb,
  provider text,
  model text,
  is_selected boolean not null default false,
  created_at timestamptz not null default now(),
  unique (post_id, platform, variant_order)
);

alter table public.posts
  add constraint posts_selected_content_fk foreign key (selected_content_id) references public.generated_content(id) on delete set null;

create table public.scheduled_posts (
  id uuid primary key default gen_random_uuid(),
  post_id uuid not null references public.posts(id) on delete cascade,
  company_id uuid not null references public.companies(id) on delete cascade,
  platform public.social_platform not null,
  run_at_utc timestamptz not null,
  status public.schedule_status not null default 'queued',
  approval_mode text not null default 'human' check (approval_mode in ('human', 'auto')),
  approved_by uuid references public.profiles(id) on delete set null,
  approved_at timestamptz,
  retry_count integer not null default 0,
  max_retries integer not null default 5,
  next_retry_at timestamptz,
  external_post_id text,
  error_code text,
  error_message text,
  idempotency_key text not null,
  created_at timestamptz not null default now(),
  unique (platform, idempotency_key)
);

create table public.social_accounts (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references public.companies(id) on delete cascade,
  platform public.social_platform not null,
  account_ref text not null,
  display_name text,
  access_token_encrypted text,
  refresh_token_encrypted text,
  token_expires_at timestamptz,
  scopes text[] not null default '{}',
  status text not null default 'active',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (company_id, platform, account_ref)
);

create table public.media_assets (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references public.companies(id) on delete cascade,
  uploaded_by uuid references public.profiles(id) on delete set null,
  storage_bucket text not null default 'media-assets',
  storage_path text not null,
  original_filename text,
  mime_type text,
  size_bytes bigint,
  width integer,
  height integer,
  alt_text text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique (storage_bucket, storage_path)
);

create table public.analytics_events (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references public.companies(id) on delete cascade,
  post_id uuid references public.posts(id) on delete set null,
  platform public.social_platform not null,
  external_post_id text,
  impressions bigint not null default 0,
  reach bigint not null default 0,
  clicks bigint not null default 0,
  saves bigint not null default 0,
  shares bigint not null default 0,
  comments bigint not null default 0,
  engagement_rate numeric(8,6) not null default 0,
  captured_at timestamptz not null default now(),
  source text not null default 'manual' check (source in ('webhook', 'pull', 'manual')),
  raw_payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table public.ai_generations (
  id uuid primary key default gen_random_uuid(),
  company_id uuid references public.companies(id) on delete set null,
  post_id uuid references public.posts(id) on delete set null,
  user_id uuid references public.profiles(id) on delete set null,
  provider text not null,
  model text not null,
  prompt_hash text,
  request jsonb not null default '{}'::jsonb,
  response jsonb not null default '{}'::jsonb,
  input_tokens integer,
  output_tokens integer,
  latency_ms integer,
  created_at timestamptz not null default now()
);

create table public.prompt_templates (
  id uuid primary key default gen_random_uuid(),
  module_name text not null,
  version integer not null,
  provider text not null,
  model text not null,
  system_prompt text not null,
  user_prompt_template text not null,
  schema_json jsonb not null default '{}'::jsonb,
  active boolean not null default false,
  created_at timestamptz not null default now(),
  unique (module_name, version)
);

create table public.audit_logs (
  id uuid primary key default gen_random_uuid(),
  company_id uuid references public.companies(id) on delete set null,
  actor_id uuid references public.profiles(id) on delete set null,
  action text not null,
  resource_type text not null,
  resource_id uuid,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index companies_created_by_idx on public.companies(created_by);
create index memberships_user_company_idx on public.memberships(user_id, company_id);
create index posts_company_status_created_idx on public.posts(company_id, status, created_at desc);
create index generated_content_post_platform_idx on public.generated_content(post_id, platform);
create index scheduled_posts_status_run_at_idx on public.scheduled_posts(status, run_at_utc);
create index scheduled_posts_company_run_at_idx on public.scheduled_posts(company_id, run_at_utc);
create index analytics_events_company_platform_captured_idx on public.analytics_events(company_id, platform, captured_at desc);
create index media_assets_company_created_idx on public.media_assets(company_id, created_at desc);
create index ai_generations_company_created_idx on public.ai_generations(company_id, created_at desc);
create index audit_logs_company_created_idx on public.audit_logs(company_id, created_at desc);

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger profiles_set_updated_at before update on public.profiles for each row execute function public.set_updated_at();
create trigger companies_set_updated_at before update on public.companies for each row execute function public.set_updated_at();
create trigger brand_profiles_set_updated_at before update on public.brand_profiles for each row execute function public.set_updated_at();
create trigger campaigns_set_updated_at before update on public.campaigns for each row execute function public.set_updated_at();
create trigger posts_set_updated_at before update on public.posts for each row execute function public.set_updated_at();
create trigger social_accounts_set_updated_at before update on public.social_accounts for each row execute function public.set_updated_at();

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'media-assets',
  'media-assets',
  false,
  52428800,
  array['image/jpeg', 'image/png', 'image/webp', 'image/gif', 'video/mp4']
)
on conflict (id) do update set
  public = excluded.public,
  file_size_limit = excluded.file_size_limit,
  allowed_mime_types = excluded.allowed_mime_types;

alter table public.profiles enable row level security;
alter table public.companies enable row level security;
alter table public.memberships enable row level security;
alter table public.brand_profiles enable row level security;
alter table public.campaigns enable row level security;
alter table public.posts enable row level security;
alter table public.generated_content enable row level security;
alter table public.scheduled_posts enable row level security;
alter table public.social_accounts enable row level security;
alter table public.media_assets enable row level security;
alter table public.analytics_events enable row level security;
alter table public.ai_generations enable row level security;
alter table public.prompt_templates enable row level security;
alter table public.audit_logs enable row level security;

create policy profiles_select_own on public.profiles for select to authenticated using ((select auth.uid()) = id);
create policy profiles_insert_own on public.profiles for insert to authenticated with check ((select auth.uid()) = id);
create policy profiles_update_own on public.profiles for update to authenticated using ((select auth.uid()) = id) with check ((select auth.uid()) = id);

create policy memberships_select_own on public.memberships for select to authenticated using (user_id = (select auth.uid()));
create policy memberships_insert_created_company on public.memberships for insert to authenticated with check (user_id = (select auth.uid()) or exists (select 1 from public.companies c where c.id = company_id and c.created_by = (select auth.uid())));

create policy companies_select_member on public.companies for select to authenticated using (exists (select 1 from public.memberships m where m.company_id = id and m.user_id = (select auth.uid())));
create policy companies_insert_own on public.companies for insert to authenticated with check (created_by = (select auth.uid()));
create policy companies_update_admin on public.companies for update to authenticated using (exists (select 1 from public.memberships m where m.company_id = id and m.user_id = (select auth.uid()) and m.role in ('agency_admin', 'brand_manager'))) with check (exists (select 1 from public.memberships m where m.company_id = id and m.user_id = (select auth.uid()) and m.role in ('agency_admin', 'brand_manager')));

create policy brand_profiles_member_all on public.brand_profiles for all to authenticated using (exists (select 1 from public.memberships m where m.company_id = brand_profiles.company_id and m.user_id = (select auth.uid()))) with check (exists (select 1 from public.memberships m where m.company_id = brand_profiles.company_id and m.user_id = (select auth.uid())));
create policy campaigns_member_all on public.campaigns for all to authenticated using (exists (select 1 from public.memberships m where m.company_id = campaigns.company_id and m.user_id = (select auth.uid()))) with check (exists (select 1 from public.memberships m where m.company_id = campaigns.company_id and m.user_id = (select auth.uid())));
create policy posts_member_all on public.posts for all to authenticated using (exists (select 1 from public.memberships m where m.company_id = posts.company_id and m.user_id = (select auth.uid()))) with check (exists (select 1 from public.memberships m where m.company_id = posts.company_id and m.user_id = (select auth.uid())));
create policy generated_content_member_all on public.generated_content for all to authenticated using (exists (select 1 from public.memberships m where m.company_id = generated_content.company_id and m.user_id = (select auth.uid()))) with check (exists (select 1 from public.memberships m where m.company_id = generated_content.company_id and m.user_id = (select auth.uid())));
create policy scheduled_posts_member_all on public.scheduled_posts for all to authenticated using (exists (select 1 from public.memberships m where m.company_id = scheduled_posts.company_id and m.user_id = (select auth.uid()))) with check (exists (select 1 from public.memberships m where m.company_id = scheduled_posts.company_id and m.user_id = (select auth.uid())));
create policy social_accounts_admin_all on public.social_accounts for all to authenticated using (exists (select 1 from public.memberships m where m.company_id = social_accounts.company_id and m.user_id = (select auth.uid()) and m.role in ('agency_admin', 'brand_manager'))) with check (exists (select 1 from public.memberships m where m.company_id = social_accounts.company_id and m.user_id = (select auth.uid()) and m.role in ('agency_admin', 'brand_manager')));
create policy media_assets_member_all on public.media_assets for all to authenticated using (exists (select 1 from public.memberships m where m.company_id = media_assets.company_id and m.user_id = (select auth.uid()))) with check (exists (select 1 from public.memberships m where m.company_id = media_assets.company_id and m.user_id = (select auth.uid())));
create policy analytics_events_member_all on public.analytics_events for all to authenticated using (exists (select 1 from public.memberships m where m.company_id = analytics_events.company_id and m.user_id = (select auth.uid()))) with check (exists (select 1 from public.memberships m where m.company_id = analytics_events.company_id and m.user_id = (select auth.uid())));
create policy ai_generations_member_select on public.ai_generations for select to authenticated using (company_id is null or exists (select 1 from public.memberships m where m.company_id = ai_generations.company_id and m.user_id = (select auth.uid())));
create policy ai_generations_insert_own on public.ai_generations for insert to authenticated with check (user_id = (select auth.uid()) and (company_id is null or exists (select 1 from public.memberships m where m.company_id = ai_generations.company_id and m.user_id = (select auth.uid()))));
create policy prompt_templates_authenticated_read on public.prompt_templates for select to authenticated using (true);
create policy audit_logs_member_select on public.audit_logs for select to authenticated using (company_id is null or exists (select 1 from public.memberships m where m.company_id = audit_logs.company_id and m.user_id = (select auth.uid())));

create policy storage_media_member_read on storage.objects for select to authenticated using (bucket_id = 'media-assets' and exists (select 1 from public.media_assets ma join public.memberships m on m.company_id = ma.company_id where ma.storage_bucket = bucket_id and ma.storage_path = name and m.user_id = (select auth.uid())));
create policy storage_media_member_insert on storage.objects for insert to authenticated with check (bucket_id = 'media-assets' and exists (select 1 from public.memberships m where m.company_id = case when (storage.foldername(name))[1] ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$' then ((storage.foldername(name))[1])::uuid else null end and m.user_id = (select auth.uid())));
create policy storage_media_member_update on storage.objects for update to authenticated using (bucket_id = 'media-assets' and exists (select 1 from public.memberships m where m.company_id = case when (storage.foldername(name))[1] ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$' then ((storage.foldername(name))[1])::uuid else null end and m.user_id = (select auth.uid()))) with check (bucket_id = 'media-assets' and exists (select 1 from public.memberships m where m.company_id = case when (storage.foldername(name))[1] ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$' then ((storage.foldername(name))[1])::uuid else null end and m.user_id = (select auth.uid())));
create policy storage_media_member_delete on storage.objects for delete to authenticated using (bucket_id = 'media-assets' and exists (select 1 from public.memberships m where m.company_id = case when (storage.foldername(name))[1] ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$' then ((storage.foldername(name))[1])::uuid else null end and m.user_id = (select auth.uid())));

grant usage on schema public to authenticated, service_role;
grant select, insert, update, delete on all tables in schema public to authenticated;
grant usage, select on all sequences in schema public to authenticated;
grant all privileges on all tables in schema public to service_role;
grant all privileges on all sequences in schema public to service_role;
