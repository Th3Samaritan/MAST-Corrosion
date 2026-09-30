-- Apply once using Supabase SQL Editor or `supabase db push`.
begin;
create table public.assessments (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  created_at timestamptz not null default clock_timestamp(),
  name text not null check (length(name) between 1 and 1000),
  method text not null check (method in ('thickness','current','lpr','coupon')),
  engine_version text not null,
  status text not null default 'unreviewed' check (status = 'unreviewed'),
  draft jsonb not null check (jsonb_typeof(draft) = 'object' and octet_length(draft::text) <= 262144),
  result jsonb not null check (jsonb_typeof(result) = 'object' and octet_length(result::text) <= 1048576)
);
create index assessments_user_created on public.assessments (user_id, created_at desc, id desc);
alter table public.assessments enable row level security;
revoke all on public.assessments from anon, authenticated;
grant select, insert, delete on public.assessments to authenticated;
create policy "Read own assessments" on public.assessments for select to authenticated
  using ((select auth.uid()) = user_id);
create policy "Insert own assessments" on public.assessments for insert to authenticated
  with check ((select auth.uid()) = user_id);
create policy "Delete own assessments" on public.assessments for delete to authenticated
  using ((select auth.uid()) = user_id);
-- No update privilege/policy: create another snapshot to record a changed calculation.
comment on table public.assessments is 'User-owned, unreviewed snapshots. UI recalculates inputs on load; stored results are not certified.';
commit;
