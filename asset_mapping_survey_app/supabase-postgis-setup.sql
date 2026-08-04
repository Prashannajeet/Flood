-- Asset Mapping central repository for Supabase PostgreSQL + PostGIS
-- Run this in the Supabase SQL editor after creating a new project.

create extension if not exists postgis;

create table if not exists public.field_records (
  id text primary key,
  project_name text not null,
  record_type text not null check (record_type in ('Dam', 'Road', 'River', 'Canal', 'Control')),
  asset_name text,
  condition text,
  latitude double precision,
  longitude double precision,
  control_type text,
  control_id text,
  surveyor_name text,
  photo_count integer not null default 0,
  payload jsonb not null default '{}'::jsonb,
  geom geometry(Point, 4326) generated always as (
    case
      when latitude is null or longitude is null then null
      else st_setsrid(st_makepoint(longitude, latitude), 4326)
    end
  ) stored,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists field_records_project_idx
  on public.field_records (project_name);

create index if not exists field_records_type_idx
  on public.field_records (record_type);

create index if not exists field_records_control_idx
  on public.field_records (control_type, control_id);

create index if not exists field_records_geom_idx
  on public.field_records using gist (geom);

-- Optional dashboard editing metadata. The web dashboard also stores these
-- inside payload so existing deployments keep working before this SQL is rerun.
alter table public.field_records
  add column if not exists editor_user_id text,
  add column if not exists allowed_editor_ids text[] not null default '{}'::text[],
  add column if not exists last_edited_by text,
  add column if not exists last_edited_at timestamptz;

create index if not exists field_records_editor_idx
  on public.field_records (editor_user_id);

create or replace function public.set_field_records_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists field_records_set_updated_at on public.field_records;

create trigger field_records_set_updated_at
before update on public.field_records
for each row
execute function public.set_field_records_updated_at();

alter table public.field_records enable row level security;

grant usage on schema public to anon, authenticated;
grant select, insert, update on public.field_records to anon, authenticated;

-- Demo policies for the current browser-based prototype.
-- For production, replace these with Supabase Auth + RLS policies that enforce
-- editor_user_id/allowed_editor_ids using auth.uid() or user profile mappings.
drop policy if exists "Prototype read field records" on public.field_records;
create policy "Prototype read field records"
on public.field_records for select
using (true);

drop policy if exists "Prototype insert field records" on public.field_records;
create policy "Prototype insert field records"
on public.field_records for insert
with check (true);

drop policy if exists "Prototype update field records" on public.field_records;
create policy "Prototype update field records"
on public.field_records for update
using (true)
with check (true);

insert into storage.buckets (id, name, public)
values ('asset-photos', 'asset-photos', true)
on conflict (id) do update set public = excluded.public;

drop policy if exists "Prototype read asset photos" on storage.objects;
create policy "Prototype read asset photos"
on storage.objects for select
using (bucket_id = 'asset-photos');

drop policy if exists "Prototype upload asset photos" on storage.objects;
create policy "Prototype upload asset photos"
on storage.objects for insert
with check (bucket_id = 'asset-photos');

drop policy if exists "Prototype update asset photos" on storage.objects;
create policy "Prototype update asset photos"
on storage.objects for update
using (bucket_id = 'asset-photos')
with check (bucket_id = 'asset-photos');

-- Useful map query example:
-- select id, project_name, record_type, control_type, control_id, st_asgeojson(geom) as geojson
-- from public.field_records
-- where geom is not null;

-- Force Supabase/PostgREST to reload the new table and policies immediately.
select pg_notify('pgrst', 'reload schema');
