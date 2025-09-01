"""
Transcript processing service for AI context and semantic search
"""
import logging
from typing import Dict, List, Optional, Any
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
try:
    import numpy as np
except ImportError:
    np = None
from .openai_client import OpenAIService
from ..models import TranscriptSegment, TranscriptReference

logger = logging.getLogger(__name__)


class TranscriptService:
    """
    Service for processing video transcripts and enabling semantic search
    """
    
    def __init__(self):
        self.openai_service = OpenAIService()
    
    async def search_transcript(
        self,
        video_id: str,
        query: str,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Search transcript content for relevant segments using semantic search
        """
        try:
            # Generate query embedding
            query_embedding = await self.openai_service.generate_embedding(query)
            
            # Get transcript segments for the video
            segments = TranscriptSegment.objects.filter(
                video_id=video_id,
                embedding__isnull=False
            )
            
            if not segments.exists():
                return {
                    'results': [],
                    'total_results': 0,
                    'search_time_ms': 0
                }
            
            # Calculate similarity scores
            start_time = timezone.now()
            scored_segments = []
            
            for segment in segments:
                if segment.embedding:
                    similarity = self._calculate_cosine_similarity(
                        query_embedding,
                        segment.embedding
                    )
                    scored_segments.append((segment, similarity))
            
            # Sort by similarity and limit results
            scored_segments.sort(key=lambda x: x[1], reverse=True)
            top_segments = scored_segments[:limit]
            
            search_time = (timezone.now() - start_time).total_seconds() * 1000
            
            # Format results
            results = []
            for segment, similarity in top_segments:
                results.append({
                    'text': segment.text,
                    'start_time': segment.start_time,
                    'end_time': segment.end_time,
                    'similarity': round(similarity, 3),
                    'chunk_id': str(segment.id)
                })
            
            return {
                'results': results,
                'total_results': len(scored_segments),
                'search_time_ms': int(search_time)
            }
            
        except Exception as e:
            logger.error(f"Error in transcript search: {e}")
            raise TranscriptServiceError(f"Transcript search failed: {str(e)}")
    
    async def save_transcript_reference(
        self,
        user,
        video_id: str,
        start_time: float,
        end_time: float,
        text: str,
        purpose: str = 'ai_context'
    ) -> Dict[str, Any]:
        """
        Save user-selected transcript segment for AI context
        """
        try:
            # Set expiration time (24 hours from now)
            expires_at = timezone.now() + timedelta(hours=24)
            
            # Create transcript reference
            reference = TranscriptReference.objects.create(
                user=user,
                video_id=video_id,
                start_time=start_time,
                end_time=end_time,
                text=text,
                purpose=purpose,
                expires_at=expires_at
            )
            
            return {
                'reference_id': str(reference.id),
                'saved': True,
                'message': 'Transcript reference saved successfully',
                'expires_at': expires_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error saving transcript reference: {e}")
            raise TranscriptServiceError(f"Failed to save transcript reference: {str(e)}")
    
    async def process_transcript_segments(
        self,
        video_id: str,
        course,
        transcript_data: List[Dict]
    ) -> int:
        """
        Process and store transcript segments with embeddings
        """
        try:
            segments_created = 0
            
            for segment_data in transcript_data:
                text = segment_data.get('text', '').strip()
                if not text:
                    continue
                
                start_time = segment_data.get('start_time', 0.0)
                end_time = segment_data.get('end_time', 0.0)
                
                # Check if segment already exists
                existing = TranscriptSegment.objects.filter(
                    video_id=video_id,
                    start_time=start_time,
                    end_time=end_time
                ).first()
                
                if existing:
                    continue
                
                # Generate embedding for the text
                try:
                    embedding = await self.openai_service.generate_embedding(text)
                except Exception as e:
                    logger.warning(f"Failed to generate embedding for segment: {e}")
                    embedding = None
                
                # Create transcript segment
                TranscriptSegment.objects.create(
                    video_id=video_id,
                    course=course,
                    text=text,
                    start_time=start_time,
                    end_time=end_time,
                    embedding=embedding,
                    metadata=segment_data.get('metadata', {})
                )
                
                segments_created += 1
            
            logger.info(f"Created {segments_created} transcript segments for video {video_id}")
            return segments_created
            
        except Exception as e:
            logger.error(f"Error processing transcript segments: {e}")
            raise TranscriptServiceError(f"Failed to process transcript segments: {str(e)}")
    
    def get_user_transcript_references(
        self,
        user,
        video_id: Optional[str] = None,
        active_only: bool = True
    ):
        """
        Get user's saved transcript references
        """
        queryset = TranscriptReference.objects.filter(user=user)
        
        if video_id:
            queryset = queryset.filter(video_id=video_id)
        
        if active_only:
            queryset = queryset.filter(
                Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
            )
        
        return queryset.order_by('-created_at')
    
    def cleanup_expired_references(self) -> int:
        """
        Clean up expired transcript references
        """
        try:
            expired_count = TranscriptReference.objects.filter(
                expires_at__lt=timezone.now()
            ).delete()[0]
            
            if expired_count > 0:
                logger.info(f"Cleaned up {expired_count} expired transcript references")
            
            return expired_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired references: {e}")
            return 0
    
    def _calculate_cosine_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        Calculate cosine similarity between two embeddings
        """
        try:
            if np is None:
                # Fallback to basic Python implementation
                dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
                norm1 = sum(a * a for a in embedding1) ** 0.5
                norm2 = sum(b * b for b in embedding2) ** 0.5
                
                if norm1 == 0 or norm2 == 0:
                    return 0.0
                
                return dot_product / (norm1 * norm2)
            else:
                # Use numpy for better performance
                vec1 = np.array(embedding1)
                vec2 = np.array(embedding2)
                
                dot_product = np.dot(vec1, vec2)
                norm1 = np.linalg.norm(vec1)
                norm2 = np.linalg.norm(vec2)
                
                if norm1 == 0 or norm2 == 0:
                    return 0.0
                
                return dot_product / (norm1 * norm2)
            
        except Exception as e:
            logger.warning(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    def get_video_transcript_context(
        self,
        video_id: str,
        timestamp: float,
        context_window: float = None
    ) -> Optional[str]:
        """
        Get transcript context around a specific timestamp
        """
        try:
            from django.conf import settings
            
            # Use configured context window or default
            if context_window is None:
                context_window = getattr(settings, 'TRANSCRIPT_CONTEXT_WINDOW_SECONDS', 30.0)
            
            # Calculate proper bounds - ensure start_time is never negative
            context_start = max(0, timestamp - context_window)
            context_end = timestamp + context_window
            
            logger.info(f"TranscriptService: Searching for segments in video {video_id} "
                       f"from {context_start}s to {context_end}s (timestamp: {timestamp}, window: {context_window}s)")
            
            # Find segments that overlap with our context window
            # A segment overlaps if: segment_start <= context_end AND segment_end >= context_start
            segments = TranscriptSegment.objects.filter(
                video_id=video_id,
                start_time__lte=context_end,
                end_time__gte=context_start
            ).order_by('start_time')
            
            segment_count = segments.count()
            logger.info(f"TranscriptService: Found {segment_count} transcript segments in context window")
            
            if not segments.exists():
                # Let's also check if there are ANY segments for this video
                total_segments = TranscriptSegment.objects.filter(video_id=video_id).count()
                logger.warning(f"TranscriptService: No segments in context window [{context_start}-{context_end}], "
                              f"total segments for video: {total_segments}")
                return None
            
            # Log segment details for debugging
            for segment in segments[:3]:  # Log first 3 segments
                logger.info(f"TranscriptService: Segment [{segment.start_time}-{segment.end_time}]: {segment.text[:50]}...")
            
            # Combine segment texts
            context_text = " ".join([segment.text for segment in segments])
            logger.info(f"TranscriptService: Returning context text of length {len(context_text)}")
            return context_text[:1000]  # Limit context length
            
        except Exception as e:
            logger.error(f"Error getting video transcript context: {e}")
            return None


class TranscriptServiceError(Exception):
    """Base exception for transcript service errors"""
    pass