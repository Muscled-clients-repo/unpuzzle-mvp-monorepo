"""
AI Agent services for specialized AI interactions
"""
import logging
from typing import Dict, List, Optional, Any
from .openai_client import OpenAIService
from ..models import AgentType

logger = logging.getLogger(__name__)


class AIAgentService:
    """
    Service for managing different AI agent types and their specialized behaviors
    """
    
    def __init__(self):
        self.openai_service = OpenAIService()
    
    async def generate_chat_response(
        self,
        message: str,
        context: Dict = None
    ) -> Dict[str, Any]:
        """Generate conversational chat response"""
        try:
            prompt = self._build_chat_prompt(message, context)
            
            response = await self.openai_service.generate_response(
                prompt=prompt,
                context=context,
                agent_type='chat',
                max_tokens=800
            )
            
            return {
                'response': response['response'],
                'agent_type': 'chat',
                'tokens_used': response['tokens_used'],
                'cached': response['cached']
            }
            
        except Exception as e:
            logger.error(f"Error in chat response generation: {e}")
            raise
    
    async def generate_hint(
        self,
        context: Dict
    ) -> Dict[str, Any]:
        """Generate contextual learning hint"""
        try:
            prompt = self._build_hint_prompt(context)
            
            response = await self.openai_service.generate_response(
                prompt=prompt,
                context=context,
                agent_type='hint',
                max_tokens=200
            )
            
            # Parse confidence from response (simplified)
            confidence = 0.85  # Default confidence
            
            return {
                'hint': response['response'],
                'confidence': confidence,
                'agent_type': 'hint',
                'tokens_used': response['tokens_used']
            }
            
        except Exception as e:
            logger.error(f"Error in hint generation: {e}")
            raise
    
    async def generate_quiz(
        self,
        context: Dict
    ) -> Dict[str, Any]:
        """Generate quiz question from content"""
        try:
            prompt = self._build_quiz_prompt(context)
            
            response = await self.openai_service.generate_response(
                prompt=prompt,
                context=context,
                agent_type='quiz',
                max_tokens=600
            )
            
            # Parse quiz response (would need more sophisticated parsing in production)
            quiz_data = self._parse_quiz_response(response['response'])
            
            return {
                **quiz_data,
                'agent_type': 'quiz',
                'tokens_used': response['tokens_used']
            }
            
        except Exception as e:
            logger.error(f"Error in quiz generation: {e}")
            raise
    
    async def generate_reflection(
        self,
        context: Dict
    ) -> Dict[str, Any]:
        """Generate reflection prompts for learning consolidation"""
        try:
            prompt = self._build_reflection_prompt(context)
            
            response = await self.openai_service.generate_response(
                prompt=prompt,
                context=context,
                agent_type='reflection',
                max_tokens=500
            )
            
            # Parse reflection response
            reflection_data = self._parse_reflection_response(response['response'])
            
            return {
                **reflection_data,
                'agent_type': 'reflection',
                'tokens_used': response['tokens_used']
            }
            
        except Exception as e:
            logger.error(f"Error in reflection generation: {e}")
            raise
    
    async def generate_learning_path(
        self,
        context: Dict
    ) -> Dict[str, Any]:
        """Generate personalized learning path recommendations"""
        try:
            prompt = self._build_path_prompt(context)
            
            response = await self.openai_service.generate_response(
                prompt=prompt,
                context=context,
                agent_type='path',
                max_tokens=800
            )
            
            # Parse path response
            path_data = self._parse_path_response(response['response'])
            
            return {
                **path_data,
                'agent_type': 'path',
                'tokens_used': response['tokens_used']
            }
            
        except Exception as e:
            logger.error(f"Error in learning path generation: {e}")
            raise
    
    def _build_chat_prompt(self, message: str, context: Dict = None) -> str:
        """Build prompt for chat agent"""
        prompt_parts = [
            f"Student question: {message}"
        ]
        
        if context and context.get('transcript_segment'):
            prompt_parts.append(f"Video content context: {context['transcript_segment']}")
        
        return "\n\n".join(prompt_parts)
    
    def _build_hint_prompt(self, context: Dict) -> str:
        """Build prompt for hint agent"""
        prompt_parts = [
            "Generate a helpful learning hint based on the following context:",
        ]
        
        if context.get('transcript_segment'):
            prompt_parts.append(f"Video content: {context['transcript_segment']}")
        
        if context.get('user_difficulty'):
            prompt_parts.append(f"Student is having difficulty with: {context['user_difficulty']}")
        
        prompt_parts.append("Provide a brief, encouraging hint that guides without giving the full answer.")
        
        return "\n\n".join(prompt_parts)
    
    def _build_quiz_prompt(self, context: Dict) -> str:
        """Build prompt for quiz agent"""
        prompt_parts = [
            "Create a multiple choice quiz question based on the following content:",
        ]
        
        if context.get('transcript_segments'):
            content = " ".join(context['transcript_segments'])
            prompt_parts.append(f"Content: {content}")
        
        difficulty = context.get('difficulty_level', 'medium')
        prompt_parts.append(f"Difficulty level: {difficulty}")
        
        prompt_parts.extend([
            "",
            "Format the response as:",
            "Question: [question text]",
            "A) [option 1]",
            "B) [option 2]", 
            "C) [option 3]",
            "D) [option 4]",
            "Correct Answer: [A/B/C/D]",
            "Explanation: [why this is correct]"
        ])
        
        return "\n".join(prompt_parts)
    
    def _build_reflection_prompt(self, context: Dict) -> str:
        """Build prompt for reflection agent"""
        prompt_parts = [
            "Create reflection prompts to help consolidate learning based on:",
        ]
        
        if context.get('completed_topics'):
            topics = ", ".join(context['completed_topics'])
            prompt_parts.append(f"Completed topics: {topics}")
        
        if context.get('learning_objectives'):
            objectives = ", ".join(context['learning_objectives'])
            prompt_parts.append(f"Learning objectives: {objectives}")
        
        prompt_parts.extend([
            "",
            "Provide:",
            "1. A main reflection prompt",
            "2. 2-3 guiding questions",
            "3. Expected response length (short/medium/long)"
        ])
        
        return "\n".join(prompt_parts)
    
    def _build_path_prompt(self, context: Dict) -> str:
        """Build prompt for learning path agent"""
        prompt_parts = [
            "Analyze the student's progress and recommend a personalized learning path:",
        ]
        
        if context.get('struggling_concepts'):
            struggling = ", ".join(context['struggling_concepts'])
            prompt_parts.append(f"Struggling with: {struggling}")
        
        if context.get('completed_concepts'):
            completed = ", ".join(context['completed_concepts'])
            prompt_parts.append(f"Already mastered: {completed}")
        
        if context.get('learning_goals'):
            goals = ", ".join(context['learning_goals'])
            prompt_parts.append(f"Learning goals: {goals}")
        
        prompt_parts.extend([
            "",
            "Provide:",
            "1. Identified issues/gaps",
            "2. Recommended content (title, description, difficulty, time estimate)",
            "3. Next steps prioritized by importance"
        ])
        
        return "\n".join(prompt_parts)
    
    def _parse_quiz_response(self, response: str) -> Dict[str, Any]:
        """Parse quiz response into structured format"""
        # Simplified parsing - in production would use more robust parsing
        lines = response.strip().split('\n')
        
        question = ""
        options = []
        correct_answer = 0
        explanation = ""
        
        try:
            for line in lines:
                line = line.strip()
                if line.startswith("Question:"):
                    question = line.replace("Question:", "").strip()
                elif line.startswith(("A)", "B)", "C)", "D)")):
                    options.append(line[3:].strip())
                elif line.startswith("Correct Answer:"):
                    answer_text = line.replace("Correct Answer:", "").strip()
                    # Handle both single letter (A, B, C, D) and full answers (A), B), etc.)
                    if answer_text:
                        # Extract first character that's A, B, C, or D
                        for char in answer_text.upper():
                            if char in ['A', 'B', 'C', 'D']:
                                correct_answer = ord(char) - ord('A')
                                break
                elif line.startswith("Explanation:"):
                    explanation = line.replace("Explanation:", "").strip()
        except Exception as e:
            logger.warning(f"Error parsing quiz response: {e}")
        
        return {
            'question': question or "What concept was discussed?",
            'options': options or ["Option A", "Option B", "Option C", "Option D"],
            'correctAnswer': max(0, min(correct_answer, 3)),
            'explanation': explanation or "Review the content for the correct answer."
        }
    
    def _parse_reflection_response(self, response: str) -> Dict[str, Any]:
        """Parse reflection response into structured format"""
        lines = [line.strip() for line in response.strip().split('\n') if line.strip()]
        
        prompt = ""
        guiding_questions = []
        expected_length = "medium"
        
        try:
            current_section = None
            for line in lines:
                if "reflection prompt" in line.lower() or line.startswith("1."):
                    current_section = "prompt"
                    prompt = line.split(":", 1)[-1].strip() if ":" in line else line
                elif "guiding questions" in line.lower() or line.startswith("2."):
                    current_section = "questions"
                elif "expected" in line.lower() and "length" in line.lower():
                    if "short" in line.lower():
                        expected_length = "short"
                    elif "long" in line.lower():
                        expected_length = "long"
                elif current_section == "questions" and line:
                    if line.startswith(("-", "•", "3.")):
                        guiding_questions.append(line.lstrip("-• 3.").strip())
                    elif not any(keyword in line.lower() for keyword in ["provide", "expected"]):
                        guiding_questions.append(line)
                elif current_section == "prompt" and line and not line.startswith(("2.", "Provide")):
                    prompt += " " + line
        except Exception as e:
            logger.warning(f"Error parsing reflection response: {e}")
        
        return {
            'prompt': prompt or "How would you apply what you've learned?",
            'guidingQuestions': guiding_questions[:3] if guiding_questions else [
                "What were the key concepts?",
                "How do they connect to your goals?",
                "What would you do differently?"
            ],
            'expectedLength': expected_length
        }
    
    def _parse_path_response(self, response: str) -> Dict[str, Any]:
        """Parse learning path response into structured format"""
        lines = [line.strip() for line in response.strip().split('\n') if line.strip()]
        
        detected_issues = []
        recommended_content = []
        next_steps = []
        
        try:
            current_section = None
            current_content = {}
            
            for line in lines:
                if "identified" in line.lower() and "issues" in line.lower():
                    current_section = "issues"
                elif "recommended" in line.lower() and "content" in line.lower():
                    current_section = "content"
                elif "next steps" in line.lower():
                    current_section = "steps"
                elif current_section == "issues" and line.startswith(("-", "•")):
                    detected_issues.append(line.lstrip("-• ").strip())
                elif current_section == "content":
                    if line.startswith(("-", "•")) or "title:" in line.lower():
                        if current_content:
                            recommended_content.append(current_content)
                        current_content = {
                            "type": "video",
                            "title": line.lstrip("-• ").replace("Title:", "").strip(),
                            "description": "",
                            "difficulty": "intermediate",
                            "estimatedTime": "15 min",
                            "priority": len(recommended_content) + 1
                        }
                    elif "description:" in line.lower() and current_content:
                        current_content["description"] = line.replace("Description:", "").strip()
                elif current_section == "steps" and line.startswith(("-", "•")):
                    next_steps.append(line.lstrip("-• ").strip())
            
            if current_content:
                recommended_content.append(current_content)
                
        except Exception as e:
            logger.warning(f"Error parsing path response: {e}")
        
        return {
            'detectedIssues': detected_issues or ["Review recent topics"],
            'recommendedContent': recommended_content or [{
                "type": "video",
                "title": "Continue Learning",
                "description": "Keep practicing the concepts",
                "difficulty": "intermediate",
                "estimatedTime": "15 min",
                "priority": 1
            }],
            'nextSteps': next_steps or ["Continue with recommended content"]
        }