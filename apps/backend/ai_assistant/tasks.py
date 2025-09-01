"""
Celery tasks for AI assistant functionality
"""
import logging
from celery import shared_task
from django.utils import timezone
from media_library.models import MediaFile, ProcessingStatus
from .services.subtitle_generation_service import subtitle_generation_service

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_video_subtitles_task(self, video_id: str):
    """
    Background task to generate subtitles for a video after upload
    """
    try:
        logger.info(f"Starting subtitle generation task for video {video_id}")
        
        # Get the media file
        try:
            media_file = MediaFile.objects.get(id=video_id, file_type='video')
        except MediaFile.DoesNotExist:
            logger.error(f"MediaFile {video_id} not found")
            return {'success': False, 'error': 'Video not found'}
        
        # Check if video has CDN URL
        if not media_file.cdn_url:
            logger.warning(f"Video {video_id} has no CDN URL, skipping subtitle generation")
            return {'success': False, 'error': 'Video CDN URL not available'}
        
        # Check if subtitles already exist
        if media_file.subtitles:
            logger.info(f"Video {video_id} already has subtitles, skipping generation")
            return {'success': True, 'message': 'Subtitles already exist', 'skipped': True}
        
        # Update processing metadata to indicate subtitle generation started
        processing_metadata = media_file.processing_metadata or {}
        processing_metadata['subtitle_generation'] = {
            'status': 'in_progress',
            'started_at': timezone.now().isoformat(),
            'task_id': self.request.id
        }
        media_file.processing_metadata = processing_metadata
        media_file.save()
        
        # Generate subtitles
        user_id = str(media_file.user.supabase_user_id)
        result = subtitle_generation_service.generate_subtitles_from_video_sync(
            video_id=video_id,
            video_cdn_url=media_file.cdn_url,
            user_id=user_id
        )
        
        # Update processing metadata with result
        processing_metadata['subtitle_generation'].update({
            'status': 'completed' if result['success'] else 'failed',
            'completed_at': timezone.now().isoformat(),
            'result': result
        })
        media_file.processing_metadata = processing_metadata
        media_file.save()
        
        if result['success']:
            logger.info(f"Subtitle generation completed for video {video_id}: {result['subtitle_url']}")
            return {
                'success': True,
                'video_id': video_id,
                'subtitle_url': result['subtitle_url'],
                'segments_count': result['segments_count']
            }
        else:
            logger.error(f"Subtitle generation failed for video {video_id}: {result['error']}")
            return {
                'success': False,
                'video_id': video_id,
                'error': result['error']
            }
            
    except Exception as e:
        logger.error(f"Subtitle generation task failed for video {video_id}: {e}")
        
        # Update processing metadata with error
        try:
            media_file = MediaFile.objects.get(id=video_id)
            processing_metadata = media_file.processing_metadata or {}
            if 'subtitle_generation' in processing_metadata:
                processing_metadata['subtitle_generation'].update({
                    'status': 'failed',
                    'completed_at': timezone.now().isoformat(),
                    'error': str(e)
                })
                media_file.processing_metadata = processing_metadata
                media_file.save()
        except Exception as save_error:
            logger.error(f"Failed to update processing metadata: {save_error}")
        
        # Retry the task if retries are available
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying subtitle generation for video {video_id} (attempt {self.request.retries + 1})")
            raise self.retry(exc=e)
        
        return {
            'success': False,
            'video_id': video_id,
            'error': f'Task failed after {self.max_retries} retries: {str(e)}'
        }


@shared_task
def cleanup_expired_transcript_references():
    """
    Periodic task to clean up expired transcript references
    """
    try:
        from .services.transcript_service import TranscriptService
        transcript_service = TranscriptService()
        cleaned_count = transcript_service.cleanup_expired_references()
        logger.info(f"Cleaned up {cleaned_count} expired transcript references")
        return {'success': True, 'cleaned_count': cleaned_count}
    except Exception as e:
        logger.error(f"Failed to cleanup expired transcript references: {e}")
        return {'success': False, 'error': str(e)}


@shared_task(bind=True, max_retries=2)
def bulk_generate_subtitles_task(self, video_ids: list):
    """
    Background task to generate subtitles for multiple videos
    """
    try:
        logger.info(f"Starting bulk subtitle generation for {len(video_ids)} videos")
        
        results = []
        for video_id in video_ids:
            try:
                # Call the individual subtitle generation task
                result = generate_video_subtitles_task.apply_async(
                    args=[video_id],
                    countdown=5  # Stagger tasks by 5 seconds
                )
                
                results.append({
                    'video_id': video_id,
                    'task_id': result.id,
                    'queued': True
                })
                
            except Exception as e:
                logger.error(f"Failed to queue subtitle generation for video {video_id}: {e}")
                results.append({
                    'video_id': video_id,
                    'task_id': None,
                    'queued': False,
                    'error': str(e)
                })
        
        successful_queued = sum(1 for r in results if r['queued'])
        logger.info(f"Bulk subtitle generation queued: {successful_queued}/{len(video_ids)} videos")
        
        return {
            'success': True,
            'total_videos': len(video_ids),
            'queued_successfully': successful_queued,
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Bulk subtitle generation task failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }