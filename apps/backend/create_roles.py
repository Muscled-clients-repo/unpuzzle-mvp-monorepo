#!/usr/bin/env python
"""
Script to create default roles in the database
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from accounts.models import Role

def create_roles():
    """Create default student and instructor roles"""
    
    # Create Student role
    student_role, created = Role.objects.get_or_create(
        name='student',
        defaults={
            'description': 'Student role with access to enrolled courses and learning materials',
            'permissions': [
                "course:read",
                "course:list",
                "enrollment:create",
                "enrollment:read",
                "media:read"
            ],
            'is_active': True
        }
    )
    
    if created:
        print(f"✓ Created Student role: {student_role}")
    else:
        print(f"✓ Student role already exists: {student_role}")
        # Update permissions if role exists
        student_role.permissions = [
            "course:read",
            "course:list",
            "enrollment:create",
            "enrollment:read",
            "media:read"
        ]
        student_role.save()
        print("  Updated student permissions")
    
    # Create Instructor role
    instructor_role, created = Role.objects.get_or_create(
        name='instructor',
        defaults={
            'description': 'Instructor role with permissions to create and manage courses',
            'permissions': [
                "course:create",
                "course:read",
                "course:update",
                "course:delete",
                "course:list",
                "course:publish",
                "enrollment:read",
                "enrollment:list",
                "media:upload",
                "media:read",
                "media:update",
                "media:delete",
                "media:list"
            ],
            'is_active': True
        }
    )
    
    if created:
        print(f"✓ Created Instructor role: {instructor_role}")
    else:
        print(f"✓ Instructor role already exists: {instructor_role}")
        # Update permissions if role exists
        instructor_role.permissions = [
            "course:create",
            "course:read",
            "course:update",
            "course:delete",
            "course:list",
            "course:publish",
            "enrollment:read",
            "enrollment:list",
            "media:upload",
            "media:read",
            "media:update",
            "media:delete",
            "media:list"
        ]
        instructor_role.save()
        print("  Updated instructor permissions")
    
    print("\n✅ Roles created/updated successfully!")

if __name__ == "__main__":
    create_roles()