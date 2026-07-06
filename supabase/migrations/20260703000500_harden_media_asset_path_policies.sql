drop policy if exists media_assets_member_all on public.media_assets;
drop policy if exists media_assets_member_select on public.media_assets;
drop policy if exists media_assets_member_insert on public.media_assets;
drop policy if exists media_assets_member_update on public.media_assets;
drop policy if exists media_assets_member_delete on public.media_assets;

drop policy if exists storage_media_member_read on storage.objects;
drop policy if exists storage_media_member_insert on storage.objects;
drop policy if exists storage_media_member_update on storage.objects;
drop policy if exists storage_media_member_delete on storage.objects;

create policy media_assets_member_select
on public.media_assets
for select
to authenticated
using (
  exists (
    select 1
    from public.memberships m
    where m.company_id = media_assets.company_id
      and m.user_id = (select auth.uid())
  )
);

create policy media_assets_member_insert
on public.media_assets
for insert
to authenticated
with check (
  storage_bucket = 'media-assets'
  and storage_path like company_id::text || '/%'
  and exists (
    select 1
    from public.memberships m
    where m.company_id = media_assets.company_id
      and m.user_id = (select auth.uid())
  )
);

create policy media_assets_member_update
on public.media_assets
for update
to authenticated
using (
  exists (
    select 1
    from public.memberships m
    where m.company_id = media_assets.company_id
      and m.user_id = (select auth.uid())
  )
)
with check (
  storage_bucket = 'media-assets'
  and storage_path like company_id::text || '/%'
  and exists (
    select 1
    from public.memberships m
    where m.company_id = media_assets.company_id
      and m.user_id = (select auth.uid())
  )
);

create policy media_assets_member_delete
on public.media_assets
for delete
to authenticated
using (
  exists (
    select 1
    from public.memberships m
    where m.company_id = media_assets.company_id
      and m.user_id = (select auth.uid())
  )
);

create policy storage_media_member_read
on storage.objects
for select
to authenticated
using (
  bucket_id = 'media-assets'
  and exists (
    select 1
    from public.memberships m
    where m.company_id = case
        when (storage.foldername(name))[1] ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
          then ((storage.foldername(name))[1])::uuid
        else null
      end
      and m.user_id = (select auth.uid())
  )
);

create policy storage_media_member_insert
on storage.objects
for insert
to authenticated
with check (
  bucket_id = 'media-assets'
  and exists (
    select 1
    from public.memberships m
    where m.company_id = case
        when (storage.foldername(name))[1] ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
          then ((storage.foldername(name))[1])::uuid
        else null
      end
      and m.user_id = (select auth.uid())
  )
);

create policy storage_media_member_update
on storage.objects
for update
to authenticated
using (
  bucket_id = 'media-assets'
  and exists (
    select 1
    from public.memberships m
    where m.company_id = case
        when (storage.foldername(name))[1] ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
          then ((storage.foldername(name))[1])::uuid
        else null
      end
      and m.user_id = (select auth.uid())
  )
)
with check (
  bucket_id = 'media-assets'
  and exists (
    select 1
    from public.memberships m
    where m.company_id = case
        when (storage.foldername(name))[1] ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
          then ((storage.foldername(name))[1])::uuid
        else null
      end
      and m.user_id = (select auth.uid())
  )
);

create policy storage_media_member_delete
on storage.objects
for delete
to authenticated
using (
  bucket_id = 'media-assets'
  and exists (
    select 1
    from public.memberships m
    where m.company_id = case
        when (storage.foldername(name))[1] ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
          then ((storage.foldername(name))[1])::uuid
        else null
      end
      and m.user_id = (select auth.uid())
  )
);
