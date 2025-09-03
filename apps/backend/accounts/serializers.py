"""
Serializers for authentication and user management.
"""
from rest_framework import serializers
from .models import UserProfile


class SignUpSerializer(serializers.Serializer):
    """Serializer for user sign up"""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True, min_length=6)
    full_name = serializers.CharField(required=False, allow_blank=True)
    # Accept firstname and lastname from frontend (both camelCase and lowercase)
    firstname = serializers.CharField(required=False, allow_blank=True)
    lastname = serializers.CharField(required=False, allow_blank=True)
    firstName = serializers.CharField(required=False, allow_blank=True)
    lastName = serializers.CharField(required=False, allow_blank=True)
    role = serializers.ChoiceField(
        choices=['student', 'instructor'], 
        default='student',
        required=False,
        help_text='User role (student or instructor)'
    )
    
    def validate(self, data):
        """Combine firstname and lastname into full_name if provided"""
        # Handle both camelCase and lowercase variants
        firstname = (
            data.get('firstName', '') or 
            data.get('firstname', '')
        ).strip()
        
        lastname = (
            data.get('lastName', '') or 
            data.get('lastname', '')
        ).strip()
        
        # If firstname/lastname provided, combine them into full_name
        if firstname or lastname:
            combined_name = f"{firstname} {lastname}".strip()
            data['full_name'] = combined_name
            print(f"[SERIALIZER DEBUG] Combined name: '{firstname}' + '{lastname}' = '{combined_name}'")
        
        return data
    
    def validate_email(self, value):
        """Check if email already exists in UserProfile"""
        if UserProfile.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("Email already registered")
        return value.lower()


class SignInSerializer(serializers.Serializer):
    """Serializer for user sign in"""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    
    def validate_email(self, value):
        return value.lower()


class RefreshTokenSerializer(serializers.Serializer):
    """Serializer for token refresh"""
    refresh_token = serializers.CharField(required=True)


class PasswordResetSerializer(serializers.Serializer):
    """Serializer for password reset request"""
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        return value.lower()


class UserProfileSerializer(serializers.ModelSerializer):
    """Optimized serializer for user profile (avoids database queries from properties)"""
    
    class Meta:
        model = UserProfile
        fields = [
            'supabase_user_id',
            'email',
            'username',
            'full_name',
            'display_name',
            'avatar_url',
            'bio',
            'status',
            'phone_number',
            'timezone',
            'language',
            'last_login',
            'email_verified',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'supabase_user_id',
            'email',
            'email_verified',
            'created_at',
            'updated_at'
        ]
    
    def to_representation(self, instance):
        """Override to prevent property method calls that cause database queries"""
        # Get the standard fields without property methods
        data = super().to_representation(instance)
        
        # Add subscription data only if explicitly prefetched to avoid queries
        # This prevents the property methods from being called
        if hasattr(instance, '_prefetched_objects_cache') or hasattr(instance, 'subscription'):
            try:
                if hasattr(instance, 'subscription') and instance.subscription:
                    # Only access if already loaded to avoid database queries
                    subscription = instance.subscription
                    data['subscription_status'] = subscription.status
                    data['subscription_plan'] = subscription.plan_id
                    if hasattr(subscription, 'plan') and subscription.plan:
                        data['subscription_display_name'] = subscription.plan.display_name
                    else:
                        data['subscription_display_name'] = 'Free Plan'
                else:
                    data['subscription_status'] = 'free'
                    data['subscription_plan'] = 'free' 
                    data['subscription_display_name'] = 'Free Plan'
            except:
                # Fallback to free if any error occurs
                data['subscription_status'] = 'free'
                data['subscription_plan'] = 'free'
                data['subscription_display_name'] = 'Free Plan'
        else:
            # Default values when not prefetched
            data['subscription_status'] = 'free'
            data['subscription_plan'] = 'free'
            data['subscription_display_name'] = 'Free Plan'
            
        return data


class UpdateProfileSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile"""
    
    class Meta:
        model = UserProfile
        fields = [
            'username',
            'full_name',
            'display_name',
            'avatar_url',
            'bio',
            'phone_number',
            'timezone',
            'language'
        ]
        
    def validate_username(self, value):
        """Check if username is unique"""
        if value:
            instance = self.instance
            if UserProfile.objects.filter(username=value).exclude(pk=instance.pk if instance else None).exists():
                raise serializers.ValidationError("Username already taken")
        return value


class OAuthProviderSerializer(serializers.Serializer):
    """Simple serializer for OAuth provider validation"""
    provider = serializers.CharField(required=True)
    redirect_url = serializers.URLField(required=False, allow_blank=True)