-- Drop existing foreign key constraint and recreate with correct reference
ALTER TABLE conversations 
  DROP CONSTRAINT IF EXISTS conversations_user_id_fkey;

-- Change user_id type from TEXT to UUID to match public.users
ALTER TABLE conversations 
  ALTER COLUMN user_id TYPE UUID USING user_id::uuid;

-- Add foreign key constraint referencing public.users instead of neon_auth.users_sync
ALTER TABLE conversations 
  ADD CONSTRAINT conversations_user_id_fkey 
  FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;

-- Also fix messages table if needed
ALTER TABLE messages 
  DROP CONSTRAINT IF EXISTS messages_user_id_fkey;

ALTER TABLE messages 
  ALTER COLUMN user_id TYPE UUID USING user_id::uuid;

ALTER TABLE messages 
  ADD CONSTRAINT messages_user_id_fkey 
  FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;
