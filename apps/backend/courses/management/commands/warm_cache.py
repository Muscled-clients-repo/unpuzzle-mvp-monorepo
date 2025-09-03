"""
Management command to warm course caches.
Can be run on server startup or via cron job.
"""
from django.core.management.base import BaseCommand
from courses.utils import warm_course_cache
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Warms course caches to improve initial load performance'

    def handle(self, *args, **options):
        self.stdout.write('Starting cache warming...')
        
        try:
            warm_course_cache()
            self.stdout.write(self.style.SUCCESS('Successfully warmed course caches'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error warming cache: {e}'))
            logger.error(f"Cache warming failed: {e}")