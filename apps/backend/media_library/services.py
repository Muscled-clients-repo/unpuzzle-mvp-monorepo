"""
Media library services for Django app - equivalent to Flask storage services
"""
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import hashlib
import mimetypes
import uuid
from typing import Optional, Dict, Any, BinaryIO, Tuple, List
from datetime import datetime, timedelta
import logging
import requests
from base64 import b64encode
import subprocess
import json
import tempfile
import os
from urllib.parse import urlparse
from django.conf import settings
from django.utils import timezone
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from .models import MediaFile, UploadSession, ProcessingStatus

logger = logging.getLogger(__name__)


class BackblazeStorageService:
    """
    Backblaze B2 storage service with comprehensive file management
    Uses both S3-compatible API and B2 native API for optimal compatibility
    """
    
    def __init__(self):
        """Initialize Backblaze client with configuration"""
        try:
            # Configure boto3 with SSL and connection settings
            from botocore.config import Config
            
            config = Config(
                region_name='us-west-002',
                retries={
                    'max_attempts': 3,
                    'mode': 'adaptive'
                },
                max_pool_connections=50,
                read_timeout=60,
                connect_timeout=10
            )
            
            self.client = boto3.client(
                's3',
                endpoint_url=f'https://{settings.BACKBLAZE_ENDPOINT}',
                aws_access_key_id=settings.BACKBLAZE_KEY_ID,
                aws_secret_access_key=settings.BACKBLAZE_APPLICATION_KEY,
                config=config
            )
            self.bucket_name = settings.BACKBLAZE_BUCKET_NAME
            self.bucket_id = settings.BACKBLAZE_BUCKET_ID
            self.cdn_base_url = getattr(settings, 'CDN_BASE_URL', None)
            
            # B2 native API credentials
            self.b2_key_id = settings.BACKBLAZE_KEY_ID
            self.b2_app_key = settings.BACKBLAZE_APPLICATION_KEY
            self._b2_auth_data = None
            self._b2_upload_url_cache = None
            
            logger.info(f"Backblaze storage service initialized for bucket: {self.bucket_name} (ID: {self.bucket_id})")
        except Exception as e:
            logger.error(f"Failed to initialize Backblaze client: {e}")
            raise
    
    def _generate_storage_key(self, user_id: str, filename: str, file_type: str = "video") -> str:
        """Generate unique storage key for file"""
        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        file_hash = hashlib.md5(f"{user_id}-{filename}-{timestamp}".encode()).hexdigest()[:8]
        # Replace spaces with underscores and keep only safe characters
        safe_filename = "".join(c if c.isalnum() or c in "._-" else "_" for c in filename)
        # Remove multiple consecutive underscores
        safe_filename = "_".join(filter(None, safe_filename.split("_")))
        return f"{file_type}s/{user_id}/{timestamp}_{file_hash}_{safe_filename}"
    
    def _calculate_file_checksum(self, file_content: bytes) -> str:
        """Calculate MD5 checksum of file content"""
        return hashlib.md5(file_content).hexdigest()
    
    def _generate_urls(self, storage_key: str) -> Tuple[str, str]:
        """Generate storage and CDN URLs"""
        storage_url = f"https://{self.bucket_name}.{settings.BACKBLAZE_ENDPOINT}/{storage_key}"
        cdn_url = f"{self.cdn_base_url}/{storage_key}" if self.cdn_base_url else storage_url
        return storage_url, cdn_url
    
    def _determine_file_type(self, mime_type: str) -> str:
        """Determine file type from MIME type"""
        if mime_type.startswith('video/'):
            return 'video'
        elif mime_type.startswith('audio/'):
            return 'audio'
        elif mime_type.startswith('image/'):
            return 'image'
        else:
            return 'document'
    
    def get_presigned_upload_url(
        self, 
        user_id: str,
        filename: str, 
        content_type: str, 
        expires_in: int = 3600
    ) -> Dict[str, Any]:
        """
        Generate presigned URL for direct browser upload
        """
        try:
            file_type = self._determine_file_type(content_type)
            storage_key = self._generate_storage_key(user_id, filename, file_type)
            
            # Use S3-compatible presigned URL for CORS compatibility
            # Generate presigned PUT URL that works with browsers (matching Flask implementation)
            presigned_url = self.client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': storage_key,
                    'ContentType': content_type,
                    'Metadata': {
                        'user-id': user_id,
                        'original-filename': filename,
                        'file-type': file_type,
                    }
                },
                ExpiresIn=expires_in
            )
            
            # Parse the URL to get the base URL for CORS
            parsed = urlparse(presigned_url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            
            # Generate URLs
            storage_url, cdn_url = self._generate_urls(storage_key)
            
            # Return response in format expected by frontend (matching Flask implementation)
            response = {
                'upload_url': presigned_url,
                'method': 'PUT',  # PUT method for S3-compatible upload
                'storage_key': storage_key,
                'cdn_url': f"{self.cdn_base_url}/{storage_key}" if self.cdn_base_url else None,
                'cors_origin': base_url,
                'headers': {
                    'Content-Type': content_type,
                    # No auth headers needed - they're in the presigned URL
                },
                's3_compatible': True  # Flag to indicate S3-compatible API
            }
            
            logger.info(f"Generated S3-compatible presigned URL for: {storage_key}")
            logger.info(f"Presigned URL: {presigned_url[:100]}...")  # Log first 100 chars for debugging
            logger.info(f"CDN URL: {response.get('cdn_url', 'None')}")
            return response
            
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise Exception(f"Failed to generate upload URL: {str(e)}")
    
    def delete_file(self, storage_key: str) -> bool:
        """Delete file from Backblaze storage"""
        try:
            logger.info(f"Deleting file from Backblaze: {storage_key}")
            self.client.delete_object(Bucket=self.bucket_name, Key=storage_key)
            logger.info(f"File deleted successfully: {storage_key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete file {storage_key}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting file {storage_key}: {e}")
            return False
    
    def get_file_info(self, storage_key: str) -> Optional[Dict[str, Any]]:
        """Get file information from Backblaze"""
        try:
            response = self.client.head_object(Bucket=self.bucket_name, Key=storage_key)
            return {
                'size': response.get('ContentLength'),
                'last_modified': response.get('LastModified'),
                'content_type': response.get('ContentType'),
                'metadata': response.get('Metadata', {}),
                'etag': response.get('ETag', '').strip('\"')
            }
        except ClientError as e:
            if e.response.get('Error', {}).get('Code') == 'NoSuchKey':
                return None
            logger.error(f"Failed to get file info for {storage_key}: {e}")
            return None


class VideoProcessingService:
    """Service for video processing and metadata extraction using ffmpeg"""
    
    def __init__(self):
        """Initialize video processing service"""
        self._check_ffmpeg_availability()
    
    def _check_ffmpeg_availability(self):
        """Check if ffmpeg is available on the system"""
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            if result.returncode != 0:
                logger.warning("ffmpeg not found - video processing features will be limited")
            else:
                logger.info("ffmpeg detected and ready for video processing")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.warning("ffmpeg not available - video processing features will be limited")
    
    def _download_temp_file(self, url: str, temp_dir: str) -> str:
        """Download video file to temporary location for processing"""
        logger.info(f"Downloading video from URL: {url}")
        
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Create temporary file
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path) or "video_temp"
            temp_path = os.path.join(temp_dir, filename)
            
            # Download file
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Video downloaded to: {temp_path}")
            return temp_path
            
        except requests.RequestException as e:
            logger.error(f"Failed to download video: {e}")
            raise Exception(f"Failed to download video: {e}")
    
    def extract_metadata(self, video_source: str) -> Dict[str, Any]:
        """Extract video metadata using ffprobe"""
        logger.info(f"Extracting metadata from: {video_source}")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Download video if it's a URL
                if video_source.startswith(('http://', 'https://')):
                    video_path = self._download_temp_file(video_source, temp_dir)
                else:
                    video_path = video_source
                
                # Use ffprobe to extract metadata
                cmd = [
                    'ffprobe',
                    '-v', 'quiet',
                    '-print_format', 'json',
                    '-show_format',
                    '-show_streams',
                    video_path
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60  # 1 minute timeout
                )
                
                if result.returncode != 0:
                    raise Exception(f"ffprobe failed: {result.stderr}")
                
                probe_data = json.loads(result.stdout)
                
                # Extract video stream information
                video_stream = None
                audio_stream = None
                
                for stream in probe_data.get('streams', []):
                    if stream['codec_type'] == 'video' and video_stream is None:
                        video_stream = stream
                    elif stream['codec_type'] == 'audio' and audio_stream is None:
                        audio_stream = stream
                
                if not video_stream:
                    raise Exception("No video stream found in file")
                
                # Parse duration
                format_info = probe_data.get('format', {})
                duration = float(format_info.get('duration', 0))
                
                # Parse frame rate
                frame_rate = None
                if 'r_frame_rate' in video_stream:
                    frame_rate_str = video_stream['r_frame_rate']
                    if '/' in frame_rate_str:
                        num, den = frame_rate_str.split('/')
                        if int(den) != 0:
                            frame_rate = float(num) / float(den)
                
                # Compile metadata
                metadata = {
                    'duration': int(duration),
                    'width': int(video_stream.get('width', 0)),
                    'height': int(video_stream.get('height', 0)),
                    'bitrate': int(video_stream.get('bit_rate', 0)),
                    'frame_rate': frame_rate,
                    'format': format_info.get('format_name', ''),
                    'file_size': int(format_info.get('size', 0)),
                    'codec': video_stream.get('codec_name', ''),
                    'audio_codec': audio_stream.get('codec_name') if audio_stream else None,
                    'audio_bitrate': int(audio_stream.get('bit_rate', 0)) if audio_stream else None,
                    'aspect_ratio': video_stream.get('display_aspect_ratio'),
                    'pixel_format': video_stream.get('pix_fmt')
                }
                
                # Add quality classification
                metadata['resolution'] = self._get_resolution_string(
                    metadata['width'], 
                    metadata['height']
                )
                
                logger.info(f"Metadata extracted successfully: {metadata}")
                return metadata
                
            except subprocess.TimeoutExpired:
                logger.error("Video metadata extraction timed out")
                raise Exception("Video processing timeout")
            except json.JSONDecodeError:
                logger.error("Failed to parse ffprobe output")
                raise Exception("Failed to parse video metadata")
            except Exception as e:
                logger.error(f"Metadata extraction failed: {e}")
                raise Exception(f"Failed to extract metadata: {e}")
    
    def _get_resolution_string(self, width: int, height: int) -> str:
        """Get resolution string based on dimensions"""
        if width >= 3840 or height >= 2160:
            return '4K'
        elif width >= 1920 or height >= 1080:
            return '1080p'
        elif width >= 1280 or height >= 720:
            return '720p'
        elif width >= 854 or height >= 480:
            return '480p'
        else:
            return '360p'
    
    def generate_thumbnail(
        self, 
        video_source: str, 
        timestamp: float = 10.0,
        width: int = 320,
        height: int = 240
    ) -> bytes:
        """Generate thumbnail from video at specified timestamp"""
        logger.info(f"Generating thumbnail for: {video_source} at {timestamp}s")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Download video if it's a URL
                if video_source.startswith(('http://', 'https://')):
                    video_path = self._download_temp_file(video_source, temp_dir)
                else:
                    video_path = video_source
                
                # Create thumbnail output path
                thumbnail_path = os.path.join(temp_dir, 'thumbnail.jpg')
                
                # Generate thumbnail using ffmpeg
                cmd = [
                    'ffmpeg',
                    '-i', video_path,
                    '-ss', str(timestamp),
                    '-vframes', '1',
                    '-vf', f'scale={width}:{height}',
                    '-q:v', '2',  # High quality JPEG
                    '-y',  # Overwrite output file
                    thumbnail_path
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode != 0:
                    raise Exception(f"Thumbnail generation failed: {result.stderr}")
                
                # Read thumbnail data
                with open(thumbnail_path, 'rb') as f:
                    thumbnail_data = f.read()
                
                logger.info(f"Thumbnail generated successfully: {len(thumbnail_data)} bytes")
                return thumbnail_data
                
            except subprocess.TimeoutExpired:
                logger.error("Thumbnail generation timed out")
                raise Exception("Thumbnail generation timeout")
            except Exception as e:
                logger.error(f"Thumbnail generation failed: {e}")
                raise Exception(f"Failed to generate thumbnail: {e}")


class MediaUploadService:
    """Service for handling media uploads and processing"""
    
    def __init__(self):
        self.storage_service = BackblazeStorageService()
        self.video_service = VideoProcessingService()
    
    def initiate_upload(self, user, filename: str, file_size: int, file_type: str, 
                       media_type: str, course_id: str = None) -> Dict[str, Any]:
        """Initiate a new media upload session for proxy upload"""
        try:
            # Validate file size
            max_size = getattr(settings, 'MAX_UPLOAD_SIZE', 500 * 1024 * 1024)  # 500MB
            if file_size > max_size:
                raise ValueError(f"File size exceeds maximum of {max_size / (1024*1024)}MB")
            
            # Determine correct file type from MIME type
            determined_file_type = self.storage_service._determine_file_type(file_type)
            
            # Generate storage key for proxy upload
            storage_key = self.storage_service._generate_storage_key(
                user_id=str(user.supabase_user_id),
                filename=filename,
                file_type=determined_file_type
            )
            
            # Generate storage and CDN URLs
            storage_url, cdn_url = self.storage_service._generate_urls(storage_key)
            
            # Remove extension from filename for user-friendly name
            import os
            filename_without_ext = os.path.splitext(filename)[0]
            
            # Create media file record
            media_file = MediaFile.objects.create(
                filename=filename_without_ext,  # Store without extension (e.g., "Introduction Video")
                original_filename=filename,      # Keep original with extension (e.g., "Introduction Video.mp4")
                file_size=file_size,
                file_type=determined_file_type,
                mime_type=file_type,
                user=user,
                processing_status='pending',
                upload_progress=0.0,
                storage_key=storage_key,
                storage_url=storage_url,
                cdn_url=cdn_url
            )
            
            # Create upload session for proxy upload
            session = UploadSession.objects.create(
                media_file=media_file,
                total_chunks=1,  # Single chunk upload
                uploaded_chunks=0,
                chunk_size=file_size,
                expires_at=timezone.now() + timedelta(hours=24),
                storage_provider='backblaze',
                storage_key=storage_key,
                upload_urls=[]  # No presigned URLs for proxy upload
            )
            
            # Update media file with session ID
            media_file.upload_id = session.session_id
            media_file.save()
            
            # Return proxy upload configuration
            from django.urls import reverse
            proxy_url = f"/api/v1/media/upload/proxy"
            
            return {
                'success': True,
                'upload_id': str(media_file.upload_id),
                'session_id': str(session.session_id),
                'upload_url': proxy_url,  # Proxy endpoint instead of presigned URL
                'storage_url': storage_url,
                'cdn_url': cdn_url,
                'method': 'POST',  # POST for proxy upload with form data
                'headers': {},
                'use_proxy': True  # Flag to indicate proxy upload
            }
            
        except Exception as e:
            logger.error(f"Failed to initiate upload: {e}")
            raise Exception(f"Upload initiation failed: {str(e)}")
    
    def complete_upload(self, session_id: str, user, upload_id: str = None) -> Dict[str, Any]:
        """Complete the upload and process the file"""
        try:
            # Get session first (since sessionId is always provided)
            session = UploadSession.objects.get(
                session_id=session_id,
                media_file__user=user
            )
            media_file = session.media_file
            
            # If upload_id is provided, verify it matches
            if upload_id and str(media_file.upload_id) != upload_id:
                raise Exception("Upload ID mismatch")
            
            # Update upload progress
            media_file.upload_progress = 100.0
            media_file.processing_status = 'completed'
            
            # If it's a video, extract metadata and trigger subtitle generation
            if media_file.file_type == 'video':
                try:
                    metadata = self.video_service.extract_metadata(media_file.cdn_url)
                    # Update video metadata fields that exist in the model
                    if hasattr(media_file, 'duration'):
                        media_file.duration = metadata.get('duration')
                    if hasattr(media_file, 'width'):
                        media_file.width = metadata.get('width')
                    if hasattr(media_file, 'height'):
                        media_file.height = metadata.get('height')
                    if hasattr(media_file, 'bitrate'):
                        media_file.bitrate = metadata.get('bitrate')
                    if hasattr(media_file, 'resolution'):
                        media_file.resolution = metadata.get('resolution')
                    if hasattr(media_file, 'metadata'):
                        media_file.metadata = metadata
                    if hasattr(media_file, 'processed_at'):
                        media_file.processed_at = timezone.now()
                        
                    logger.info(f"Video metadata extracted for {media_file.id}, triggering subtitle generation")
                except Exception as e:
                    logger.warning(f"Failed to extract video metadata: {e}")
                
                # Trigger automatic subtitle generation for video
                try:
                    from ai_assistant.tasks import generate_video_subtitles_task
                    
                    # Queue subtitle generation task with a 30-second delay to ensure video is fully processed
                    task = generate_video_subtitles_task.apply_async(
                        args=[str(media_file.id)],
                        countdown=30
                    )
                    
                    # Update processing metadata to track the subtitle generation task
                    processing_metadata = media_file.processing_metadata or {}
                    processing_metadata['subtitle_generation'] = {
                        'status': 'queued',
                        'queued_at': timezone.now().isoformat(),
                        'task_id': task.id
                    }
                    media_file.processing_metadata = processing_metadata
                    
                    logger.info(f"Subtitle generation task queued for video {media_file.id} with task ID: {task.id}")
                    
                except Exception as e:
                    logger.error(f"Failed to queue subtitle generation task for video {media_file.id}: {e}")
                    # Don't fail the upload if subtitle generation fails to queue
            
            media_file.save()
            
            # Mark session as complete
            session.is_active = False
            session.completed_at = timezone.now()
            session.save()
            
            return {
                'success': True,
                'media_file_id': str(media_file.id),
                'cdn_url': media_file.cdn_url,
                'processing_status': media_file.processing_status
            }
            
        except MediaFile.DoesNotExist:
            raise Exception("Upload session not found")
        except Exception as e:
            logger.error(f"Failed to complete upload: {e}")
            raise Exception(f"Upload completion failed: {str(e)}")


# Singleton instances
backblaze_service = BackblazeStorageService()
video_processing_service = VideoProcessingService()
media_upload_service = MediaUploadService()