-- À exécuter dans Supabase > SQL Editor > New query.
-- Version simple pour une partie privée entre deux personnes.
-- Important : cette version utilise la clé secrète/service_role côté serveur Streamlit.
-- Ne mets JAMAIS cette clé dans le code public ni dans un navigateur.

create extension if not exists pgcrypto;

create table if not exists public.games (
  id uuid primary key default gen_random_uuid(),
  code text unique not null,
  status text not null default 'picking' check (status in ('picking','live','finished')),
  created_at timestamptz not null default now()
);

create table if not exists public.players (
  id uuid primary key default gen_random_uuid(),
  game_id uuid not null references public.games(id) on delete cascade,
  name text not null,
  slot integer not null check (slot in (1,2)),
  access_token text not null,
  locked boolean not null default false,
  created_at timestamptz not null default now(),
  unique(game_id, slot),
  unique(game_id, name)
);

create table if not exists public.picks (
  id uuid primary key default gen_random_uuid(),
  game_id uuid not null references public.games(id) on delete cascade,
  player_id uuid not null references public.players(id) on delete cascade,
  player_name text not null,
  predicted_rank integer not null check (predicted_rank between 1 and 10),
  unique(player_id, predicted_rank)
);

create table if not exists public.results (
  id uuid primary key default gen_random_uuid(),
  game_id uuid not null references public.games(id) on delete cascade,
  player_name text not null,
  rank integer not null check (rank between 1 and 10),
  created_at timestamptz not null default now(),
  unique(game_id, rank),
  unique(game_id, player_name)
);

alter table public.games enable row level security;
alter table public.players enable row level security;
alter table public.picks enable row level security;
alter table public.results enable row level security;

-- No public policies are created. The Streamlit server uses the service_role key.
