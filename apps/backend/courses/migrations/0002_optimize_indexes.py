# Generated migration to add database indexes for better query performance
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0001_initial'),  # Update this to your latest migration
    ]

    operations = [
        # Index for filtering published and active courses (most common query)
        migrations.AddIndex(
            model_name='course',
            index=models.Index(
                fields=['is_published', 'status', '-created_at'],
                name='idx_published_status_created'
            ),
        ),
        
        # Index for instructor's courses
        migrations.AddIndex(
            model_name='course',
            index=models.Index(
                fields=['instructor', '-created_at'],
                name='idx_instructor_courses'
            ),
        ),
        
        # Index for category filtering
        migrations.AddIndex(
            model_name='course',
            index=models.Index(
                fields=['category', 'is_published'],
                name='idx_category_published'
            ),
        ),
        
        # Index for price filtering
        migrations.AddIndex(
            model_name='course',
            index=models.Index(
                fields=['is_free', 'price'],
                name='idx_free_price'
            ),
        ),
        
        # Index for rating sorting
        migrations.AddIndex(
            model_name='course',
            index=models.Index(
                fields=['-rating_average', '-rating_count'],
                name='idx_rating'
            ),
        ),
        
        # Index for sections
        migrations.AddIndex(
            model_name='coursesection',
            index=models.Index(
                fields=['course', 'is_published', 'order'],
                name='idx_course_section_order'
            ),
        ),
    ]