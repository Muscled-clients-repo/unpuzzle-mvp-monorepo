"""
OpenAI API client service for AI assistant functionality
"""
import os
import logging
from typing import Dict, List, Optional, Any
from decimal import Decimal
import openai
from django.conf import settings
from django.core.cache import cache
import hashlib
import json

logger = logging.getLogger(__name__)


class OpenAIService:
    """
    Service for interacting with OpenAI API
    """
    
    def __init__(self):
        api_key = getattr(settings, 'OPENAI_API_KEY', None)
        logger.info(f"OpenAI Service initialization - API key exists: {bool(api_key)}")
        logger.info(f"OpenAI API key from settings: {api_key[:20] + '...' if api_key else 'None'}")
        
        if not api_key:
            logger.warning("OpenAI API key not configured - using mock mode")
            self.client = None
            self.mock_mode = True
        else:
            logger.info(f"Initializing OpenAI client with API key")
            self.client = openai.OpenAI(api_key=api_key)
            self.mock_mode = False
            logger.info(f"OpenAI client initialized successfully")
            
        self.model = getattr(settings, 'OPENAI_MODEL', 'gpt-4')
        self.max_tokens = getattr(settings, 'OPENAI_MAX_TOKENS', 500)
        self.cache_ttl = getattr(settings, 'AI_CACHE_TTL_SECONDS', 3600)
    
    def _generate_cache_key(self, prompt: str, context: Dict = None) -> str:
        """Generate cache key for AI responses"""
        cache_data = {
            'prompt': prompt,
            'context': context or {},
            'model': self.model
        }
        cache_string = json.dumps(cache_data, sort_keys=True)
        return f"ai_response:{hashlib.md5(cache_string.encode()).hexdigest()}"
    
    def _calculate_cost(self, tokens_used: int) -> Decimal:
        """Calculate cost based on token usage"""
        # GPT-4 pricing (approximate)
        cost_per_1k_tokens = Decimal('0.03')  # $0.03 per 1k tokens
        return (Decimal(tokens_used) / 1000) * cost_per_1k_tokens
    
    async def generate_response(
        self,
        prompt: str,
        context: Dict = None,
        agent_type: str = 'chat',
        max_tokens: Optional[int] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Generate AI response with caching support
        """
        try:
            # Check if we're in mock mode
            if self.mock_mode or not self.client:
                logger.warning("OpenAI client not available - returning mock response")
                return {
                    'response': "I'm currently unavailable due to API configuration. Please ensure the OpenAI API key is properly configured.",
                    'tokens_used': 0,
                    'cost': 0.0,
                    'cached': False,
                    'model': 'mock'
                }
            
            # Check cache first
            cache_key = self._generate_cache_key(prompt, context)
            if use_cache:
                cached_response = cache.get(cache_key)
                if cached_response:
                    logger.info(f"Cache hit for AI request: {agent_type}")
                    cached_response['cached'] = True
                    return cached_response
            
            # Prepare messages
            messages = self._prepare_messages(prompt, context, agent_type)
            
            # Make API call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens or self.max_tokens,
                temperature=0.7
            )
            
            # Extract response data
            ai_response = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            cost = self._calculate_cost(tokens_used)
            
            result = {
                'response': ai_response,
                'tokens_used': tokens_used,
                'cost': float(cost),
                'cached': False,
                'model': self.model
            }
            
            # Cache the response
            if use_cache:
                cache.set(cache_key, result, self.cache_ttl)
                logger.info(f"Cached AI response for {agent_type}")
            
            logger.info(f"Generated AI response: {agent_type}, tokens: {tokens_used}")
            return result
            
        except openai.RateLimitError as e:
            logger.error(f"OpenAI rate limit exceeded: {e}")
            raise OpenAIRateLimitError("AI service rate limit exceeded. Please try again later.")
        
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise OpenAIServiceError(f"AI service temporarily unavailable: {str(e)}")
        
        except Exception as e:
            logger.error(f"Unexpected error in AI generation: {e}")
            raise OpenAIServiceError(f"AI service error: {str(e)}")
    
    def _prepare_messages(
        self,
        prompt: str,
        context: Dict = None,
        agent_type: str = 'chat'
    ) -> List[Dict[str, str]]:
        """Prepare messages for OpenAI API based on agent type"""
        
        # System prompts for different agent types
        system_prompts = {
            'chat': (
                "You are a helpful learning assistant. Provide clear, educational responses "
                "based on the video content and context provided. Keep responses conversational "
                "and focused on helping the user understand the material."
            ),
            'hint': (
                "You are a hint generator. Provide brief, helpful hints that guide learning "
                "without giving away the complete answer. Focus on nudging the user toward "
                "understanding rather than providing full explanations."
            ),
            'quiz': (
                "You are a quiz generator. Create clear, educational quiz questions with "
                "multiple choice options based on the provided content. Include explanations "
                "for the correct answers."
            ),
            'reflection': (
                "You are a reflection prompt generator. Create thoughtful questions that help "
                "learners consolidate their understanding and connect concepts to broader "
                "learning objectives."
            ),
            'path': (
                "You are a learning path advisor. Analyze user progress and recommend "
                "personalized next steps, identify knowledge gaps, and suggest relevant "
                "content to help achieve learning goals."
            )
        }
        
        messages = [
            {"role": "system", "content": system_prompts.get(agent_type, system_prompts['chat'])}
        ]
        
        # Add context if provided
        if context:
            context_message = self._format_context(context)
            if context_message:
                messages.append({"role": "system", "content": context_message})
        
        # Add user prompt
        messages.append({"role": "user", "content": prompt})
        
        return messages
    
    def _format_context(self, context: Dict) -> str:
        """Format context information for AI prompt"""
        context_parts = []
        
        if context.get('video_id'):
            context_parts.append(f"Video ID: {context['video_id']}")
        
        if context.get('course_id'):
            context_parts.append(f"Course ID: {context['course_id']}")
        
        if context.get('timestamp'):
            context_parts.append(f"Video timestamp: {context['timestamp']} seconds")
        
        if context.get('transcript_segment'):
            context_parts.append(f"Transcript context: {context['transcript_segment']}")
        
        if context.get('user_difficulty'):
            context_parts.append(f"User difficulty: {context['user_difficulty']}")
        
        return "\n".join(context_parts) if context_parts else ""
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate text embedding for semantic search"""
        try:
            response = self.client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
        
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise OpenAIServiceError(f"Embedding generation failed: {str(e)}")


class OpenAIServiceError(Exception):
    """Base exception for OpenAI service errors"""
    pass


class OpenAIRateLimitError(OpenAIServiceError):
    """Exception for rate limit errors"""
    pass


class OpenAIInsufficientContextError(OpenAIServiceError):
    """Exception for insufficient context errors"""
    pass