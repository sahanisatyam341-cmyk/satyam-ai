-- Supabase -> SQL Editor me ye ek baar chalao
create table if not exists chats (
  id uuid primary key,
  user_id uuid not null default auth.uid() references auth.users on delete cascade,
  title text,
  msgs jsonb default '[]',
  created_at timestamptz default now()
);
alter table chats enable row level security;
create policy "apni chats" on chats for all
  using (auth.uid() = user_id) with check (auth.uid() = user_id);
