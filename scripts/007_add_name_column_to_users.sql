-- Add name column to users table if it doesn't exist
ALTER TABLE public.users 
ADD COLUMN IF NOT EXISTS name TEXT NOT NULL DEFAULT 'User';

-- Remove the default after adding the column
ALTER TABLE public.users 
ALTER COLUMN name DROP DEFAULT;
