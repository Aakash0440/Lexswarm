-- supabase/schema.sql
-- Run this in Supabase SQL editor (Dashboard → SQL Editor → New Query)

-- Cases table — stores every case submission and its output
create table public.cases (
    id              uuid default gen_random_uuid() primary key,
    user_id         uuid references auth.users(id) on delete cascade,
    case_ref        text not null,                    -- e.g. "FA38AF99"
    case_type       text not null,                    -- "family", "labor", etc.
    urgency         text not null,                    -- "CRITICAL", "HIGH", etc.
    country         text not null,                    -- "PK", "BD", etc.
    language        text not null,                    -- "ur", "en", etc.
    description     text not null,                    -- raw user input
    legal_rights    jsonb default '[]',               -- statutes found
    action_plan     jsonb default '[]',               -- steps
    documents       jsonb default '[]',               -- generated docs
    simulation      jsonb default '{}',               -- MiroFish result
    win_probability integer default 0,
    lawyer_alerted  boolean default false,
    flags           jsonb default '{}',               -- is_stateless, involves_minor, etc.
    created_at      timestamptz default now()
);

-- Enable Row Level Security — users can only see their own cases
alter table public.cases enable row level security;

create policy "Users see own cases"
    on public.cases for select
    using (auth.uid() = user_id);

create policy "Users insert own cases"
    on public.cases for insert
    with check (auth.uid() = user_id);

-- Index for fast user case history lookup
create index cases_user_id_idx on public.cases(user_id);
create index cases_created_at_idx on public.cases(created_at desc);
