drop policy if exists companies_select_member on public.companies;
drop policy if exists companies_update_admin on public.companies;

create policy companies_select_member_or_creator
on public.companies
for select
to authenticated
using (
  created_by = (select auth.uid())
  or exists (
    select 1
    from public.memberships m
    where m.company_id = id
      and m.user_id = (select auth.uid())
  )
);

create policy companies_update_admin_or_creator
on public.companies
for update
to authenticated
using (
  created_by = (select auth.uid())
  or exists (
    select 1
    from public.memberships m
    where m.company_id = id
      and m.user_id = (select auth.uid())
      and m.role in ('agency_admin', 'brand_manager')
  )
)
with check (
  created_by = (select auth.uid())
  or exists (
    select 1
    from public.memberships m
    where m.company_id = id
      and m.user_id = (select auth.uid())
      and m.role in ('agency_admin', 'brand_manager')
  )
);
