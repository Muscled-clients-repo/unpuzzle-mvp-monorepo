"""
Management command to generate subtitles for existing videos that don't have them
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from media_library.models import MediaFile
from ai_assistant.tasks import generate_video_subtitles_task, bulk_generate_subtitles_task


class Command(BaseCommand):
    help = 'Generate subtitles for existing videos that do not have them'

    def add_arguments(self, parser):
        parser.add_argument(
            '--video-id',
            type=str,
            help='Generate subtitles for a specific video ID'
        )
        parser.add_argument(
            '--user-id',
            type=str,
            help='Generate subtitles for videos from a specific user'
        )
        parser.add_argument(
            '--course-id',
            type=str,
            help='Generate subtitles for videos from a specific course'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Number of videos to process in each batch (default: 10)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show which videos would be processed without actually processing them'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Regenerate subtitles even if they already exist'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🎬 Starting subtitle generation for existing videos...'))

        # Build queryset based on options
        queryset = MediaFile.objects.filter(
            file_type='video',
            cdn_url__isnull=False,
            processing_status='completed'
        ).exclude(
            cdn_url__exact=''
        )

        # Filter by specific video ID
        if options['video_id']:
            try:
                queryset = queryset.filter(id=options['video_id'])
            except ValueError:
                raise CommandError(f"Invalid video ID: {options['video_id']}")

        # Filter by user ID
        if options['user_id']:
            queryset = queryset.filter(user__supabase_user_id=options['user_id'])

        # Filter by course ID
        if options['course_id']:
            queryset = queryset.filter(course_id=options['course_id'])

        # Filter out videos that already have subtitles (unless force is used)
        if not options['force']:
            queryset = queryset.filter(
                models.Q(subtitles__isnull=True) | models.Q(subtitles__exact='')
            )

        videos = list(queryset.order_by('created_at'))

        if not videos:
            self.stdout.write(self.style.WARNING('📭 No videos found matching the criteria'))
            return

        self.stdout.write(f'📊 Found {len(videos)} video(s) to process:')
        
        for video in videos[:10]:  # Show first 10 for preview
            status = '✅ Has subtitles' if video.subtitles else '❌ No subtitles'
            self.stdout.write(f'   • {video.filename} ({video.id}) - {status}')
        
        if len(videos) > 10:
            self.stdout.write(f'   ... and {len(videos) - 10} more videos')

        if options['dry_run']:
            self.stdout.write(self.style.SUCCESS('🔍 Dry run completed - no videos were processed'))
            return

        # Confirm before processing
        if not options['force'] and not options['video_id']:
            confirm = input(f'\nProcess {len(videos)} video(s)? [y/N]: ')
            if confirm.lower() not in ['y', 'yes']:
                self.stdout.write(self.style.WARNING('❌ Operation cancelled'))
                return

        # Process videos
        batch_size = options['batch_size']
        processed = 0
        queued = 0

        try:
            if len(videos) == 1:
                # Single video processing
                video = videos[0]
                self.stdout.write(f'🎯 Processing single video: {video.filename}')
                
                task = generate_video_subtitles_task.apply_async(
                    args=[str(video.id)],
                    countdown=5
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Queued subtitle generation for {video.filename} (Task ID: {task.id})')
                )
                queued = 1
                
            else:
                # Batch processing
                for i in range(0, len(videos), batch_size):
                    batch = videos[i:i + batch_size]
                    video_ids = [str(video.id) for video in batch]
                    
                    self.stdout.write(f'📦 Processing batch {i//batch_size + 1}: {len(batch)} videos')
                    
                    # Queue bulk generation task
                    task = bulk_generate_subtitles_task.apply_async(
                        args=[video_ids],
                        countdown=10 + (i // batch_size) * 30  # Stagger batches
                    )
                    
                    for video in batch:
                        self.stdout.write(f'   • {video.filename} ({video.id})')
                    
                    queued += len(batch)
                    processed += 1
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Batch {processed} queued (Task ID: {task.id})')
                    )

            # Summary
            self.stdout.write(
                self.style.SUCCESS(f'\n🎉 Successfully queued subtitle generation for {queued} video(s)')
            )
            self.stdout.write('📋 Task Details:')
            self.stdout.write('   • Tasks are processed asynchronously by Celery workers')
            self.stdout.write('   • Check video processing_metadata for status updates')
            self.stdout.write('   • Completed subtitles will appear in MediaFile.subtitles field')
            
            if queued > 1:
                estimated_time = (queued * 2)  # Rough estimate: 2 minutes per video
                self.stdout.write(f'   • Estimated completion time: ~{estimated_time} minutes')

        except Exception as e:
            raise CommandError(f'Failed to queue subtitle generation: {e}')


# Fix the import for Q objects
from django.db import models