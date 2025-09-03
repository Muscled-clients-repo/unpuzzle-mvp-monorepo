# Generated migration to optimize database indexes
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='userprofile',
            index=models.Index(fields=['supabase_user_id'], name='idx_supabase_user_id'),
        ),
        migrations.AddIndex(
            model_name='userrole',
            index=models.Index(fields=['user', 'role'], name='idx_user_role'),
        ),
        migrations.AddIndex(
            model_name='role',
            index=models.Index(fields=['name', 'is_active'], name='idx_role_active'),
        ),
    ]