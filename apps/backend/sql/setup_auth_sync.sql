-- ============================================
-- Automatic Sync between auth.users and user_profiles
-- ============================================
-- Run this script in Supabase SQL Editor to enable automatic syncing
-- This script is safe to run multiple times

-- Drop existing triggers first (to allow re-running)
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
DROP TRIGGER IF EXISTS on_auth_user_updated ON auth.users;
DROP TRIGGER IF EXISTS on_auth_user_deleted ON auth.users;

-- Drop existing functions (to allow re-creation)
DROP FUNCTION IF EXISTS public.handle_new_user() CASCADE;
DROP FUNCTION IF EXISTS public.handle_user_update() CASCADE;
DROP FUNCTION IF EXISTS public.handle_user_delete() CASCADE;

-- Function to handle new user creation
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
  -- Only proceed if email is not null (required field)
  IF NEW.email IS NOT NULL THEN
    INSERT INTO public.user_profiles (
      supabase_user_id,
      email,
      full_name,
      display_name,
      avatar_url,
      bio,
      status,
      phone_number,
      timezone,
      language,
      email_verified,
      created_at,
      updated_at
    )
    VALUES (
      NEW.id,
      NEW.email,  -- Email is required, no COALESCE needed
      COALESCE(NEW.raw_user_meta_data->>'full_name', ''),
      COALESCE(
        NEW.raw_user_meta_data->>'display_name', 
        NEW.raw_user_meta_data->>'full_name', 
        SPLIT_PART(NEW.email, '@', 1)
      ),
      COALESCE(NEW.raw_user_meta_data->>'avatar_url', ''),
      COALESCE(NEW.raw_user_meta_data->>'bio', ''),
      'active',
      COALESCE(NEW.phone, ''),
      COALESCE(NEW.raw_user_meta_data->>'timezone', 'UTC'),
      COALESCE(NEW.raw_user_meta_data->>'language', 'en'),
      COALESCE(NEW.email_confirmed_at IS NOT NULL, false),
      COALESCE(NEW.created_at, NOW()),
      NOW()
    )
    ON CONFLICT (supabase_user_id) DO UPDATE SET
      email = EXCLUDED.email,
      full_name = COALESCE(EXCLUDED.full_name, user_profiles.full_name),
      email_verified = EXCLUDED.email_verified,
      updated_at = NOW();
  END IF;
  
  RETURN NEW;
EXCEPTION
  WHEN OTHERS THEN
    -- Log the error but don't block the signup
    RAISE WARNING 'Failed to create user profile for %: %', NEW.email, SQLERRM;
    -- Still return NEW to allow the auth signup to complete
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to handle user updates
CREATE OR REPLACE FUNCTION public.handle_user_update()
RETURNS trigger AS $$
BEGIN
  UPDATE public.user_profiles
  SET
    email = COALESCE(NEW.email, OLD.email),
    full_name = COALESCE(NEW.raw_user_meta_data->>'full_name', OLD.raw_user_meta_data->>'full_name', full_name),
    display_name = COALESCE(NEW.raw_user_meta_data->>'display_name', NEW.raw_user_meta_data->>'full_name', OLD.raw_user_meta_data->>'display_name', OLD.raw_user_meta_data->>'full_name', display_name),
    avatar_url = COALESCE(NEW.raw_user_meta_data->>'avatar_url', OLD.raw_user_meta_data->>'avatar_url', avatar_url),
    phone_number = COALESCE(NEW.phone, OLD.phone, ''),
    email_verified = COALESCE(NEW.email_confirmed_at IS NOT NULL, false),
    updated_at = NOW()
  WHERE supabase_user_id = NEW.id;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to handle user deletion (cascade delete)
CREATE OR REPLACE FUNCTION public.handle_user_delete()
RETURNS trigger AS $$
BEGIN
  -- Delete the user profile and let CASCADE handle related records
  DELETE FROM public.user_profiles
  WHERE supabase_user_id = OLD.id;
  
  RETURN OLD;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create triggers
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

CREATE TRIGGER on_auth_user_updated
  AFTER UPDATE ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_user_update();

CREATE TRIGGER on_auth_user_deleted
  AFTER DELETE ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_user_delete();

-- Sync existing users (one-time migration)
DO $$
DECLARE
  auth_user RECORD;
BEGIN
  FOR auth_user IN 
    SELECT au.id, au.email, au.phone, au.raw_user_meta_data, au.email_confirmed_at, au.created_at
    FROM auth.users au
    LEFT JOIN public.user_profiles up ON up.supabase_user_id = au.id
    WHERE up.supabase_user_id IS NULL AND au.email IS NOT NULL
  LOOP
    BEGIN
      INSERT INTO public.user_profiles (
        supabase_user_id,
        email,
        full_name,
        display_name,
        avatar_url,
        bio,
        status,
        phone_number,
        timezone,
        language,
        email_verified,
        created_at,
        updated_at
      )
      VALUES (
        auth_user.id,
        auth_user.email,  -- Email is required
        COALESCE(auth_user.raw_user_meta_data->>'full_name', ''),
        COALESCE(
          auth_user.raw_user_meta_data->>'display_name', 
          auth_user.raw_user_meta_data->>'full_name', 
          SPLIT_PART(auth_user.email, '@', 1)
        ),
        COALESCE(auth_user.raw_user_meta_data->>'avatar_url', ''),
        COALESCE(auth_user.raw_user_meta_data->>'bio', ''),
        'active',
        COALESCE(auth_user.phone, ''),
        COALESCE(auth_user.raw_user_meta_data->>'timezone', 'UTC'),
        COALESCE(auth_user.raw_user_meta_data->>'language', 'en'),
        COALESCE(auth_user.email_confirmed_at IS NOT NULL, false),
        COALESCE(auth_user.created_at, NOW()),
        NOW()
      )
      ON CONFLICT (supabase_user_id) DO NOTHING;
    EXCEPTION
      WHEN OTHERS THEN
        RAISE WARNING 'Failed to migrate user %: %', auth_user.email, SQLERRM;
    END;
  END LOOP;
END $$;

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT EXECUTE ON FUNCTION public.handle_new_user() TO service_role;
GRANT EXECUTE ON FUNCTION public.handle_user_update() TO service_role;
GRANT EXECUTE ON FUNCTION public.handle_user_delete() TO service_role;

-- Enable RLS bypass for triggers (they run as service_role context)
COMMENT ON FUNCTION public.handle_new_user() IS 'Automatically creates user_profiles when users are created in auth.users';
COMMENT ON FUNCTION public.handle_user_update() IS 'Automatically updates user_profiles when users are updated in auth.users';
COMMENT ON FUNCTION public.handle_user_delete() IS 'Automatically soft-deletes user_profiles when users are deleted from auth.users';

-- Fix PostgreSQL sequences (prevents duplicate key errors)
DO $$
DECLARE
  seq_record RECORD;
  max_id INTEGER;
BEGIN
  -- Fix user_roles sequence
  SELECT COALESCE(MAX(id), 0) INTO max_id FROM public.user_roles;
  PERFORM setval('user_roles_id_seq', max_id + 1);
  RAISE NOTICE 'Fixed user_roles sequence to %', max_id + 1;
  
  -- Fix roles sequence  
  SELECT COALESCE(MAX(id), 0) INTO max_id FROM public.roles;
  PERFORM setval('roles_id_seq', max_id + 1);
  RAISE NOTICE 'Fixed roles sequence to %', max_id + 1;
  
  -- Fix sessions sequence
  SELECT COALESCE(MAX(id), 0) INTO max_id FROM public.sessions;
  PERFORM setval('sessions_id_seq', max_id + 1);
  RAISE NOTICE 'Fixed sessions sequence to %', max_id + 1;
  
EXCEPTION
  WHEN OTHERS THEN
    RAISE WARNING 'Error fixing sequences: %', SQLERRM;
END $$;

SELECT 'Auth sync triggers created successfully!' AS status;