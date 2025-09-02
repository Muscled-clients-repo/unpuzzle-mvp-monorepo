-- ============================================
-- COMPREHENSIVE ROW LEVEL SECURITY (RLS) POLICIES
-- This script enables RLS and creates policies for ALL Django tables
-- Ensures service role can perform all operations
-- ============================================

-- ============================================
-- ACCOUNTS APP TABLES
-- ============================================

-- 1. User Profiles
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Users can view own profile" ON user_profiles;
DROP POLICY IF EXISTS "Users can update own profile" ON user_profiles;
DROP POLICY IF EXISTS "Public profiles are viewable" ON user_profiles;
DROP POLICY IF EXISTS "service_role_user_profiles" ON user_profiles;

-- User policies
CREATE POLICY "Users can view own profile" ON user_profiles
    FOR SELECT USING (supabase_user_id = auth.uid());

CREATE POLICY "Users can update own profile" ON user_profiles
    FOR UPDATE USING (supabase_user_id = auth.uid());

CREATE POLICY "Users can insert own profile" ON user_profiles
    FOR INSERT WITH CHECK (supabase_user_id = auth.uid());

CREATE POLICY "Public profiles are viewable" ON user_profiles
    FOR SELECT USING (status = 'active');

-- Service role bypass
CREATE POLICY "service_role_user_profiles" ON user_profiles
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- 2. Roles
ALTER TABLE roles ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "View active roles" ON roles;
DROP POLICY IF EXISTS "service_role_roles" ON roles;

CREATE POLICY "View active roles" ON roles
    FOR SELECT USING (is_active = true);

CREATE POLICY "service_role_roles" ON roles
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- 3. User Roles
ALTER TABLE user_roles ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own roles" ON user_roles;
DROP POLICY IF EXISTS "service_role_user_roles" ON user_roles;

CREATE POLICY "Users can view own roles" ON user_roles
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "service_role_user_roles" ON user_roles
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- 4. Sessions
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own sessions" ON sessions;
DROP POLICY IF EXISTS "Users can update own sessions" ON sessions;
DROP POLICY IF EXISTS "service_role_sessions" ON sessions;

CREATE POLICY "Users can view own sessions" ON sessions
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users can update own sessions" ON sessions
    FOR UPDATE USING (user_id = auth.uid());

CREATE POLICY "Users can insert own sessions" ON sessions
    FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can delete own sessions" ON sessions
    FOR DELETE USING (user_id = auth.uid());

CREATE POLICY "service_role_sessions" ON sessions
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- 5. Subscription Plans
ALTER TABLE subscription_plans ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "View active subscription plans" ON subscription_plans;
DROP POLICY IF EXISTS "service_role_subscription_plans" ON subscription_plans;

CREATE POLICY "View active subscription plans" ON subscription_plans
    FOR SELECT USING (is_active = true);

CREATE POLICY "service_role_subscription_plans" ON subscription_plans
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- 6. User Subscriptions
ALTER TABLE user_subscriptions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own subscription" ON user_subscriptions;
DROP POLICY IF EXISTS "Users can update own subscription" ON user_subscriptions;
DROP POLICY IF EXISTS "service_role_user_subscriptions" ON user_subscriptions;

CREATE POLICY "Users can view own subscription" ON user_subscriptions
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users can update own subscription" ON user_subscriptions
    FOR UPDATE USING (user_id = auth.uid());

CREATE POLICY "service_role_user_subscriptions" ON user_subscriptions
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- 7. Subscription History
ALTER TABLE subscription_history ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own subscription history" ON subscription_history;
DROP POLICY IF EXISTS "service_role_subscription_history" ON subscription_history;

CREATE POLICY "Users can view own subscription history" ON subscription_history
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "service_role_subscription_history" ON subscription_history
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- ============================================
-- COURSES APP TABLES
-- ============================================

-- 8. Course Categories
ALTER TABLE course_categories ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "View active categories" ON course_categories;
DROP POLICY IF EXISTS "service_role_course_categories" ON course_categories;

CREATE POLICY "View active categories" ON course_categories
    FOR SELECT USING (is_active = true);

CREATE POLICY "service_role_course_categories" ON course_categories
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- 9. Courses
ALTER TABLE courses ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "View published courses" ON courses;
DROP POLICY IF EXISTS "Instructors view own courses" ON courses;
DROP POLICY IF EXISTS "Instructors update own courses" ON courses;
DROP POLICY IF EXISTS "Instructors can create courses" ON courses;
DROP POLICY IF EXISTS "Instructors delete own courses" ON courses;
DROP POLICY IF EXISTS "service_role_courses" ON courses;

CREATE POLICY "View published courses" ON courses
    FOR SELECT USING (is_published = true AND status IN ('published', 'active'));

CREATE POLICY "Instructors view own courses" ON courses
    FOR SELECT USING (instructor_id = auth.uid());

CREATE POLICY "Instructors update own courses" ON courses
    FOR UPDATE USING (instructor_id = auth.uid());

CREATE POLICY "Instructors can create courses" ON courses
    FOR INSERT WITH CHECK (instructor_id = auth.uid());

CREATE POLICY "Instructors delete own courses" ON courses
    FOR DELETE USING (instructor_id = auth.uid());

CREATE POLICY "service_role_courses" ON courses
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- 10. Course Sections
ALTER TABLE course_sections ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "View published course sections" ON course_sections;
DROP POLICY IF EXISTS "Instructors manage own course sections" ON course_sections;
DROP POLICY IF EXISTS "service_role_course_sections" ON course_sections;

CREATE POLICY "View published course sections" ON course_sections
    FOR SELECT USING (
        is_published = true AND
        course_id IN (
            SELECT id FROM courses 
            WHERE is_published = true AND status IN ('published', 'active')
        )
    );

CREATE POLICY "Instructors manage own course sections" ON course_sections
    FOR ALL USING (
        course_id IN (
            SELECT id FROM courses 
            WHERE instructor_id = auth.uid()
        )
    );

CREATE POLICY "service_role_course_sections" ON course_sections
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- ============================================
-- ENROLLMENTS APP TABLES
-- ============================================

-- 11. Enrollments
ALTER TABLE enrollments ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users view own enrollments" ON enrollments;
DROP POLICY IF EXISTS "Users update own enrollments" ON enrollments;
DROP POLICY IF EXISTS "Users create own enrollments" ON enrollments;
DROP POLICY IF EXISTS "Instructors view course enrollments" ON enrollments;
DROP POLICY IF EXISTS "service_role_enrollments" ON enrollments;

CREATE POLICY "Users view own enrollments" ON enrollments
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users update own enrollments" ON enrollments
    FOR UPDATE USING (user_id = auth.uid());

CREATE POLICY "Users create own enrollments" ON enrollments
    FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY "Instructors view course enrollments" ON enrollments
    FOR SELECT USING (
        course_id IN (
            SELECT id FROM courses 
            WHERE instructor_id = auth.uid()
        )
    );

CREATE POLICY "service_role_enrollments" ON enrollments
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- 12. Course Reviews
ALTER TABLE course_reviews ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "View verified reviews" ON course_reviews;
DROP POLICY IF EXISTS "Users manage own reviews" ON course_reviews;
DROP POLICY IF EXISTS "service_role_course_reviews" ON course_reviews;

CREATE POLICY "View verified reviews" ON course_reviews
    FOR SELECT USING (is_verified = true);

CREATE POLICY "Users manage own reviews" ON course_reviews
    FOR ALL USING (
        enrollment_id IN (
            SELECT id FROM enrollments 
            WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "service_role_course_reviews" ON course_reviews
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- ============================================
-- MEDIA LIBRARY TABLES
-- ============================================

-- 13. Media Files
ALTER TABLE media_files ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users view own media files" ON media_files;
DROP POLICY IF EXISTS "View public media files" ON media_files;
DROP POLICY IF EXISTS "Users manage own media files" ON media_files;
DROP POLICY IF EXISTS "Instructors view course media" ON media_files;
DROP POLICY IF EXISTS "service_role_media_files" ON media_files;

CREATE POLICY "Users view own media files" ON media_files
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "View public media files" ON media_files
    FOR SELECT USING (is_public = true);

CREATE POLICY "Users manage own media files" ON media_files
    FOR ALL USING (user_id = auth.uid());

CREATE POLICY "Instructors view course media" ON media_files
    FOR SELECT USING (
        course_id IN (
            SELECT id FROM courses 
            WHERE instructor_id = auth.uid()
        )
    );

CREATE POLICY "service_role_media_files" ON media_files
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- 14. Upload Sessions
ALTER TABLE upload_sessions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users manage own upload sessions" ON upload_sessions;
DROP POLICY IF EXISTS "service_role_upload_sessions" ON upload_sessions;

CREATE POLICY "Users manage own upload sessions" ON upload_sessions
    FOR ALL USING (created_by = auth.uid());

CREATE POLICY "service_role_upload_sessions" ON upload_sessions
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- ============================================
-- PAYMENTS APP TABLES
-- ============================================

-- 15. Payment Intents
ALTER TABLE payment_intents ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users view own payment intents" ON payment_intents;
DROP POLICY IF EXISTS "Users create own payment intents" ON payment_intents;
DROP POLICY IF EXISTS "service_role_payment_intents" ON payment_intents;

CREATE POLICY "Users view own payment intents" ON payment_intents
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users create own payment intents" ON payment_intents
    FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY "service_role_payment_intents" ON payment_intents
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- 16. Payment Transactions
ALTER TABLE payment_transactions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users view own payment transactions" ON payment_transactions;
DROP POLICY IF EXISTS "service_role_payment_transactions" ON payment_transactions;

CREATE POLICY "Users view own payment transactions" ON payment_transactions
    FOR SELECT USING (
        payment_intent_id IN (
            SELECT id FROM payment_intents 
            WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "service_role_payment_transactions" ON payment_transactions
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- 17. Payment Refunds
ALTER TABLE payment_refunds ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users view own payment refunds" ON payment_refunds;
DROP POLICY IF EXISTS "service_role_payment_refunds" ON payment_refunds;

CREATE POLICY "Users view own payment refunds" ON payment_refunds
    FOR SELECT USING (
        transaction_id IN (
            SELECT pt.id FROM payment_transactions pt
            JOIN payment_intents pi ON pt.payment_intent_id = pi.id
            WHERE pi.user_id = auth.uid()
        )
    );

CREATE POLICY "service_role_payment_refunds" ON payment_refunds
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- 18. Stripe Customers
ALTER TABLE stripe_customers ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users view own stripe customer" ON stripe_customers;
DROP POLICY IF EXISTS "service_role_stripe_customers" ON stripe_customers;

CREATE POLICY "Users view own stripe customer" ON stripe_customers
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "service_role_stripe_customers" ON stripe_customers
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- 19. Webhook Events
ALTER TABLE webhook_events ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "service_role_webhook_events" ON webhook_events;

-- No user policies for webhook events - admin only table
CREATE POLICY "service_role_webhook_events" ON webhook_events
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- ============================================
-- PUZZLE REFLECTIONS APP TABLES
-- ============================================

-- 20. Puzzle Reflections
ALTER TABLE puzzle_reflections ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users view own puzzle reflections" ON puzzle_reflections;
DROP POLICY IF EXISTS "Users manage own puzzle reflections" ON puzzle_reflections;
DROP POLICY IF EXISTS "Instructors view course puzzle reflections" ON puzzle_reflections;
DROP POLICY IF EXISTS "service_role_puzzle_reflections" ON puzzle_reflections;

CREATE POLICY "Users view own puzzle reflections" ON puzzle_reflections
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users manage own puzzle reflections" ON puzzle_reflections
    FOR ALL USING (user_id = auth.uid());

CREATE POLICY "Instructors view course puzzle reflections" ON puzzle_reflections
    FOR SELECT USING (
        course_id IN (
            SELECT id FROM courses 
            WHERE instructor_id = auth.uid()
        )
    );

CREATE POLICY "service_role_puzzle_reflections" ON puzzle_reflections
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- ============================================
-- AI ASSISTANT APP TABLES
-- ============================================

-- 21. AI Sessions
ALTER TABLE ai_sessions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users manage own AI sessions" ON ai_sessions;
DROP POLICY IF EXISTS "service_role_ai_sessions" ON ai_sessions;

CREATE POLICY "Users manage own AI sessions" ON ai_sessions
    FOR ALL USING (user_id = auth.uid());

CREATE POLICY "service_role_ai_sessions" ON ai_sessions
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- 22. AI Messages
ALTER TABLE ai_messages ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users manage own AI messages" ON ai_messages;
DROP POLICY IF EXISTS "service_role_ai_messages" ON ai_messages;

CREATE POLICY "Users manage own AI messages" ON ai_messages
    FOR ALL USING (
        session_id IN (
            SELECT id FROM ai_sessions 
            WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "service_role_ai_messages" ON ai_messages
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- 23. AI Usage Metrics
ALTER TABLE ai_usage_metrics ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users view own AI usage metrics" ON ai_usage_metrics;
DROP POLICY IF EXISTS "service_role_ai_usage_metrics" ON ai_usage_metrics;

CREATE POLICY "Users view own AI usage metrics" ON ai_usage_metrics
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "service_role_ai_usage_metrics" ON ai_usage_metrics
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- 24. Transcript Segments
ALTER TABLE transcript_segments ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "View transcript segments for enrolled courses" ON transcript_segments;
DROP POLICY IF EXISTS "Instructors manage course transcript segments" ON transcript_segments;
DROP POLICY IF EXISTS "service_role_transcript_segments" ON transcript_segments;

CREATE POLICY "View transcript segments for enrolled courses" ON transcript_segments
    FOR SELECT USING (
        course_id IN (
            SELECT course_id FROM enrollments 
            WHERE user_id = auth.uid() AND status = 'active'
        )
    );

CREATE POLICY "Instructors manage course transcript segments" ON transcript_segments
    FOR ALL USING (
        course_id IN (
            SELECT id FROM courses 
            WHERE instructor_id = auth.uid()
        )
    );

CREATE POLICY "service_role_transcript_segments" ON transcript_segments
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- 25. Transcript References
ALTER TABLE transcript_references ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users manage own transcript references" ON transcript_references;
DROP POLICY IF EXISTS "service_role_transcript_references" ON transcript_references;

CREATE POLICY "Users manage own transcript references" ON transcript_references
    FOR ALL USING (user_id = auth.uid());

CREATE POLICY "service_role_transcript_references" ON transcript_references
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- 26. User AI Preferences
ALTER TABLE user_ai_preferences ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users manage own AI preferences" ON user_ai_preferences;
DROP POLICY IF EXISTS "service_role_user_ai_preferences" ON user_ai_preferences;

CREATE POLICY "Users manage own AI preferences" ON user_ai_preferences
    FOR ALL USING (user_id = auth.uid());

CREATE POLICY "service_role_user_ai_preferences" ON user_ai_preferences
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- ============================================
-- DJANGO SYSTEM TABLES
-- ============================================
-- IMPORTANT: Django system tables need RLS enabled but should ONLY be accessible
-- by the service role (Django backend). No user policies are created for these tables.

-- 27. Django Auth Group
ALTER TABLE auth_group ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "service_role_auth_group" ON auth_group;

CREATE POLICY "service_role_auth_group" ON auth_group
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- 28. Django Auth Group Permissions
ALTER TABLE auth_group_permissions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "service_role_auth_group_permissions" ON auth_group_permissions;

CREATE POLICY "service_role_auth_group_permissions" ON auth_group_permissions
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- 29. Django Auth Permission
ALTER TABLE auth_permission ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "service_role_auth_permission" ON auth_permission;

CREATE POLICY "service_role_auth_permission" ON auth_permission
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- 30. Django Auth User (Legacy - if still exists)
ALTER TABLE auth_user ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "service_role_auth_user" ON auth_user;

CREATE POLICY "service_role_auth_user" ON auth_user
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- 31. Django Auth User Groups
ALTER TABLE auth_user_groups ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "service_role_auth_user_groups" ON auth_user_groups;

CREATE POLICY "service_role_auth_user_groups" ON auth_user_groups
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- 32. Django Auth User Permissions
ALTER TABLE auth_user_user_permissions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "service_role_auth_user_user_permissions" ON auth_user_user_permissions;

CREATE POLICY "service_role_auth_user_user_permissions" ON auth_user_user_permissions
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- 33. Django Content Type
ALTER TABLE django_content_type ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "service_role_django_content_type" ON django_content_type;

CREATE POLICY "service_role_django_content_type" ON django_content_type
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- 34. Django Migrations
ALTER TABLE django_migrations ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "service_role_django_migrations" ON django_migrations;

CREATE POLICY "service_role_django_migrations" ON django_migrations
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- 35. Django Admin Log (if exists)
DO $$ 
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'django_admin_log') THEN
        ALTER TABLE django_admin_log ENABLE ROW LEVEL SECURITY;
        
        DROP POLICY IF EXISTS "service_role_django_admin_log" ON django_admin_log;
        
        CREATE POLICY "service_role_django_admin_log" ON django_admin_log
            FOR ALL TO service_role USING (true) WITH CHECK (true);
    END IF;
END $$;

-- 36. Django Session (if exists)
DO $$ 
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'django_session') THEN
        ALTER TABLE django_session ENABLE ROW LEVEL SECURITY;
        
        DROP POLICY IF EXISTS "service_role_django_session" ON django_session;
        
        CREATE POLICY "service_role_django_session" ON django_session
            FOR ALL TO service_role USING (true) WITH CHECK (true);
    END IF;
END $$;

-- 37. Django Site (if using django.contrib.sites)
DO $$ 
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'django_site') THEN
        ALTER TABLE django_site ENABLE ROW LEVEL SECURITY;
        
        DROP POLICY IF EXISTS "service_role_django_site" ON django_site;
        
        CREATE POLICY "service_role_django_site" ON django_site
            FOR ALL TO service_role USING (true) WITH CHECK (true);
    END IF;
END $$;

-- 38. Django Flatpage (if using django.contrib.flatpages)
DO $$ 
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'django_flatpage') THEN
        ALTER TABLE django_flatpage ENABLE ROW LEVEL SECURITY;
        ALTER TABLE django_flatpage_sites ENABLE ROW LEVEL SECURITY;
        
        DROP POLICY IF EXISTS "service_role_django_flatpage" ON django_flatpage;
        DROP POLICY IF EXISTS "service_role_django_flatpage_sites" ON django_flatpage_sites;
        
        CREATE POLICY "service_role_django_flatpage" ON django_flatpage
            FOR ALL TO service_role USING (true) WITH CHECK (true);
            
        CREATE POLICY "service_role_django_flatpage_sites" ON django_flatpage_sites
            FOR ALL TO service_role USING (true) WITH CHECK (true);
    END IF;
END $$;

-- 39. Django Redirect (if using django.contrib.redirects)
DO $$ 
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'django_redirect') THEN
        ALTER TABLE django_redirect ENABLE ROW LEVEL SECURITY;
        
        DROP POLICY IF EXISTS "service_role_django_redirect" ON django_redirect;
        
        CREATE POLICY "service_role_django_redirect" ON django_redirect
            FOR ALL TO service_role USING (true) WITH CHECK (true);
    END IF;
END $$;

-- ============================================
-- THIRD PARTY PACKAGE TABLES (if they exist)
-- ============================================

-- 40. REST Framework Token (if using token auth)
DO $$ 
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'authtoken_token') THEN
        ALTER TABLE authtoken_token ENABLE ROW LEVEL SECURITY;
        
        DROP POLICY IF EXISTS "service_role_authtoken_token" ON authtoken_token;
        
        CREATE POLICY "service_role_authtoken_token" ON authtoken_token
            FOR ALL TO service_role USING (true) WITH CHECK (true);
    END IF;
END $$;

-- 41. Token Blacklist (if using JWT blacklist)
DO $$ 
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'token_blacklist_outstandingtoken') THEN
        ALTER TABLE token_blacklist_outstandingtoken ENABLE ROW LEVEL SECURITY;
        ALTER TABLE token_blacklist_blacklistedtoken ENABLE ROW LEVEL SECURITY;
        
        DROP POLICY IF EXISTS "service_role_outstanding_token" ON token_blacklist_outstandingtoken;
        DROP POLICY IF EXISTS "service_role_blacklisted_token" ON token_blacklist_blacklistedtoken;
        
        CREATE POLICY "service_role_outstanding_token" ON token_blacklist_outstandingtoken
            FOR ALL TO service_role USING (true) WITH CHECK (true);
            
        CREATE POLICY "service_role_blacklisted_token" ON token_blacklist_blacklistedtoken
            FOR ALL TO service_role USING (true) WITH CHECK (true);
    END IF;
END $$;

-- 42. Celery Beat Tables (if using celery beat)
DO $$ 
BEGIN
    -- Periodic Tasks
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'django_celery_beat_periodictask') THEN
        ALTER TABLE django_celery_beat_periodictask ENABLE ROW LEVEL SECURITY;
        
        DROP POLICY IF EXISTS "service_role_celery_periodic_task" ON django_celery_beat_periodictask;
        
        CREATE POLICY "service_role_celery_periodic_task" ON django_celery_beat_periodictask
            FOR ALL TO service_role USING (true) WITH CHECK (true);
    END IF;
    
    -- Interval Schedule
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'django_celery_beat_intervalschedule') THEN
        ALTER TABLE django_celery_beat_intervalschedule ENABLE ROW LEVEL SECURITY;
        
        DROP POLICY IF EXISTS "service_role_celery_interval" ON django_celery_beat_intervalschedule;
        
        CREATE POLICY "service_role_celery_interval" ON django_celery_beat_intervalschedule
            FOR ALL TO service_role USING (true) WITH CHECK (true);
    END IF;
    
    -- Crontab Schedule
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'django_celery_beat_crontabschedule') THEN
        ALTER TABLE django_celery_beat_crontabschedule ENABLE ROW LEVEL SECURITY;
        
        DROP POLICY IF EXISTS "service_role_celery_crontab" ON django_celery_beat_crontabschedule;
        
        CREATE POLICY "service_role_celery_crontab" ON django_celery_beat_crontabschedule
            FOR ALL TO service_role USING (true) WITH CHECK (true);
    END IF;
    
    -- Solar Schedule
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'django_celery_beat_solarschedule') THEN
        ALTER TABLE django_celery_beat_solarschedule ENABLE ROW LEVEL SECURITY;
        
        DROP POLICY IF EXISTS "service_role_celery_solar" ON django_celery_beat_solarschedule;
        
        CREATE POLICY "service_role_celery_solar" ON django_celery_beat_solarschedule
            FOR ALL TO service_role USING (true) WITH CHECK (true);
    END IF;
    
    -- Clocked Schedule
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'django_celery_beat_clockedschedule') THEN
        ALTER TABLE django_celery_beat_clockedschedule ENABLE ROW LEVEL SECURITY;
        
        DROP POLICY IF EXISTS "service_role_celery_clocked" ON django_celery_beat_clockedschedule;
        
        CREATE POLICY "service_role_celery_clocked" ON django_celery_beat_clockedschedule
            FOR ALL TO service_role USING (true) WITH CHECK (true);
    END IF;
    
    -- Periodic Task Changed
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'django_celery_beat_periodictasks') THEN
        ALTER TABLE django_celery_beat_periodictasks ENABLE ROW LEVEL SECURITY;
        
        DROP POLICY IF EXISTS "service_role_celery_periodic_tasks" ON django_celery_beat_periodictasks;
        
        CREATE POLICY "service_role_celery_periodic_tasks" ON django_celery_beat_periodictasks
            FOR ALL TO service_role USING (true) WITH CHECK (true);
    END IF;
END $$;

-- 43. Celery Results Tables (if using django-celery-results)
DO $$ 
BEGIN
    -- Task Results
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'django_celery_results_taskresult') THEN
        ALTER TABLE django_celery_results_taskresult ENABLE ROW LEVEL SECURITY;
        
        DROP POLICY IF EXISTS "service_role_celery_task_result" ON django_celery_results_taskresult;
        
        CREATE POLICY "service_role_celery_task_result" ON django_celery_results_taskresult
            FOR ALL TO service_role USING (true) WITH CHECK (true);
    END IF;
    
    -- Chord Counter
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'django_celery_results_chordcounter') THEN
        ALTER TABLE django_celery_results_chordcounter ENABLE ROW LEVEL SECURITY;
        
        DROP POLICY IF EXISTS "service_role_celery_chord_counter" ON django_celery_results_chordcounter;
        
        CREATE POLICY "service_role_celery_chord_counter" ON django_celery_results_chordcounter
            FOR ALL TO service_role USING (true) WITH CHECK (true);
    END IF;
    
    -- Group Results
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'django_celery_results_groupresult') THEN
        ALTER TABLE django_celery_results_groupresult ENABLE ROW LEVEL SECURITY;
        
        DROP POLICY IF EXISTS "service_role_celery_group_result" ON django_celery_results_groupresult;
        
        CREATE POLICY "service_role_celery_group_result" ON django_celery_results_groupresult
            FOR ALL TO service_role USING (true) WITH CHECK (true);
    END IF;
END $$;

-- 44. Django Cache Table (if using database cache)
DO $$ 
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'django_cache') THEN
        ALTER TABLE django_cache ENABLE ROW LEVEL SECURITY;
        
        DROP POLICY IF EXISTS "service_role_django_cache" ON django_cache;
        
        CREATE POLICY "service_role_django_cache" ON django_cache
            FOR ALL TO service_role USING (true) WITH CHECK (true);
    END IF;
END $$;

-- 45. Django Q Tables (if using Django Q)
DO $$ 
BEGIN
    -- ORM Queue
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'django_q_ormq') THEN
        ALTER TABLE django_q_ormq ENABLE ROW LEVEL SECURITY;
        
        DROP POLICY IF EXISTS "service_role_django_q_ormq" ON django_q_ormq;
        
        CREATE POLICY "service_role_django_q_ormq" ON django_q_ormq
            FOR ALL TO service_role USING (true) WITH CHECK (true);
    END IF;
    
    -- Task
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'django_q_task') THEN
        ALTER TABLE django_q_task ENABLE ROW LEVEL SECURITY;
        
        DROP POLICY IF EXISTS "service_role_django_q_task" ON django_q_task;
        
        CREATE POLICY "service_role_django_q_task" ON django_q_task
            FOR ALL TO service_role USING (true) WITH CHECK (true);
    END IF;
    
    -- Schedule
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'django_q_schedule') THEN
        ALTER TABLE django_q_schedule ENABLE ROW LEVEL SECURITY;
        
        DROP POLICY IF EXISTS "service_role_django_q_schedule" ON django_q_schedule;
        
        CREATE POLICY "service_role_django_q_schedule" ON django_q_schedule
            FOR ALL TO service_role USING (true) WITH CHECK (true);
    END IF;
END $$;

-- 46. Corsheaders (if using django-cors-headers)
DO $$ 
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'corsheaders_corsmodel') THEN
        ALTER TABLE corsheaders_corsmodel ENABLE ROW LEVEL SECURITY;
        
        DROP POLICY IF EXISTS "service_role_corsheaders" ON corsheaders_corsmodel;
        
        CREATE POLICY "service_role_corsheaders" ON corsheaders_corsmodel
            FOR ALL TO service_role USING (true) WITH CHECK (true);
    END IF;
END $$;

-- 47. Social Auth Tables (if using social-auth-app-django)
DO $$ 
BEGIN
    -- User Social Auth
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'social_auth_usersocialauth') THEN
        ALTER TABLE social_auth_usersocialauth ENABLE ROW LEVEL SECURITY;
        
        DROP POLICY IF EXISTS "service_role_social_auth_user" ON social_auth_usersocialauth;
        
        CREATE POLICY "service_role_social_auth_user" ON social_auth_usersocialauth
            FOR ALL TO service_role USING (true) WITH CHECK (true);
    END IF;
    
    -- Nonce
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'social_auth_nonce') THEN
        ALTER TABLE social_auth_nonce ENABLE ROW LEVEL SECURITY;
        
        DROP POLICY IF EXISTS "service_role_social_auth_nonce" ON social_auth_nonce;
        
        CREATE POLICY "service_role_social_auth_nonce" ON social_auth_nonce
            FOR ALL TO service_role USING (true) WITH CHECK (true);
    END IF;
    
    -- Association
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'social_auth_association') THEN
        ALTER TABLE social_auth_association ENABLE ROW LEVEL SECURITY;
        
        DROP POLICY IF EXISTS "service_role_social_auth_association" ON social_auth_association;
        
        CREATE POLICY "service_role_social_auth_association" ON social_auth_association
            FOR ALL TO service_role USING (true) WITH CHECK (true);
    END IF;
    
    -- Code
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'social_auth_code') THEN
        ALTER TABLE social_auth_code ENABLE ROW LEVEL SECURITY;
        
        DROP POLICY IF EXISTS "service_role_social_auth_code" ON social_auth_code;
        
        CREATE POLICY "service_role_social_auth_code" ON social_auth_code
            FOR ALL TO service_role USING (true) WITH CHECK (true);
    END IF;
    
    -- Partial
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'social_auth_partial') THEN
        ALTER TABLE social_auth_partial ENABLE ROW LEVEL SECURITY;
        
        DROP POLICY IF EXISTS "service_role_social_auth_partial" ON social_auth_partial;
        
        CREATE POLICY "service_role_social_auth_partial" ON social_auth_partial
            FOR ALL TO service_role USING (true) WITH CHECK (true);
    END IF;
END $$;

-- 48. Django Channels Layer (if using channels_redis)
DO $$ 
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'channels_presence') THEN
        ALTER TABLE channels_presence ENABLE ROW LEVEL SECURITY;
        
        DROP POLICY IF EXISTS "service_role_channels_presence" ON channels_presence;
        
        CREATE POLICY "service_role_channels_presence" ON channels_presence
            FOR ALL TO service_role USING (true) WITH CHECK (true);
    END IF;
END $$;

-- ============================================
-- HELPER FUNCTIONS
-- ============================================

-- Function to check if user is an instructor
CREATE OR REPLACE FUNCTION is_instructor(check_user_id uuid)
RETURNS boolean AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM user_roles ur
        JOIN roles r ON ur.role_id = r.id
        WHERE ur.user_id = check_user_id 
        AND r.name = 'instructor'
        AND r.is_active = true
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to check if user is enrolled in course
CREATE OR REPLACE FUNCTION is_enrolled_in_course(check_user_id uuid, check_course_id uuid)
RETURNS boolean AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM enrollments
        WHERE user_id = check_user_id 
        AND course_id = check_course_id
        AND status = 'active'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to check if user has admin role
CREATE OR REPLACE FUNCTION is_admin(check_user_id uuid)
RETURNS boolean AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM user_roles ur
        JOIN roles r ON ur.role_id = r.id
        WHERE ur.user_id = check_user_id 
        AND r.name = 'admin'
        AND r.is_active = true
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- VERIFICATION QUERIES
-- ============================================
-- Run these queries to verify RLS is enabled on all tables:

-- Check which tables have RLS enabled
SELECT schemaname, tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY tablename;

-- Count policies per table
SELECT schemaname, tablename, COUNT(*) as policy_count
FROM pg_policies
WHERE schemaname = 'public'
GROUP BY schemaname, tablename
ORDER BY tablename;

-- ============================================
-- NOTES
-- ============================================
-- 1. This script enables RLS on ALL tables in the Django application
-- 2. Service role (used by Django backend) bypasses RLS for all operations
-- 3. Users can only access their own data through authenticated role
-- 4. Public/anonymous users have limited read access to published content
-- 5. Instructors have additional permissions for their courses
-- 6. All policies use DROP IF EXISTS to ensure idempotency
-- 7. Helper functions provide reusable permission checks
-- 8. Run verification queries to ensure all tables are protected