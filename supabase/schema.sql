-- Inscriptions aux alertes AR.
-- À coller une fois dans Supabase : SQL Editor → New query → Run.
--
-- Sécurité :
--   * le public (clé « publishable ») peut seulement AJOUTER une inscription, avec un nombre
--     limité de colonnes ; il ne peut ni lire, ni modifier, ni supprimer la liste ;
--   * confirmation et désinscription passent par deux fonctions qui n'agissent que sur la ligne
--     dont on connaît le jeton secret (envoyé uniquement par e-mail) ;
--   * le script d'alerte (GitHub Actions) utilise la clé secrète, qui contourne ces règles.

create table if not exists public.subscriptions (
  id              uuid primary key default gen_random_uuid(),
  token           uuid not null unique default gen_random_uuid(),
  email           text not null
                  check (length(email) <= 254 and email ~* '^[^@\s]+@[^@\s]+\.[^@\s]{2,}$'),
  station         text check (length(station) <= 80),
  lat             double precision not null check (lat between -90 and -40),
  lon             double precision not null check (lon between -180 and 180),
  algorithms      text[] not null
                  check (cardinality(algorithms) between 1 and 3
                         and algorithms <@ array['wille_vivt', 'wille_iwv', 'dark']),
  lang            text not null default 'fr' check (lang in ('fr', 'en')),
  created_at      timestamptz not null default now(),
  confirm_sent_at timestamptz,
  confirmed_at    timestamptz,
  unsubscribed_at timestamptz,
  alert_state     jsonb not null default '{}'::jsonb,
  remind_24h      boolean not null default false
);
-- projets créés avant l'option de rappel
alter table public.subscriptions add column if not exists remind_24h boolean not null default false;

-- une seule inscription active par adresse et par lieu
create unique index if not exists subscriptions_unique_active
  on public.subscriptions (lower(email), round(lat::numeric, 2), round(lon::numeric, 2))
  where unsubscribed_at is null;

-- garde-fous contre les inscriptions en masse
create or replace function public.subscriptions_limits() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  if (select count(*) from subscriptions
      where lower(email) = lower(new.email) and unsubscribed_at is null) >= 10 then
    raise exception 'too many subscriptions for this address';
  end if;
  if (select count(*) from subscriptions where created_at > now() - interval '1 hour') >= 100 then
    raise exception 'too many subscriptions, try later';
  end if;
  new.email := lower(trim(new.email));
  return new;
end $$;

drop trigger if exists subscriptions_limits on public.subscriptions;
create trigger subscriptions_limits before insert on public.subscriptions
  for each row execute function public.subscriptions_limits();

-- droits : le public n'insère que ces colonnes, sans rien pouvoir relire
alter table public.subscriptions enable row level security;
revoke all on public.subscriptions from anon, authenticated;
grant insert (email, station, lat, lon, algorithms, lang, remind_24h) on public.subscriptions to anon;
-- clé secrète (script d'alerte) : droits explicites, même si l'option « Grant API access to
-- new tables automatically » est désactivée dans le projet
grant select, insert, update, delete on public.subscriptions to service_role;

drop policy if exists "public can subscribe" on public.subscriptions;
create policy "public can subscribe" on public.subscriptions
  for insert to anon
  with check (confirmed_at is null and unsubscribed_at is null and confirm_sent_at is null);

-- lien « confirmer » de l'e-mail
create or replace function public.confirm_subscription(p_token uuid) returns text
language sql security definer set search_path = public as $$
  update subscriptions
     set confirmed_at = coalesce(confirmed_at, now())
   where token = p_token and unsubscribed_at is null
  returning coalesce(station, round(lat::numeric, 2) || ', ' || round(lon::numeric, 2));
$$;

-- lien « se désinscrire » de l'e-mail
create or replace function public.unsubscribe(p_token uuid) returns text
language sql security definer set search_path = public as $$
  update subscriptions
     set unsubscribed_at = coalesce(unsubscribed_at, now())
   where token = p_token
  returning coalesce(station, round(lat::numeric, 2) || ', ' || round(lon::numeric, 2));
$$;

revoke execute on function public.confirm_subscription(uuid), public.unsubscribe(uuid),
  public.subscriptions_limits() from public;
grant execute on function public.confirm_subscription(uuid), public.unsubscribe(uuid) to anon;
