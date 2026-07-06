drop policy if exists storage_media_member_read on storage.objects;
drop policy if exists storage_media_member_insert on storage.objects;
drop policy if exists storage_media_member_update on storage.objects;
drop policy if exists storage_media_member_delete on storage.objects;

-- Media object names must start with the company UUID, for example:
-- <company_id>/uploads/<file-name>.png
create policy storage_media_member_read
on storage.objects
for select
to authenticated
using (
  bucket_id = 'media-assets'
  and exists (
    select 1
    from public.media_assets ma
    join public.memberships m on m.company_id = ma.company_id
    where ma.storage_bucket = bucket_id
      and ma.storage_path = name
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
    where m.company_id = case when (storage.foldername(name))[1] ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$' then ((storage.foldername(name))[1])::uuid else null end
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
    where m.company_id = case when (storage.foldername(name))[1] ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$' then ((storage.foldername(name))[1])::uuid else null end
      and m.user_id = (select auth.uid())
  )
)
with check (
  bucket_id = 'media-assets'
  and exists (
    select 1
    from public.memberships m
    where m.company_id = case when (storage.foldername(name))[1] ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$' then ((storage.foldername(name))[1])::uuid else null end
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
    where m.company_id = case when (storage.foldername(name))[1] ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$' then ((storage.foldername(name))[1])::uuid else null end
      and m.user_id = (select auth.uid())
  )
);
