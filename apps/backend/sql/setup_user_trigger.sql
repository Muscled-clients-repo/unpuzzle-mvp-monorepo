-- Fix the user creation trigger to match Django model structure
-- This script updates the trigger to include all required fields

-- Drop existing trigger first
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
DROP FUNCTION IF EXISTS public.handle_new_user();

-- Create improved function to handle new user creation
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
  INSERT INTO public.user_profiles (
    supabase_user_id,
    email,
    full_name,
    display_name,
    status,
    timezone,
    language,
    email_verified,
    created_at,
    updated_at
  )
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'full_name', ''),
    COALESCE(NEW.raw_user_meta_data->>'display_name', ''),
    'active',  -- Default status
    'UTC',     -- Default timezone
    'en',      -- Default language
    COALESCE(NEW.email_confirmed_at IS NOT NULL, false),
    NOW(),
    NOW()
  )
  ON CONFLICT (supabase_user_id) DO UPDATE
  SET
    email = EXCLUDED.email,
    full_name = EXCLUDED.full_name,
    email_verified = EXCLUDED.email_verified,
    updated_at = NOW();
  
  RETURN NEW;
EXCEPTION
  WHEN OTHERS THEN
    -- Log error but don't fail the signup
    RAISE WARNING 'Failed to create user profile: %', SQLERRM;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create trigger for new user sign ups
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Grant permissions
GRANT EXECUTE ON FUNCTION public.handle_new_user() TO service_role;

-- Test by syncing any existing users that don't have profiles
INSERT INTO public.user_profiles (
  supabase_user_id,
  email,
  full_name,
  status,
  timezone,
  language,
  email_verified,
  created_at,
  updated_at
)
SELECT 
  au.id,
  au.email,
  COALESCE(au.raw_user_meta_data->>'full_name', ''),
  'active',
  'UTC',
  'en',
  COALESCE(au.email_confirmed_at IS NOT NULL, false),
  COALESCE(au.created_at, NOW()),
  NOW()
FROM auth.users au
LEFT JOIN public.user_profiles up ON up.supabase_user_id = au.id
WHERE up.supabase_user_id IS NULL
ON CONFLICT (supabase_user_id) DO NOTHING;