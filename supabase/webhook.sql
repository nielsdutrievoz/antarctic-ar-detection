-- Confirmation immédiate : à chaque nouvelle inscription, Supabase demande à GitHub de lancer
-- la tâche « Confirmations d'inscription » (.github/workflows/confirmations.yml).
--
-- Prérequis : le jeton GitHub est rangé dans le coffre-fort de Supabase (Vault) sous le nom
-- « github_dispatch_token » (voir README). Il n'apparaît jamais dans ce fichier ni sur le site.
-- À coller dans Supabase : SQL Editor → New query → Run.

create extension if not exists pg_net with schema extensions;

create or replace function public.dispatch_confirmations() returns trigger
language plpgsql security definer set search_path = public as $$
declare
  tok text;
begin
  select decrypted_secret into tok from vault.decrypted_secrets where name = 'github_dispatch_token';
  if tok is not null then
    perform net.http_post(
      url := 'https://api.github.com/repos/nielsdutrievoz/antarctic-ar-detection/actions/workflows/confirmations.yml/dispatches',
      body := '{"ref": "main"}'::jsonb,
      headers := jsonb_build_object(
        'Accept', 'application/vnd.github+json',
        'Authorization', 'Bearer ' || tok,
        'X-GitHub-Api-Version', '2022-11-28',
        'User-Agent', 'antarctic-ar-alerts',
        'Content-Type', 'application/json'),
      timeout_milliseconds := 5000);
  end if;
  return null;
exception when others then
  -- l'appel à GitHub ne doit jamais bloquer une inscription : la tâche planifiée prendra le relais
  return null;
end $$;

revoke execute on function public.dispatch_confirmations() from public, anon, authenticated;

drop trigger if exists dispatch_confirmations on public.subscriptions;
create trigger dispatch_confirmations after insert on public.subscriptions
  for each statement execute function public.dispatch_confirmations();
