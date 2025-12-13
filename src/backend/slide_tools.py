"""
Slide Tools Module

Implements slide deck-specific tools for the agentic slide presentation system.

Tools provided:
- navigate_slide: Navigate between slides
- inject_image: Generate and inject images (stub)
- add_content: Add text/bullet points
- generate_summary: Create summary from transcript
- get_presentation_context: Get current state
"""

import sys
from typing import Optional, Dict, Any
from state_manager import StateManager


class SlideTools:
    """
    Collection of slide deck control tools.
    
    These tools integrate with StateManager to provide presentation
    control functionality for the Gemini Live API.
    """
    
    def __init__(self, state_manager: StateManager):
        """
        Initialize slide tools with a state manager.
        
        Args:
            state_manager: StateManager instance
        """
        self.state = state_manager
    
    async def navigate_slide(
        self, 
        direction: str, 
        index: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Navigate to a different slide.
        
        Args:
            direction: 'next', 'prev', or 'jump'
            index: Slide index (required for 'jump')
            
        Returns:
            Dict with navigation result
        """
        try:
            new_index = await self.state.navigate(direction, index)
            total = await self.state.get_total_slides()
            
            return {
                "action": "navigate",
                "direction": direction,
                "current_slide": new_index,
                "total_slides": total,
                "success": True
            }
        except Exception as e:
            return {
                "action": "navigate",
                "success": False,
                "error": str(e)
            }
    
    async def inject_image(
        self, 
        prompt: str, 
        target_placeholder: str = "AI:IMAGE"
    ) -> Dict[str, Any]:
        """
        Generate and inject an image into the current slide.
        
        NOTE: This is a stub implementation. Actual image generation
        via Imagen API will be added in Phase 3.
        
        Args:
            prompt: Description of the image to generate
            target_placeholder: Placeholder identifier in markdown
            
        Returns:
            Dict with injection result
        """
        try:
            current_slide = await self.state.get_current_slide()
            
            # STUB: Actual Imagen integration will be added
            # For now, just track the injection request
            await self.state.track_injection(
                placeholder=target_placeholder,
                content_type="image",
                content={
                    "prompt": prompt,
                    "status": "stub",
                    "message": "Image generation not yet implemented"
                },
                slide_index=current_slide
            )
            
            return {
                "action": "inject_image",
                "placeholder": target_placeholder,
                "prompt": prompt,
                "slide_index": current_slide,
                "success": True,
                "stub": True,
                "message": "Image generation stub - will be implemented with Imagen API"
            }
        except Exception as e:
            return {
                "action": "inject_image",
                "success": False,
                "error": str(e)
            }
    
    async def add_content(
        self, 
        content: str, 
        target_placeholder: str = "AI:CONTENT"
    ) -> Dict[str, Any]:
        """
        Add bullet points or text to the current slide.
        
        Args:
            content: Text content to add
            target_placeholder: Placeholder identifier in markdown
            
        Returns:
            Dict with injection result
        """
        try:
            current_slide = await self.state.get_current_slide()
            
            # Track the content injection
            await self.state.track_injection(
                placeholder=target_placeholder,
                content_type="text",
                content=content,
                slide_index=current_slide
            )
            
            return {
                "action": "inject_content",
                "placeholder": target_placeholder,
                "content": content,
                "slide_index": current_slide,
                "success": True
            }
        except Exception as e:
            return {
                "action": "inject_content",
                "success": False,
                "error": str(e)
            }
    
    async def generate_summary(self) -> Dict[str, Any]:
        """
        Generate a summary slide based on presentation transcript.
        
        Uses recent transcript entries to create bullet points.
        
        Returns:
            Dict with summary result
        """
        try:
            # Get recent transcript
            recent = await self.state.get_recent_transcript(n=20)
            
            if not recent:
                return {
                    "action": "generate_summary",
                    "success": False,
                    "error": "No transcript available to summarize"
                }
            
            # Extract text from transcript
            texts = [entry["text"] for entry in recent]
            
            # Simple summary: create bullet points from key statements
            # TODO: In Phase 3, use Gemini API to generate better summaries
            summary_bullets = []
            for text in texts[:5]:  # Take first 5 entries as key points
                if len(text) > 10:  # Skip very short entries
                    summary_bullets.append(f"- {text[:100]}...")  # Truncate long entries
            
            summary = "\n".join(summary_bullets)
            
            # Track the summary injection
            current_slide = await self.state.get_current_slide()
            await self.state.track_injection(
                placeholder="AI:SUMMARY",
                content_type="summary",
                content=summary,
                slide_index=current_slide
            )
            
            return {
                "action": "inject_summary",
                "summary": summary,
                "slide_index": current_slide,
                "success": True,
                "stub": True,
                "message": "Basic summary - will be improved with Gemini API"
            }
        except Exception as e:
            return {
                "action": "generate_summary",
                "success": False,
                "error": str(e)
            }
    
    async def get_presentation_context(self) -> Dict[str, Any]:
        """
        Get current presentation context.
        
        Returns current slide index, total slides, and recent activity.
        
        Returns:
            Dict with presentation context
        """
        try:
            context = await self.state.get_context()
            return {
                "action": "get_context",
                "success": True,
                **context
            }
        except Exception as e:
            return {
                "action": "get_context",
                "success": False,
                "error": str(e)
            }


# Convenience factory function
def create_slide_tools(state_manager: StateManager) -> SlideTools:
    """
    Factory function to create a SlideTools instance.
    
    Args:
        state_manager: StateManager instance
        
    Returns:
        Configured SlideTools instance
    """
    return SlideTools(state_manager)
