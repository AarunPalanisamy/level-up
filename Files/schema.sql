-- Enable UUID extension
create extension if not exists "uuid-ossp";
create extension if not exists moddatetime;

-- 1. PROFILES TABLE
-- Linked to auth.users via trigger
create table public.profiles (
  id uuid references auth.users on delete cascade not null primary key,
  full_name text,
  avatar_url text,
  current_streak int default 0,
  total_xp int default 0,
  last_active_date date, -- Used to calculate streaks
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamptz
);

-- Secure the table
alter table public.profiles enable row level security;

-- Trigger to create profile on signup
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profiles (id, full_name, avatar_url)
  values (
    new.id,
    new.raw_user_meta_data->>'full_name',
    new.raw_user_meta_data->>'avatar_url'
  );
  return new;
end;
$$;


create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();


-- 2. COURSES TABLE
create type course_difficulty as enum ('Low', 'Medium', 'High');
create type course_type_enum as enum ('Interview', 'Basics', 'Deep Concepts');

create table public.courses (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid references public.profiles(id) on delete cascade not null,
  title text not null,
  description text,
  difficulty course_difficulty not null,
  course_type course_type_enum not null,
  length text not null default 'Medium', -- Short, Medium, Long
  toc jsonb not null, -- Stores the list of chapters (validated by app logic/schema)
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamptz
);

alter table public.courses enable row level security;


-- 3. CHAPTERS TABLE
create table public.chapters (
  id uuid default uuid_generate_v4() primary key,
  course_id uuid references public.courses(id) on delete cascade not null,
  chapter_index int not null, -- 1 to 15
  title text not null,
  content jsonb, -- Stores { slides: [...], quiz: [...] }
  is_generated boolean default false,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamptz,
  unique(course_id, chapter_index)
);

alter table public.chapters enable row level security;


-- 4. USER COURSE PROGRESS
create type course_status as enum ('Yet To Start', 'In Progress', 'Completed');

create table public.user_course_progress (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid references public.profiles(id) on delete cascade not null,
  course_id uuid references public.courses(id) on delete cascade not null,
  status course_status default 'Yet To Start',
  last_accessed_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamptz,
  unique(user_id, course_id)
);

alter table public.user_course_progress enable row level security;


-- 5. USER CHAPTER PROGRESS
create table public.user_chapter_progress (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid references public.profiles(id) on delete cascade not null,
  chapter_id uuid references public.chapters(id) on delete cascade not null,
  completed boolean default false,
  last_slide_index int default 0, -- Tracks the last viewed slide (0-based)
  quiz_score int, -- Number of correct answers
  completed_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamptz,
  unique(user_id, chapter_id)
);

alter table public.user_chapter_progress enable row level security;


-- 6. DAILY CAPSULES
create table public.daily_capsules (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid references public.profiles(id) on delete cascade not null,
  content jsonb not null, -- Stores flashcards/micro-lessons
  date date not null default CURRENT_DATE,
  is_completed boolean default false,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamptz
);

alter table public.daily_capsules enable row level security;


-- 7. USER SKILLS
create table public.user_skills (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid references public.profiles(id) on delete cascade not null,
  skill_name text not null,
  level int default 0 check (level >= 0 and level <= 100),
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null,
  unique(user_id, skill_name)
);

alter table public.user_skills enable row level security;


-- 8. CONTENT FEEDBACK
create table public.content_feedback (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid references public.profiles(id) on delete cascade not null,
  chapter_id uuid references public.chapters(id) on delete cascade not null,
  slide_index int, -- Nullable if feedback is for the whole chapter
  is_positive boolean not null, -- Thumbs up (true) or down (false)
  feedback_text text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

alter table public.content_feedback enable row level security;


-- 9. USER BOOKMARKS
create table public.user_bookmarks (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid references public.profiles(id) on delete cascade not null,
  chapter_id uuid references public.chapters(id) on delete cascade not null,
  slide_index int not null, -- Specific slide being bookmarked
  note text, -- Optional user note
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

alter table public.user_bookmarks enable row level security;

-- =========================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- =========================================

-- 1. Profiles: View/Update own profile
create policy "Users can view own profile"
on public.profiles
for select
using (auth.uid() = id);

create policy "Users can update own profile"
on public.profiles
for update
using (auth.uid() = id)
with check (auth.uid() = id);


-- 2. Courses: CRUD own courses
create policy "Users can manage own courses"
on public.courses
for all
using (auth.uid() = user_id)
with check (auth.uid() = user_id);


-- 3. Chapters: CRUD chapters via course ownership
create policy "Users can manage chapters of own courses"
on public.chapters
for all
using (
  exists (
    select 1 from public.courses
    where id = chapters.course_id
      and user_id = auth.uid()
  )
)
with check (
  exists (
    select 1 from public.courses
    where id = chapters.course_id
      and user_id = auth.uid()
  )
);


-- 4. User Progress (Courses): CRUD own
create policy "Users can manage own course progress"
on public.user_course_progress
for all
using (auth.uid() = user_id)
with check (auth.uid() = user_id);


-- 5. User Progress (Chapters): CRUD own
create policy "Users can manage own chapter progress"
on public.user_chapter_progress
for all
using (auth.uid() = user_id)
with check (auth.uid() = user_id);


-- 6. Daily Capsules: CRUD own
create policy "Users can manage own capsules"
on public.daily_capsules
for all
using (auth.uid() = user_id)
with check (auth.uid() = user_id);


-- 7. User Skills: CRUD own
create policy "Users can manage own skills"
on public.user_skills
for all
using (auth.uid() = user_id)
with check (auth.uid() = user_id);


-- 8. Content Feedback: CRUD own
create policy "Users can manage own feedback"
on public.content_feedback
for all
using (auth.uid() = user_id)
with check (auth.uid() = user_id);


-- 9. User Bookmarks: CRUD own
create policy "Users can manage own bookmarks"
on public.user_bookmarks
for all
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

