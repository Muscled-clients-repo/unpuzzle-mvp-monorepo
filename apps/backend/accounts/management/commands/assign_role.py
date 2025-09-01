"""
Django management command to assign roles to users.
"""
from django.core.management.base import BaseCommand, CommandError
from accounts.models import UserProfile, Role
from accounts.permissions import PermissionService


class Command(BaseCommand):
    help = 'Assign a role to a user'

    def add_arguments(self, parser):
        parser.add_argument(
            'user_email',
            type=str,
            help='Email of the user to assign the role to'
        )
        parser.add_argument(
            'role_name',
            type=str,
            help='Name of the role to assign'
        )
        parser.add_argument(
            '--assigned-by',
            type=str,
            help='Email of the user assigning the role (optional)'
        )

    def handle(self, *args, **options):
        user_email = options['user_email']
        role_name = options['role_name']
        assigned_by_email = options.get('assigned_by')
        
        try:
            # Get the user profile
            user_profile = UserProfile.objects.get(email=user_email)
            
            # Get assigned_by user ID if provided
            assigned_by_id = None
            if assigned_by_email:
                try:
                    assigned_by_profile = UserProfile.objects.get(email=assigned_by_email)
                    assigned_by_id = str(assigned_by_profile.supabase_user_id)
                except UserProfile.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'Warning: Assigned-by user "{assigned_by_email}" not found')
                    )
            
            # Check if role exists
            try:
                role = Role.objects.get(name=role_name)
            except Role.DoesNotExist:
                available_roles = Role.objects.filter(is_active=True).values_list('name', flat=True)
                raise CommandError(
                    f'Role "{role_name}" does not exist. Available roles: {list(available_roles)}'
                )
            
            # Assign the role
            success = PermissionService.assign_role_to_user(
                str(user_profile.supabase_user_id),
                role_name,
                assigned_by_id
            )
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Successfully assigned role "{role_name}" to user "{user_email}"'
                    )
                )
                
                # Show user's permissions
                permissions = PermissionService.get_user_permissions(str(user_profile.supabase_user_id))
                self.stdout.write(f'User now has {len(permissions)} permissions:')
                for perm in sorted(permissions):
                    self.stdout.write(f'  - {perm}')
            else:
                raise CommandError('Failed to assign role (user may already have this role)')
                
        except UserProfile.DoesNotExist:
            raise CommandError(f'User with email "{user_email}" does not exist')