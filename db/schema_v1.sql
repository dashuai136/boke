-- Schema v1 (revised) for Begonia new-species database
-- Goals:
-- 1) enforce data quality with explicit enums/checks
-- 2) keep search/query fast at MVP scale
-- 3) support moderation + digest delivery workflows

create extension if not exists pg_trgm;
create extension if not exists unaccent;
create extension if not exists pgcrypto;

-- =========================
-- Enum types
-- =========================
do $$ begin
  create type species_status as enum ('candidate','provisional','verified','archived');
exception when duplicate_object then null; end $$;

do $$ begin
  create type media_display_policy as enum ('hosted','proxied','linked_only','card_only');
exception when duplicate_object then null; end $$;

do $$ begin
  create type media_permission_status as enum ('licensed','compatible','unclear','denied');
exception when duplicate_object then null; end $$;

do $$ begin
  create type geometry_visibility as enum ('exact','blurred','region_only');
exception when duplicate_object then null; end $$;

do $$ begin
  create type submission_status as enum ('pending','reviewed','accepted','rejected');
exception when duplicate_object then null; end $$;

do $$ begin
  create type subscription_channel as enum ('email','telegram','wecom','webpush');
exception when duplicate_object then null; end $$;

do $$ begin
  create type subscription_status as enum ('active','paused','unverified');
exception when duplicate_object then null; end $$;

do $$ begin
  create type delivery_status as enum ('queued','sent','failed','retrying');
exception when duplicate_object then null; end $$;

-- =========================
-- Utility trigger
-- =========================
create or replace function set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

-- =========================
-- Core entities
-- =========================
create table if not exists species (
  id uuid primary key default gen_random_uuid(),
  slug varchar(160) not null unique,
  scientific_name varchar(255) not null,
  authorship varchar(255),
  rank varchar(32) not null default 'species',
  section_name varchar(128),
  common_name_zh varchar(255),
  taxon_scope varchar(32) not null default 'new_species',
  status species_status not null default 'candidate',
  doi varchar(128),
  journal_title varchar(255),
  published_on date,
  first_seen_at timestamptz,
  entered_at timestamptz,
  verified_at timestamptz,
  source_confidence numeric(5,2) check (source_confidence is null or (source_confidence >= 0 and source_confidence <= 100)),
  abstract_text text,
  diagnosis_text text,
  habitat_text text,
  conservation_status varchar(64),
  notes_md text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  search_tsv tsvector generated always as (
    setweight(to_tsvector('simple', unaccent(coalesce(scientific_name,''))), 'A') ||
    setweight(to_tsvector('simple', unaccent(coalesce(authorship,''))), 'B') ||
    setweight(to_tsvector('simple', unaccent(coalesce(section_name,''))), 'B') ||
    setweight(to_tsvector('simple', unaccent(coalesce(abstract_text,''))), 'C')
  ) stored
);

create unique index if not exists ux_species_doi_nonnull on species(doi) where doi is not null;
create index if not exists ix_species_status on species(status);
create index if not exists ix_species_published_on on species(published_on desc);
create index if not exists ix_species_entered_at on species(entered_at desc);
create index if not exists ix_species_scientific_name_trgm on species using gin (scientific_name gin_trgm_ops);
create index if not exists ix_species_search_tsv on species using gin (search_tsv);

create trigger trg_species_set_updated_at
before update on species
for each row execute function set_updated_at();

create table if not exists external_refs (
  id uuid primary key default gen_random_uuid(),
  species_id uuid not null references species(id) on delete cascade,
  provider varchar(32) not null,
  provider_id varchar(255),
  ref_type varchar(32) not null,
  url text not null,
  is_primary boolean not null default false,
  fetched_at timestamptz,
  payload_json jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint ck_external_refs_provider_id_required check (
    (provider in ('DOI') and provider_id is not null) or provider <> 'DOI' or provider_id is not null
  )
);

create unique index if not exists ux_external_refs_provider_unique
  on external_refs(species_id, provider, provider_id, ref_type)
  where provider_id is not null;
create index if not exists ix_external_refs_species_id on external_refs(species_id);
create index if not exists ix_external_refs_provider on external_refs(provider);

create trigger trg_external_refs_set_updated_at
before update on external_refs
for each row execute function set_updated_at();

create table if not exists source_documents (
  id uuid primary key default gen_random_uuid(),
  species_id uuid not null references species(id) on delete cascade,
  source_type varchar(32) not null,
  title text not null,
  source_name varchar(255) not null,
  url text,
  pdf_url text,
  doi varchar(128),
  publication_date date,
  license_label varchar(128),
  rights_note text,
  checksum varchar(128),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create unique index if not exists ux_source_documents_checksum_nonnull
  on source_documents(checksum) where checksum is not null;
create index if not exists ix_source_documents_species_id on source_documents(species_id);
create index if not exists ix_source_documents_doi on source_documents(doi);
create index if not exists ix_source_documents_publication_date on source_documents(publication_date desc);

create trigger trg_source_documents_set_updated_at
before update on source_documents
for each row execute function set_updated_at();

create table if not exists media_assets (
  id uuid primary key default gen_random_uuid(),
  species_id uuid not null references species(id) on delete cascade,
  media_role varchar(32) not null,
  source_kind varchar(32) not null,
  display_policy media_display_policy not null,
  original_url text,
  thumb_url text,
  page_ref varchar(64),
  caption text,
  alt_text text,
  copyright_owner varchar(255),
  license_label varchar(128),
  permission_status media_permission_status not null default 'unclear',
  derivative_allowed boolean,
  hotlink_allowed boolean,
  width integer,
  height integer,
  verified_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint ck_media_dimensions_positive check (
    (width is null or width > 0) and (height is null or height > 0)
  )
);

create index if not exists ix_media_assets_species_id on media_assets(species_id);
create index if not exists ix_media_assets_display_policy on media_assets(display_policy);
create index if not exists ix_media_assets_permission_status on media_assets(permission_status);

create trigger trg_media_assets_set_updated_at
before update on media_assets
for each row execute function set_updated_at();

create table if not exists occurrences (
  id uuid primary key default gen_random_uuid(),
  species_id uuid not null references species(id) on delete cascade,
  country varchar(128),
  admin1 varchar(128),
  locality text,
  latitude decimal(9,6),
  longitude decimal(9,6),
  coordinate_precision_m integer,
  is_type_locality boolean,
  source_url text,
  geometry_visibility geometry_visibility not null default 'blurred',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint ck_occurrence_latlon_pair check (
    (latitude is null and longitude is null) or (latitude is not null and longitude is not null)
  ),
  constraint ck_occurrence_lat_range check (latitude is null or (latitude >= -90 and latitude <= 90)),
  constraint ck_occurrence_lon_range check (longitude is null or (longitude >= -180 and longitude <= 180)),
  constraint ck_occurrence_precision check (coordinate_precision_m is null or coordinate_precision_m > 0)
);

create index if not exists ix_occurrences_species_id on occurrences(species_id);
create index if not exists ix_occurrences_country on occurrences(country);

create trigger trg_occurrences_set_updated_at
before update on occurrences
for each row execute function set_updated_at();

create table if not exists submissions (
  id uuid primary key default gen_random_uuid(),
  submitter_name varchar(255),
  submitter_email varchar(255),
  submitted_name varchar(255) not null,
  evidence_urls jsonb,
  message text,
  status submission_status not null default 'pending',
  assigned_to uuid,
  review_notes text,
  created_at timestamptz not null default now(),
  reviewed_at timestamptz,
  updated_at timestamptz not null default now(),
  constraint ck_submissions_reviewed_time check (
    (status in ('accepted','rejected','reviewed') and reviewed_at is not null)
    or (status = 'pending')
  )
);

create index if not exists ix_submissions_status on submissions(status);
create index if not exists ix_submissions_created_at on submissions(created_at desc);

create trigger trg_submissions_set_updated_at
before update on submissions
for each row execute function set_updated_at();

create table if not exists subscriptions (
  id uuid primary key default gen_random_uuid(),
  channel subscription_channel not null,
  endpoint text not null,
  timezone varchar(64) not null,
  preferred_hour smallint not null check (preferred_hour between 0 and 23),
  status subscription_status not null default 'unverified',
  last_sent_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (channel, endpoint)
);

create index if not exists ix_subscriptions_channel on subscriptions(channel);
create index if not exists ix_subscriptions_status on subscriptions(status);
create index if not exists ix_subscriptions_timezone_hour on subscriptions(timezone, preferred_hour);

create trigger trg_subscriptions_set_updated_at
before update on subscriptions
for each row execute function set_updated_at();

create table if not exists digests (
  id uuid primary key default gen_random_uuid(),
  business_date date not null,
  generated_at timestamptz not null default now(),
  item_count integer not null check (item_count >= 0),
  payload_json jsonb not null,
  created_at timestamptz not null default now(),
  unique (business_date)
);

create table if not exists delivery_logs (
  id uuid primary key default gen_random_uuid(),
  digest_id uuid references digests(id) on delete set null,
  subscription_id uuid references subscriptions(id) on delete set null,
  channel subscription_channel not null,
  endpoint text,
  status delivery_status not null default 'queued',
  error_message text,
  attempt_count integer not null default 0 check (attempt_count >= 0),
  sent_at timestamptz,
  created_at timestamptz not null default now()
);

create index if not exists ix_delivery_logs_status on delivery_logs(status);
create index if not exists ix_delivery_logs_digest_id on delivery_logs(digest_id);
create index if not exists ix_delivery_logs_subscription_id on delivery_logs(subscription_id);
create index if not exists ix_delivery_logs_created_at on delivery_logs(created_at desc);
