"""
Django management command to set up default roles and permissions.
"""
from django.core.management.base import BaseCommand
from accounts.models import Role
from accounts.permissions import RoleConstants


class Command(BaseCommand):
    help = 'Set up default roles and permissions for the application'

    def handle(self, *args, **options):
        self.stdout.write('Setting up default roles and permissions...')
        
        default_roles = RoleConstants.get_default_roles()
        created_count = 0
        updated_count = 0
        
        for role_name, role_config in default_roles.items():
            role, created = Role.objects.get_or_create(
                name=role_name,
                defaults={
                    'description': role_config['description'],
                    'permissions': role_config['permissions'],
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created role: {role_name}')
                )
            else:
                # Update existing role with latest permissions
                role.description = role_config['description']
                role.permissions = role_config['permissions']
                role.is_active = True
                role.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'🔄 Updated role: {role_name}')
                )
        
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Role setup complete! Created: {created_count}, Updated: {updated_count}'
            )
        )
        
        # Display role summary
        self.stdout.write('')
        self.stdout.write('Role Summary:')
        for role_name, role_config in default_roles.items():
            permission_count = len(role_config['permissions'])
            self.stdout.write(f'  {role_name}: {permission_count} permissions')
            self.stdout.write(f'    Description: {role_config["description"]}')
        
        self.stdout.write('')
        self.stdout.write('Next steps:')
        self.stdout.write('1. Assign roles to users using: python manage.py assign_role <user_email> <role_name>')
        self.stdout.write('2. Use permission classes in your views to enforce access control')