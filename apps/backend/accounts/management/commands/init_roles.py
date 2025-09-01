"""
Management command to initialize default roles in the database.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models import Role
from accounts.permissions import RoleConstants, PermissionConstants


class Command(BaseCommand):
    help = 'Initialize default roles with their permissions'

    def handle(self, *args, **options):
        """Create or update default roles"""
        
        default_roles = RoleConstants.get_default_roles()
        
        with transaction.atomic():
            for role_name, role_config in default_roles.items():
                role, created = Role.objects.update_or_create(
                    name=role_name,
                    defaults={
                        'description': role_config['description'],
                        'permissions': role_config['permissions'],
                        'is_active': True
                    }
                )
                
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'Created role: {role_name}')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f'Updated role: {role_name}')
                    )
        
        self.stdout.write(
            self.style.SUCCESS('Successfully initialized all default roles')
        )
        
        # Display role summary
        self.stdout.write('\nRole Summary:')
        for role_name, role_config in default_roles.items():
            self.stdout.write(f'\n{role_name}:')
            self.stdout.write(f'  Description: {role_config["description"]}')
            self.stdout.write(f'  Permissions: {len(role_config["permissions"])} permissions')