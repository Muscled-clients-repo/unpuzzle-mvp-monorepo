"""
Course management serializers.
"""
from rest_framework import serializers
from django.utils import timezone
from accounts.serializers import UserProfileSerializer
from .models import (
    Course, CourseSection, CourseCategory
)
from enrollments.models import Enrollment, CourseReview
from accounts.models import Session


class CourseCategorySerializer(serializers.ModelSerializer):
    """Serializer for course categories"""
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = CourseCategory
        fields = [
            'id', 'name', 'slug', 'description', 'icon', 
            'order', 'is_active', 'children'
        ]
    
    def get_children(self, obj):
        if hasattr(obj, 'children'):
            return CourseCategorySerializer(obj.children.filter(is_active=True), many=True).data
        return []


class CourseSectionSerializer(serializers.ModelSerializer):
    """Serializer for course sections"""
    media_files_count = serializers.SerializerMethodField()
    
    class Meta:
        model = CourseSection
        fields = [
            'id', 'title', 'description', 'order', 'is_published',
            'is_preview', 'media_files_count', 'created_at', 'updated_at'
        ]
    
    def get_media_files_count(self, obj):
        return obj.media_files.count()


class InstructorSerializer(serializers.ModelSerializer):
    """Simplified instructor info serializer"""
    avatar_url = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfileSerializer.Meta.model
        fields = [
            'supabase_user_id', 'full_name', 'display_name', 'avatar_url', 
            'bio', 'email_verified', 'created_at'
        ]
    
    def get_avatar_url(self, obj):
        """Return avatar URL or fallback to default avatar"""
        if obj.avatar_url:
            return obj.avatar_url
        
        # Generate fallback avatar using initials
        name = self.get_display_name(obj)
        if name and name.strip():
            # Use initials for avatar generation service (like UI Avatars)
            initials = ''.join(word[0].upper() for word in name.split()[:2] if word)
            if initials:
                return f"https://ui-avatars.com/api/?name={initials}&background=6366f1&color=ffffff&size=128"
        
        # Ultimate fallback
        return "https://ui-avatars.com/api/?name=User&background=6366f1&color=ffffff&size=128"
    
    def get_display_name(self, obj):
        """Return display name with fallbacks"""
        if obj.display_name and obj.display_name.strip():
            return obj.display_name
        elif obj.full_name and obj.full_name.strip():
            return obj.full_name
        else:
            return "Instructor"


class CourseListSerializer(serializers.ModelSerializer):
    """Serializer for course list views (public) - OPTIMIZED"""
    instructor = InstructorSerializer(read_only=True)
    category = CourseCategorySerializer(read_only=True)
    is_enrolled = serializers.SerializerMethodField()
    sections_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'short_description', 'thumbnail',
            'instructor', 'price', 'discount_price', 'currency', 'is_free',
            'duration', 'difficulty', 'language', 'category', 'tags',
            'enrollment_count', 'rating_average', 'rating_count',
            'is_published', 'published_at', 'created_at', 'updated_at',
            'is_enrolled', 'sections_count'
        ]
    
    def get_is_enrolled(self, obj):
        """Check if current user is enrolled (OPTIMIZED)"""
        # First check if we have the annotated field from the optimized query
        if hasattr(obj, 'user_is_enrolled'):
            return obj.user_is_enrolled
        
        # Fallback to database query if annotation is not present
        request = self.context.get('request')
        if request and hasattr(request, 'user_id'):
            # This should rarely be hit due to the annotation in the view
            return Enrollment.objects.filter(
                user__supabase_user_id=request.user_id,
                course=obj,
                status='active'
            ).exists()
        return False
    
    def get_sections_count(self, obj):
        """Get sections count (OPTIMIZED)"""
        # First check if we have the annotated field from the optimized query
        if hasattr(obj, 'published_sections_count'):
            return obj.published_sections_count
        
        # Fallback to counting prefetched sections if available
        if hasattr(obj, '_prefetched_objects_cache') and 'sections' in obj._prefetched_objects_cache:
            return len([s for s in obj.sections.all() if s.is_published])
        
        # Last resort: database query (should rarely be hit)
        return obj.sections.filter(is_published=True).count()


class CourseDetailSerializer(serializers.ModelSerializer):
    """Detailed course serializer with sections and lessons"""
    instructor = InstructorSerializer(read_only=True)
    category = CourseCategorySerializer(read_only=True)
    sections = CourseSectionSerializer(many=True, read_only=True)
    is_enrolled = serializers.SerializerMethodField()
    enrollment_info = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'description', 'short_description',
            'thumbnail', 'preview_video_url', 'instructor', 'price',
            'discount_price', 'currency', 'is_free', 'duration', 'difficulty',
            'language', 'category', 'tags', 'prerequisites', 'learning_outcomes',
            'target_audience', 'course_structure', 'enrollment_count',
            'completion_count', 'rating_average', 'rating_count', 'status',
            'is_published', 'published_at', 'sections', 'is_enrolled',
            'enrollment_info', 'progress', 'metadata', 'seo_metadata',
            'created_at', 'updated_at'
        ]
    
    def get_is_enrolled(self, obj):
        """Check if current user is enrolled"""
        request = self.context.get('request')
        if request and hasattr(request, 'user_id'):
            return Enrollment.objects.filter(
                user__supabase_user_id=request.user_id,
                course=obj,
                status='active'
            ).exists()
        return False
    
    def get_enrollment_info(self, obj):
        """Get enrollment information for current user"""
        request = self.context.get('request')
        if request and hasattr(request, 'user_id'):
            try:
                enrollment = Enrollment.objects.get(
                    user__supabase_user_id=request.user_id,
                    course=obj
                )
                return EnrollmentSerializer(enrollment).data
            except Enrollment.DoesNotExist:
                pass
        return None
    
    def get_progress(self, obj):
        """Get course progress for current user"""
        request = self.context.get('request')
        if request and hasattr(request, 'user_id'):
            try:
                enrollment = Enrollment.objects.get(
                    user__supabase_user_id=request.user_id,
                    course=obj,
                    status='active'
                )
                return {
                    'progress_percentage': enrollment.progress_percentage,
                    'last_accessed_at': enrollment.last_accessed_at
                }
            except Enrollment.DoesNotExist:
                pass
        return None


class CourseCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating courses"""
    category = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    class Meta:
        model = Course
        fields = [
            'title', 'description', 'short_description', 'thumbnail',
            'preview_video_url', 'price', 'discount_price', 'currency',
            'is_free', 'duration', 'difficulty', 'language', 'category',
            'tags', 'prerequisites', 'learning_outcomes', 'target_audience',
            'course_structure', 'metadata', 'seo_metadata'
        ]
    
    def validate_category(self, value):
        """Validate and get or create category"""
        if not value:
            return None
            
        from django.utils.text import slugify
        from .models import CourseCategory
        
        # If it's already a UUID, try to get the category
        try:
            import uuid
            uuid.UUID(str(value))
            try:
                return CourseCategory.objects.get(id=value)
            except CourseCategory.DoesNotExist:
                raise serializers.ValidationError(f"Category with ID {value} does not exist")
        except ValueError:
            # Not a UUID, treat as category name/slug
            pass
        
        # Try to find by slug first, then by name
        slug = slugify(value)
        try:
            return CourseCategory.objects.get(slug=slug)
        except CourseCategory.DoesNotExist:
            try:
                return CourseCategory.objects.get(name__iexact=value)
            except CourseCategory.DoesNotExist:
                # Create new category
                category = CourseCategory.objects.create(
                    name=value.title(),
                    slug=slug,
                    description=f"Automatically created category for {value}"
                )
                return category
    
    def create(self, validated_data):
        # Set instructor to current user
        request = self.context.get('request')
        if request and hasattr(request, 'user_id'):
            from accounts.models import UserProfile
            try:
                instructor = UserProfile.objects.get(supabase_user_id=request.user_id)
                validated_data['instructor'] = instructor
            except UserProfile.DoesNotExist:
                raise serializers.ValidationError("Instructor profile not found")
        
        return Course.objects.create(**validated_data)


class EnrollmentSerializer(serializers.ModelSerializer):
    """Serializer for enrollments"""
    course = CourseListSerializer(read_only=True)
    user = InstructorSerializer(read_only=True)
    
    class Meta:
        model = Enrollment
        fields = [
            'id', 'user', 'course', 'status', 'progress_percentage',
            'enrolled_at', 'completed_at', 'last_accessed_at', 
            'payment_method', 'amount_paid', 'coupon_code'
        ]


class EnrollmentCreateSerializer(serializers.Serializer):
    """Serializer for creating enrollments"""
    payment_method = serializers.CharField(max_length=50, required=False)
    coupon_code = serializers.CharField(max_length=50, required=False)
    
    def validate(self, data):
        # Add any enrollment validation logic here
        return data




class CourseReviewSerializer(serializers.ModelSerializer):
    """Serializer for course reviews"""
    user = InstructorSerializer(read_only=True)
    
    class Meta:
        model = CourseReview
        fields = [
            'id', 'user', 'rating', 'title', 'comment', 'pros', 'cons',
            'helpful_count', 'unhelpful_count', 'is_verified', 'is_featured',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'helpful_count', 'unhelpful_count', 'is_verified', 'is_featured']


class CourseReviewCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating course reviews"""
    
    class Meta:
        model = CourseReview
        fields = ['rating', 'title', 'comment', 'pros', 'cons']
    
    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value




class SessionSerializer(serializers.ModelSerializer):
    """Serializer for user sessions"""
    
    class Meta:
        model = Session
        fields = [
            'id', 'session_id', 'device_info', 'ip_address', 'location',
            'is_active', 'last_activity', 'expires_at', 'created_at'
        ]
        read_only_fields = ['session_id', 'ip_address', 'created_at']


class CourseSectionCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating course sections"""
    
    class Meta:
        model = CourseSection
        fields = [
            'title', 'description', 'order', 'is_published', 'is_preview'
        ]


class CourseAnalyticsSerializer(serializers.Serializer):
    """Serializer for course analytics data"""
    enrollments = serializers.IntegerField()
    completion_rate = serializers.FloatField()
    avg_progress = serializers.FloatField()
    revenue_total = serializers.DecimalField(max_digits=10, decimal_places=2)
    revenue_this_month = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_students = serializers.IntegerField()
    student_engagement = serializers.DictField()
    top_performers = serializers.ListField()
    struggling_students = serializers.ListField()


class CourseLearningSerializer(serializers.ModelSerializer):
    """Serializer for course learning page with sections"""
    instructor = InstructorSerializer(read_only=True)
    category = CourseCategorySerializer(read_only=True)
    sections = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'short_description', 'thumbnail',
            'instructor', 'category', 'difficulty', 'duration', 'sections'
        ]
    
    def get_sections(self, obj):
        """Get published sections with media count"""
        sections = obj.sections.filter(is_published=True).order_by('order')
        return CourseSectionLearningSerializer(sections, many=True).data


class CourseSectionLearningSerializer(serializers.ModelSerializer):
    """Serializer for course sections in learning context"""
    media_count = serializers.SerializerMethodField()
    
    class Meta:
        model = CourseSection
        fields = [
            'id', 'title', 'description', 'order', 'is_published', 
            'is_preview', 'media_count'
        ]
    
    def get_media_count(self, obj):
        """Get count of media files in this section"""
        return obj.media_files.filter(processing_status='completed').count()


class EnrollmentProgressSerializer(serializers.ModelSerializer):
    """Serializer for enrollment with progress information"""
    
    class Meta:
        model = Enrollment
        fields = [
            'enrolled_at', 'progress_percentage', 'lessons_completed', 
            'total_lessons', 'last_accessed_at', 'started_at'
        ]


class SectionContentSerializer(serializers.ModelSerializer):
    """Serializer for section content with media files"""
    media_files = serializers.SerializerMethodField()
    
    class Meta:
        model = CourseSection
        fields = [
            'id', 'title', 'description', 'order', 'course', 'media_files'
        ]
    
    def get_media_files(self, obj):
        """Get media files for this section with user progress"""
        from media_library.serializers import MediaFileSerializer
        
        media_files = obj.media_files.filter(
            processing_status='completed'
        ).order_by('order', 'created_at')
        
        return MediaFileSerializer(media_files, many=True).data