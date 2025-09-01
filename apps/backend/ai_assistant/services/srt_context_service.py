"""
Service for extracting video context from SRT subtitle files
"""
import re
import requests
import logging
from typing import Dict, Any, Optional, List, Tuple
from django.conf import settings
from media_library.models import MediaFile

logger = logging.getLogger(__name__)


class SRTContextService:
    """
    Service for parsing SRT files and extracting video context based on timestamps
    """
    
    def __init__(self):
        self.context_window_seconds = getattr(settings, 'TRANSCRIPT_CONTEXT_WINDOW_SECONDS', 30)
    
    def get_video_context_from_srt(
        self,
        video_id: str,
        timestamp: float,
        context_window: Optional[float] = None
    ) -> Optional[str]:
        """
        Get video context from SRT subtitle file based on timestamp
        
        Args:
            video_id: ID of the video
            timestamp: Timestamp in seconds to get context around
            context_window: Window in seconds around timestamp (default from settings)
            
        Returns:
            Context text from subtitles or None if not available
        """
        try:
            logger.info(f"SRTContextService: Getting context for video {video_id} at timestamp {timestamp}s")
            
            # Get MediaFile with subtitle URL
            try:
                media_file = MediaFile.objects.get(id=video_id, file_type='video')
            except MediaFile.DoesNotExist:
                logger.warning(f"MediaFile {video_id} not found")
                return None
            
            if not media_file.subtitles:
                logger.warning(f"Video {video_id} has no subtitle URL")
                return None
            
            # Stream and parse SRT file
            srt_segments = self._stream_and_parse_srt(media_file.subtitles)
            if not srt_segments:
                logger.warning(f"No SRT segments found for video {video_id}")
                return None
            
            # Extract context around timestamp
            context_window = context_window or self.context_window_seconds
            context_text = self._extract_context_from_segments(
                srt_segments, timestamp, context_window
            )
            
            if context_text:
                logger.info(f"SRTContextService: Found context for video {video_id}: {len(context_text)} characters")
                return context_text
            else:
                logger.warning(f"SRTContextService: No context found for video {video_id} at timestamp {timestamp}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting SRT context for video {video_id}: {e}")
            return None
    
    def _stream_and_parse_srt(self, srt_url: str) -> List[Dict[str, Any]]:
        """
        Stream and parse SRT file from URL
        
        Returns:
            List of subtitle segments with start_time, end_time, and text
        """
        try:
            logger.info(f"SRTContextService: Streaming SRT from {srt_url}")
            
            # Stream SRT file content
            response = requests.get(srt_url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Read content in chunks and build the SRT content
            srt_content = ""
            for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
                if chunk:
                    srt_content += chunk
            
            # Parse SRT content
            segments = self._parse_srt_content(srt_content)
            logger.info(f"SRTContextService: Parsed {len(segments)} segments from streamed SRT")
            
            return segments
            
        except requests.RequestException as e:
            logger.error(f"Failed to stream SRT file from {srt_url}: {e}")
            return []
        except Exception as e:
            logger.error(f"Failed to parse streamed SRT file: {e}")
            return []
    
    def _parse_srt_content(self, srt_content: str) -> List[Dict[str, Any]]:
        """
        Parse SRT file content into segments
        
        Args:
            srt_content: Raw SRT file content
            
        Returns:
            List of segments with start_time, end_time, and text
        """
        segments = []
        
        try:
            # Split content into subtitle blocks (separated by double newlines)
            blocks = re.split(r'\n\s*\n', srt_content.strip())
            
            for block in blocks:
                if not block.strip():
                    continue
                
                lines = block.strip().split('\n')
                if len(lines) < 3:
                    continue
                
                # Extract sequence number (first line)
                try:
                    sequence = int(lines[0].strip())
                except (ValueError, IndexError):
                    continue
                
                # Extract timestamp (second line)
                timestamp_line = lines[1].strip()
                start_time, end_time = self._parse_srt_timestamp(timestamp_line)
                
                if start_time is None or end_time is None:
                    continue
                
                # Extract text (remaining lines)
                text_lines = lines[2:]
                text = ' '.join(line.strip() for line in text_lines if line.strip())
                
                if text:
                    segments.append({
                        'sequence': sequence,
                        'start_time': start_time,
                        'end_time': end_time,
                        'text': text
                    })
            
            # Sort by start time
            segments.sort(key=lambda x: x['start_time'])
            logger.info(f"Successfully parsed {len(segments)} SRT segments")
            
            return segments
            
        except Exception as e:
            logger.error(f"Error parsing SRT content: {e}")
            return []
    
    def _parse_srt_timestamp(self, timestamp_line: str) -> Tuple[Optional[float], Optional[float]]:
        """
        Parse SRT timestamp line (e.g., "00:00:01,500 --> 00:00:04,000")
        
        Returns:
            Tuple of (start_seconds, end_seconds) or (None, None) if parsing fails
        """
        try:
            # SRT timestamp format: HH:MM:SS,mmm --> HH:MM:SS,mmm
            timestamp_pattern = r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})'
            match = re.match(timestamp_pattern, timestamp_line)
            
            if not match:
                return None, None
            
            # Parse start time
            start_h, start_m, start_s, start_ms = map(int, match.groups()[:4])
            start_seconds = start_h * 3600 + start_m * 60 + start_s + start_ms / 1000
            
            # Parse end time
            end_h, end_m, end_s, end_ms = map(int, match.groups()[4:])
            end_seconds = end_h * 3600 + end_m * 60 + end_s + end_ms / 1000
            
            return start_seconds, end_seconds
            
        except Exception as e:
            logger.warning(f"Failed to parse timestamp '{timestamp_line}': {e}")
            return None, None
    
    def _extract_context_from_segments(
        self,
        segments: List[Dict[str, Any]],
        timestamp: float,
        context_window: float
    ) -> Optional[str]:
        """
        Extract context text from segments around the given timestamp using proper bounds logic
        
        Examples:
        - timestamp=10s, window=30s -> context_start=0s (max(0, 10-30)), context_end=40s
        - timestamp=50s, window=30s -> context_start=20s, context_end=80s
        
        Args:
            segments: List of SRT segments
            timestamp: Target timestamp in seconds
            context_window: Window size in seconds
            
        Returns:
            Context text or None if no relevant segments found
        """
        try:
            # Calculate context window bounds - ensure start_time is never negative
            context_start = max(0, timestamp - context_window)
            context_end = timestamp + context_window
            
            logger.info(f"SRTContextService: Looking for segments between {context_start:.1f}s and {context_end:.1f}s "
                       f"(timestamp: {timestamp}s, window: {context_window}s)")
            
            # Find segments that overlap with the context window
            relevant_segments = []
            
            for segment in segments:
                segment_start = segment['start_time']
                segment_end = segment['end_time']
                
                # Check if segment overlaps with context window
                # A segment overlaps if: segment_start <= context_end AND segment_end >= context_start
                if segment_start <= context_end and segment_end >= context_start:
                    relevant_segments.append(segment)
            
            if not relevant_segments:
                logger.warning(f"No segments found in context window [{context_start:.1f}-{context_end:.1f}]")
                return None
            
            # Sort by start time and combine text
            relevant_segments.sort(key=lambda x: x['start_time'])
            
            # Log first few segments for debugging
            for i, segment in enumerate(relevant_segments[:3]):
                logger.info(f"SRTContextService: Segment {i+1} [{segment['start_time']:.1f}-{segment['end_time']:.1f}s]: {segment['text'][:50]}...")
            
            context_text = ' '.join(segment['text'] for segment in relevant_segments)
            
            # Limit context length (max 1000 characters)
            if len(context_text) > 1000:
                context_text = context_text[:1000] + "..."
            
            logger.info(f"SRTContextService: Extracted context from {len(relevant_segments)} segments, "
                       f"length: {len(context_text)} characters")
            return context_text
            
        except Exception as e:
            logger.error(f"Error extracting context from segments: {e}")
            return None
    
    def get_segment_at_timestamp(self, video_id: str, timestamp: float) -> Optional[Dict[str, Any]]:
        """
        Get the specific subtitle segment at a given timestamp
        
        Args:
            video_id: ID of the video
            timestamp: Timestamp in seconds
            
        Returns:
            Segment dict or None if not found
        """
        try:
            # Get MediaFile with subtitle URL
            try:
                media_file = MediaFile.objects.get(id=video_id, file_type='video')
            except MediaFile.DoesNotExist:
                return None
            
            if not media_file.subtitles:
                return None
            
            # Stream and parse SRT file
            srt_segments = self._stream_and_parse_srt(media_file.subtitles)
            if not srt_segments:
                return None
            
            # Find segment containing the timestamp
            for segment in srt_segments:
                if segment['start_time'] <= timestamp <= segment['end_time']:
                    return segment
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting segment at timestamp {timestamp} for video {video_id}: {e}")
            return None


# Singleton instance
srt_context_service = SRTContextService()