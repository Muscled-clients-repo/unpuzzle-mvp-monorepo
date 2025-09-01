"""
AI-powered subtitle generation service using OpenAI Whisper API
"""
import os
import tempfile
import logging
import subprocess
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from django.core.files.base import ContentFile

from .openai_client import OpenAIService
from media_library.services import BackblazeStorageService
from media_library.models import MediaFile
from ai_assistant.models import TranscriptSegment

logger = logging.getLogger(__name__)


class SubtitleGenerationService:
    """
    Service for generating subtitles from video content using OpenAI Whisper
    """
    
    def __init__(self):
        self.openai_service = OpenAIService()
        self.storage_service = BackblazeStorageService()
        self.max_audio_size = 25 * 1024 * 1024  # 25MB OpenAI limit
        self.supported_audio_formats = ['mp3', 'mp4', 'm4a', 'wav', 'webm']
    
    def generate_subtitles_from_video_sync(
        self,
        video_id: str,
        video_cdn_url: str,
        user_id: str = None
    ) -> Dict[str, Any]:
        """
        Generate subtitles from video URL
        
        Args:
            video_id: ID of the video in MediaFile
            video_cdn_url: CDN URL of the video file
            user_id: User ID for storage key generation
            
        Returns:
            Dict containing success status, SRT URL, and transcript segments
        """
        try:
            logger.info(f"Starting subtitle generation for video {video_id} from URL: {video_cdn_url}")
            
            # Get media file record
            try:
                media_file = MediaFile.objects.get(id=video_id)
                user_id = user_id or str(media_file.user.supabase_user_id)
            except MediaFile.DoesNotExist:
                raise Exception(f"MediaFile with ID {video_id} not found")
            
            with tempfile.TemporaryDirectory() as temp_dir:
                # Step 1: Download and extract audio from video
                logger.info(f"Extracting audio from video: {video_id}")
                audio_path = self._extract_audio_from_video_sync(video_cdn_url, temp_dir)
                
                # Step 2: Check audio file size and split if necessary
                audio_chunks = self._prepare_audio_chunks_sync(audio_path, temp_dir)
                
                # Step 3: Transcribe audio using OpenAI Whisper
                logger.info(f"Transcribing {len(audio_chunks)} audio chunk(s)")
                transcript_segments = self._transcribe_audio_chunks_sync(audio_chunks)
                
                # Step 4: Generate SRT content
                srt_content = self._generate_srt_content(transcript_segments)
                
                # Step 5: Upload SRT file to Backblaze
                srt_url = self._upload_srt_to_backblaze_sync(
                    srt_content, video_id, user_id, temp_dir
                )
                
                # Step 6: Update MediaFile with subtitle URL
                media_file.subtitles = srt_url
                media_file.save()
                
                # Step 7: Store transcript segments in database for AI context
                self._store_transcript_segments_sync(
                    video_id, transcript_segments, media_file.course
                )
                
                logger.info(f"Subtitle generation completed for video {video_id}")
                return {
                    'success': True,
                    'video_id': video_id,
                    'subtitle_url': srt_url,
                    'segments_count': len(transcript_segments),
                    'message': 'Subtitles generated successfully'
                }
                
        except Exception as e:
            logger.error(f"Subtitle generation failed for video {video_id}: {e}")
            return {
                'success': False,
                'video_id': video_id,
                'error': str(e),
                'message': 'Subtitle generation failed'
            }
    
    def _extract_audio_from_video_sync(self, video_url: str, temp_dir: str) -> str:
        """
        Extract audio from video using ffmpeg
        """
        try:
            # Download video file
            logger.info(f"Downloading video from: {video_url}")
            video_response = requests.get(video_url, stream=True, timeout=300)
            video_response.raise_for_status()
            
            # Save video to temp file
            video_path = os.path.join(temp_dir, "video_temp.mp4")
            with open(video_path, 'wb') as f:
                for chunk in video_response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Extract audio using ffmpeg
            audio_path = os.path.join(temp_dir, "audio_temp.mp3")
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vn',  # No video
                '-acodec', 'mp3',  # Audio codec
                '-ar', '16000',  # Sample rate (16kHz is good for speech)
                '-ac', '1',  # Mono channel
                '-b:a', '64k',  # Bitrate
                '-y',  # Overwrite output
                audio_path
            ]
            
            logger.info(f"Extracting audio with command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )
            
            if result.returncode != 0:
                raise Exception(f"FFmpeg audio extraction failed: {result.stderr}")
            
            if not os.path.exists(audio_path):
                raise Exception("Audio extraction failed - output file not created")
            
            audio_size = os.path.getsize(audio_path)
            logger.info(f"Audio extracted successfully: {audio_size} bytes")
            return audio_path
            
        except subprocess.TimeoutExpired:
            raise Exception("Audio extraction timed out")
        except requests.RequestException as e:
            raise Exception(f"Failed to download video: {e}")
        except Exception as e:
            raise Exception(f"Audio extraction failed: {e}")
    
    def _prepare_audio_chunks_sync(self, audio_path: str, temp_dir: str) -> List[str]:
        """
        Prepare audio chunks for OpenAI (max 25MB per chunk)
        """
        try:
            audio_size = os.path.getsize(audio_path)
            logger.info(f"Audio file size: {audio_size} bytes")
            
            # If file is small enough, return as single chunk
            if audio_size <= self.max_audio_size:
                return [audio_path]
            
            # Split audio into chunks
            logger.info(f"Audio file too large ({audio_size} bytes), splitting into chunks")
            
            # Get audio duration first
            duration_cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-show_entries', 'format=duration',
                '-of', 'csv=p=0',
                audio_path
            ]
            
            result = subprocess.run(duration_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception("Failed to get audio duration")
            
            total_duration = float(result.stdout.strip())
            
            # Calculate chunk duration (aim for 20MB chunks to stay under 25MB limit)
            target_chunk_size = 20 * 1024 * 1024
            chunk_duration = (total_duration * target_chunk_size) / audio_size
            chunk_duration = max(60, min(chunk_duration, 600))  # Between 1-10 minutes
            
            chunks = []
            chunk_count = int(total_duration / chunk_duration) + 1
            
            for i in range(chunk_count):
                start_time = i * chunk_duration
                if start_time >= total_duration:
                    break
                
                chunk_path = os.path.join(temp_dir, f"audio_chunk_{i}.mp3")
                
                # Extract chunk
                cmd = [
                    'ffmpeg',
                    '-i', audio_path,
                    '-ss', str(start_time),
                    '-t', str(chunk_duration),
                    '-acodec', 'copy',
                    '-y',
                    chunk_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0 and os.path.exists(chunk_path):
                    chunk_size = os.path.getsize(chunk_path)
                    if chunk_size > 0:
                        chunks.append(chunk_path)
                        logger.info(f"Created chunk {i}: {chunk_size} bytes")
            
            if not chunks:
                raise Exception("Failed to create any audio chunks")
            
            return chunks
            
        except Exception as e:
            raise Exception(f"Failed to prepare audio chunks: {e}")
    
    def _transcribe_audio_chunks_sync(self, audio_chunks: List[str]) -> List[Dict[str, Any]]:
        """
        Transcribe audio chunks using OpenAI Whisper API
        """
        try:
            all_segments = []
            current_offset = 0.0
            
            for i, chunk_path in enumerate(audio_chunks):
                logger.info(f"Transcribing chunk {i+1}/{len(audio_chunks)}")
                
                # Read audio file
                with open(chunk_path, 'rb') as audio_file:
                    # Call OpenAI Whisper API
                    response = self.openai_service.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="verbose_json",  # Get timestamps
                        timestamp_granularities=["segment"]
                    )
                
                # Process segments
                if hasattr(response, 'segments'):
                    for segment in response.segments:
                        segment_data = {
                            'start': segment.start + current_offset,
                            'end': segment.end + current_offset,
                            'text': segment.text.strip()
                        }
                        all_segments.append(segment_data)
                else:
                    # Fallback if no segments available
                    segment_data = {
                        'start': current_offset,
                        'end': current_offset + 30.0,  # Estimate 30s duration
                        'text': response.text.strip()
                    }
                    all_segments.append(segment_data)
                
                # Update offset for next chunk (rough estimate)
                if all_segments:
                    current_offset = all_segments[-1]['end']
                else:
                    current_offset += 300  # 5 minute estimate
            
            logger.info(f"Transcription completed: {len(all_segments)} segments")
            return all_segments
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise Exception(f"Failed to transcribe audio: {e}")
    
    def _generate_srt_content(self, segments: List[Dict[str, Any]]) -> str:
        """
        Generate SRT subtitle content from transcript segments
        """
        try:
            srt_lines = []
            
            for i, segment in enumerate(segments, 1):
                start_time = self._seconds_to_srt_time(segment['start'])
                end_time = self._seconds_to_srt_time(segment['end'])
                text = segment['text'].strip()
                
                if text:  # Only add non-empty segments
                    srt_lines.extend([
                        str(i),
                        f"{start_time} --> {end_time}",
                        text,
                        ""  # Empty line between segments
                    ])
            
            srt_content = "\n".join(srt_lines)
            logger.info(f"Generated SRT content: {len(srt_lines)} lines")
            return srt_content
            
        except Exception as e:
            raise Exception(f"Failed to generate SRT content: {e}")
    
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """
        Convert seconds to SRT time format (HH:MM:SS,mmm)
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
    
    def _upload_srt_to_backblaze_sync(
        self, 
        srt_content: str, 
        video_id: str, 
        user_id: str,
        temp_dir: str
    ) -> str:
        """
        Upload SRT file to Backblaze and return CDN URL
        """
        try:
            # Create SRT file
            srt_filename = f"video_{video_id}_subtitles.srt"
            srt_path = os.path.join(temp_dir, srt_filename)
            
            with open(srt_path, 'w', encoding='utf-8') as f:
                f.write(srt_content)
            
            # Generate storage key
            storage_key = self.storage_service._generate_storage_key(
                user_id=user_id,
                filename=srt_filename,
                file_type="subtitle"
            )
            
            # Read SRT file content
            with open(srt_path, 'rb') as f:
                srt_data = f.read()
            
            # Upload to Backblaze
            logger.info(f"Uploading SRT file to Backblaze: {storage_key}")
            
            self.storage_service.client.put_object(
                Bucket=self.storage_service.bucket_name,
                Key=storage_key,
                Body=srt_data,
                ContentType='text/plain',
                Metadata={
                    'video-id': video_id,
                    'user-id': user_id,
                    'content-type': 'subtitle',
                    'generated-at': datetime.utcnow().isoformat()
                }
            )
            
            # Generate CDN URL
            cdn_url = f"{self.storage_service.cdn_base_url}/{storage_key}"
            logger.info(f"SRT file uploaded successfully: {cdn_url}")
            return cdn_url
            
        except Exception as e:
            raise Exception(f"Failed to upload SRT file: {e}")
    
    def _store_transcript_segments_sync(
        self, 
        video_id: str, 
        segments: List[Dict[str, Any]], 
        course
    ) -> int:
        """
        Store transcript segments in database for AI context
        """
        try:
            logger.info(f"Storing {len(segments)} transcript segments for video {video_id}")
            
            # Delete existing segments for this video
            TranscriptSegment.objects.filter(video_id=video_id).delete()
            
            segments_created = 0
            
            for segment in segments:
                try:
                    # Generate embedding for semantic search
                    embedding = None
                    try:
                        if segment['text'].strip():
                            embedding = self.openai_service.client.embeddings.create(
                                model="text-embedding-ada-002",
                                input=segment['text'].strip()
                            ).data[0].embedding
                    except Exception as e:
                        logger.warning(f"Failed to generate embedding for segment: {e}")
                    
                    # Create transcript segment
                    TranscriptSegment.objects.create(
                        video_id=video_id,
                        course=course,
                        text=segment['text'].strip(),
                        start_time=segment['start'],
                        end_time=segment['end'],
                        embedding=embedding,
                        metadata={
                            'generated_at': datetime.utcnow().isoformat(),
                            'source': 'whisper_api'
                        }
                    )
                    segments_created += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to store segment: {e}")
                    continue
            
            logger.info(f"Stored {segments_created} transcript segments for video {video_id}")
            return segments_created
            
        except Exception as e:
            logger.error(f"Failed to store transcript segments: {e}")
            return 0


# Singleton instance
subtitle_generation_service = SubtitleGenerationService()