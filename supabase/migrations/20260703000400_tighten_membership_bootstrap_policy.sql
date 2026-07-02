drop policy if exists memberships_insert_created_company on public.memberships;

create policy memberships_insert_creator_or_admin
on public.memberships
for insert
to authenticated
with check (
  (
    user_id = (select auth.uid())
    and exists (
      select 1
      from public.companies c
      where c.id = company_id
        and c.created_by = (select auth.uid())
    )
  )
  or exists (
    select 1
    from public.memberships m
    where m.company_id = memberships.company_id
      and m.user_id = (select auth.uid())
      and m.role in ('agency_admin', 'brand_manager')
  )
);
