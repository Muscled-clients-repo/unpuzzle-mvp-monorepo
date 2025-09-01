"""
Django management command to set up automatic auth.users sync with user_profiles.
"""
import os
from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings


class Command(BaseCommand):
    help = 'Set up automatic sync between auth.users and user_profiles using PostgreSQL triggers'

    def handle(self, *args, **options):
        self.stdout.write('Setting up automatic auth sync...')
        
        # Read the SQL script
        sql_file_path = os.path.join(settings.BASE_DIR, 'sql', 'setup_auth_sync.sql')
        
        try:
            with open(sql_file_path, 'r') as f:
                sql_script = f.read()
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f'SQL file not found: {sql_file_path}')
            )
            return
        
        # Execute the SQL script
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql_script)
                
            self.stdout.write(
                self.style.SUCCESS('✅ Auth sync triggers set up successfully!')
            )
            self.stdout.write('The following triggers are now active:')
            self.stdout.write('  - on_auth_user_created: Creates user_profiles when users sign up')
            self.stdout.write('  - on_auth_user_updated: Updates user_profiles when users are updated')
            self.stdout.write('  - on_auth_user_deleted: Soft-deletes user_profiles when users are deleted')
            self.stdout.write('')
            self.stdout.write('Any existing auth.users have been synced to user_profiles.')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to set up auth sync: {e}')
            )
            raise