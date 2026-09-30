-- Run in a disposable Supabase project as postgres AFTER the migration.
-- Tests are transactional and leave no rows/users behind on success.
begin;
insert into auth.users (id, email) values
  ('a1111111-1111-4111-8111-111111111111','mast-test-a@example.invalid'),
  ('b2222222-2222-4222-8222-222222222222','mast-test-b@example.invalid');
set local role authenticated;
select set_config('request.jwt.claims','{"sub":"a1111111-1111-4111-8111-111111111111","role":"authenticated"}',true);
insert into public.assessments (id,user_id,name,method,engine_version,draft,result) values
  ('c3333333-3333-4333-8333-333333333333','a1111111-1111-4111-8111-111111111111','A test','thickness','test','{}','{}');
do $$ begin
  if (select count(*) from public.assessments) <> 1 then raise exception 'Owner cannot read own row'; end if;
  begin
    insert into public.assessments (user_id,name,method,engine_version,draft,result) values
      ('b2222222-2222-4222-8222-222222222222','forged owner','thickness','test','{}','{}');
    raise exception 'Cross-owner insert was allowed';
  exception when insufficient_privilege then null; end;
  begin
    update public.assessments set name='changed';
    raise exception 'Snapshot update was allowed';
  exception when insufficient_privilege then null; end;
end $$;
select set_config('request.jwt.claims','{"sub":"b2222222-2222-4222-8222-222222222222","role":"authenticated"}',true);
do $$ declare deleted integer; begin
  if exists(select 1 from public.assessments) then raise exception 'Cross-owner select was allowed'; end if;
  delete from public.assessments where id='c3333333-3333-4333-8333-333333333333';
  get diagnostics deleted = row_count;
  if deleted <> 0 then raise exception 'Cross-owner delete was allowed'; end if;
end $$;
select set_config('request.jwt.claims','{"sub":"a1111111-1111-4111-8111-111111111111","role":"authenticated"}',true);
do $$ begin
  if not exists(select 1 from public.assessments where id='c3333333-3333-4333-8333-333333333333') then raise exception 'Owner row disappeared'; end if;
end $$;
delete from public.assessments where id='c3333333-3333-4333-8333-333333333333';
set local role anon;
select set_config('request.jwt.claims','{"role":"anon"}',true);
do $$ begin
  begin
    perform 1 from public.assessments;
    raise exception 'Anonymous select was allowed';
  exception when insufficient_privilege then null; end;
end $$;
rollback;
