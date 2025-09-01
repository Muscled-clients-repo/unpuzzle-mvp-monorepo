-- Enable Row Level Security for all Django tables
-- This script enables RLS and creates basic policies for Supabase Auth integration

-- ============================================
-- ACCOUNTS TABLES
-- ============================================

-- User Profiles
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- Users can read their own profile
CREATE POLICY "Users can view own profile" ON user_profiles
    FOR SELECT USING (supabase_user_id = auth.uid());

-- Users can update their own profile
CREATE POLICY "Users can update own profile" ON user_profiles
    FOR UPDATE USING (supabase_user_id = auth.uid());

-- Public profiles can be viewed by anyone (optional - adjust as needed)
CREATE POLICY "Public profiles are viewable" ON user_profiles
    FOR SELECT USING (status = 'active');

-- Roles
ALTER TABLE roles ENABLE ROW LEVEL SECURITY;

-- Anyone can view active roles
CREATE POLICY "View active roles" ON roles
    FOR SELECT USING (is_active = true);

-- User Roles
ALTER TABLE user_roles ENABLE ROW LEVEL SECURITY;

-- Users can view their own roles
CREATE POLICY "Users can view own roles" ON user_roles
    FOR SELECT USING (user_id = auth.uid());

-- Sessions
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;

-- Users can view their own sessions
CREATE POLICY "Users can view own sessions" ON sessions
    FOR SELECT USING (user_id = auth.uid());

-- Users can update their own sessions
CREATE POLICY "Users can update own sessions" ON sessions
    FOR UPDATE USING (user_id = auth.uid());

-- ============================================
-- COURSES TABLES
-- ============================================

-- Course Categories
ALTER TABLE course_categories ENABLE ROW LEVEL SECURITY;

-- Anyone can view active categories
CREATE POLICY "View active categories" ON course_categories
    FOR SELECT USING (is_active = true);

-- Courses
ALTER TABLE courses ENABLE ROW LEVEL SECURITY;

-- Anyone can view published courses
CREATE POLICY "View published courses" ON courses
    FOR SELECT USING (is_published = true AND status = 'published');

-- Instructors can view their own courses
CREATE POLICY "Instructors view own courses" ON courses
    FOR SELECT USING (instructor_id = auth.uid());

-- Instructors can update their own courses
CREATE POLICY "Instructors update own courses" ON courses
    FOR UPDATE USING (instructor_id = auth.uid());

-- Instructors can insert courses
CREATE POLICY "Instructors can create courses" ON courses
    FOR INSERT WITH CHECK (instructor_id = auth.uid());

-- Course Sections
ALTER TABLE course_sections ENABLE ROW LEVEL SECURITY;

-- View sections of published courses
CREATE POLICY "View published course sections" ON course_sections
    FOR SELECT USING (
        is_published = true AND
        course_id IN (
            SELECT id FROM courses 
            WHERE is_published = true AND status = 'published'
        )
    );

-- Instructors can manage their course sections
CREATE POLICY "Instructors manage own course sections" ON course_sections
    FOR ALL USING (
        course_id IN (
            SELECT id FROM courses 
            WHERE instructor_id = auth.uid()
        )
    );

-- Note: Lessons table doesn't exist yet in this version

-- ============================================
-- ENROLLMENTS TABLES
-- ============================================

-- Enrollments
ALTER TABLE enrollments ENABLE ROW LEVEL SECURITY;

-- Users can view their own enrollments
CREATE POLICY "Users view own enrollments" ON enrollments
    FOR SELECT USING (user_id = auth.uid());

-- Users can update their own enrollments
CREATE POLICY "Users update own enrollments" ON enrollments
    FOR UPDATE USING (user_id = auth.uid());

-- Instructors can view enrollments for their courses
CREATE POLICY "Instructors view course enrollments" ON enrollments
    FOR SELECT USING (
        course_id IN (
            SELECT id FROM courses 
            WHERE instructor_id = auth.uid()
        )
    );

-- Note: Lesson Progress table doesn't exist yet in this version

-- Course Reviews
ALTER TABLE course_reviews ENABLE ROW LEVEL SECURITY;

-- Anyone can view verified reviews
CREATE POLICY "View verified reviews" ON course_reviews
    FOR SELECT USING (is_verified = true);

-- Users can manage their own reviews
CREATE POLICY "Users manage own reviews" ON course_reviews
    FOR ALL USING (
        enrollment_id IN (
            SELECT id FROM enrollments 
            WHERE user_id = auth.uid()
        )
    );

-- ============================================
-- MEDIA LIBRARY TABLES
-- ============================================

-- Media Files
ALTER TABLE media_files ENABLE ROW LEVEL SECURITY;

-- Users can view their own media files
CREATE POLICY "Users view own media files" ON media_files
    FOR SELECT USING (user_id = auth.uid());

-- Users can view public media files
CREATE POLICY "View public media files" ON media_files
    FOR SELECT USING (is_public = true);

-- Users can manage their own media files
CREATE POLICY "Users manage own media files" ON media_files
    FOR ALL USING (user_id = auth.uid());

-- Instructors can view media files for their courses
CREATE POLICY "Instructors view course media" ON media_files
    FOR SELECT USING (
        course_id IN (
            SELECT id FROM courses 
            WHERE instructor_id = auth.uid()
        )
    );

-- Upload Sessions
ALTER TABLE upload_sessions ENABLE ROW LEVEL SECURITY;

-- Users can manage their own upload sessions
CREATE POLICY "Users manage own upload sessions" ON upload_sessions
    FOR ALL USING (created_by = auth.uid());

-- ============================================
-- PAYMENTS TABLES
-- ============================================

-- Payment Intents
ALTER TABLE payment_intents ENABLE ROW LEVEL SECURITY;

-- Users can view their own payment intents
CREATE POLICY "Users view own payment intents" ON payment_intents
    FOR SELECT USING (user_id = auth.uid());

-- Payment Transactions
ALTER TABLE payment_transactions ENABLE ROW LEVEL SECURITY;

-- Users can view their own payment transactions (via payment_intent)
CREATE POLICY "Users view own payment transactions" ON payment_transactions
    FOR SELECT USING (
        payment_intent_id IN (
            SELECT id FROM payment_intents 
            WHERE user_id = auth.uid()
        )
    );

-- Payment Refunds
ALTER TABLE payment_refunds ENABLE ROW LEVEL SECURITY;

-- Users can view their own payment refunds (via transaction)
CREATE POLICY "Users view own payment refunds" ON payment_refunds
    FOR SELECT USING (
        transaction_id IN (
            SELECT pt.id FROM payment_transactions pt
            JOIN payment_intents pi ON pt.payment_intent_id = pi.id
            WHERE pi.user_id = auth.uid()
        )
    );

-- Stripe Customers
ALTER TABLE stripe_customers ENABLE ROW LEVEL SECURITY;

-- Users can view their own stripe customer data
CREATE POLICY "Users view own stripe customer" ON stripe_customers
    FOR SELECT USING (user_id = auth.uid());

-- Webhook Events
ALTER TABLE webhook_events ENABLE ROW LEVEL SECURITY;

-- No user policies for webhook events - admin only table

-- ============================================
-- DJANGO SYSTEM TABLES
-- ============================================

-- Django Auth Tables (managed by Django, not Supabase)
ALTER TABLE auth_group ENABLE ROW LEVEL SECURITY;
ALTER TABLE auth_group_permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE auth_permission ENABLE ROW LEVEL SECURITY;
ALTER TABLE auth_user ENABLE ROW LEVEL SECURITY;
ALTER TABLE auth_user_groups ENABLE ROW LEVEL SECURITY;
ALTER TABLE auth_user_user_permissions ENABLE ROW LEVEL SECURITY;

-- Django Content Type
ALTER TABLE django_content_type ENABLE ROW LEVEL SECURITY;

-- Django Migrations
ALTER TABLE django_migrations ENABLE ROW LEVEL SECURITY;

-- Note: Django system tables don't need user policies since they're only accessed
-- by the service role for admin functionality. The service role bypasses RLS by default.

-- ============================================
-- SERVICE ROLE BYPASS POLICIES
-- ============================================
-- Adding explicit policies for service role to ensure Django backend can perform all operations
-- Note: Service role bypasses RLS by default, but these policies make operations more explicit

-- Allow service role to perform all operations on all tables
-- This ensures your Django backend can fully manage all data

-- Accounts tables
CREATE POLICY "service_role_user_profiles" ON user_profiles
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_roles" ON roles
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_user_roles" ON user_roles
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_sessions" ON sessions
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Courses tables
CREATE POLICY "service_role_course_categories" ON course_categories
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_courses" ON courses
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_course_sections" ON course_sections
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Enrollments tables
CREATE POLICY "service_role_enrollments" ON enrollments
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_course_reviews" ON course_reviews
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Media tables
CREATE POLICY "service_role_media_files" ON media_files
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_upload_sessions" ON upload_sessions
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Payment tables
CREATE POLICY "service_role_payment_intents" ON payment_intents
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_payment_transactions" ON payment_transactions
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_payment_refunds" ON payment_refunds
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_stripe_customers" ON stripe_customers
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_webhook_events" ON webhook_events
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Django system tables
CREATE POLICY "service_role_auth_group" ON auth_group
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_auth_group_permissions" ON auth_group_permissions
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_auth_permission" ON auth_permission
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_auth_user" ON auth_user
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_auth_user_groups" ON auth_user_groups
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_auth_user_user_permissions" ON auth_user_user_permissions
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_django_content_type" ON django_content_type
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_django_migrations" ON django_migrations
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- ============================================
-- HELPER FUNCTIONS (Optional)
-- ============================================

-- Function to check if user is an instructor
CREATE OR REPLACE FUNCTION is_instructor(user_id uuid)
RETURNS boolean AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM user_roles ur
        JOIN roles r ON ur.role_id = r.id
        WHERE ur.user_id = user_id 
        AND r.name = 'instructor'
        AND r.is_active = true
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to check if user is enrolled in course
CREATE OR REPLACE FUNCTION is_enrolled_in_course(user_id uuid, course_id uuid)
RETURNS boolean AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM enrollments
        WHERE user_id = user_id 
        AND course_id = course_id
        AND status = 'active'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- NOTES
-- ============================================
-- 1. These policies provide basic RLS protection
-- 2. Adjust policies based on your specific business requirements
-- 3. Consider adding more granular policies for different user roles
-- 4. Test thoroughly in development before applying to production
-- 5. Remember that service role key bypasses RLS