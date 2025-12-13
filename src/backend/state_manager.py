"""
State Manager Module

Manages presentation state including current slide, conversation history,
and injected content tracking for the agentic slide deck.

This module provides:
- Current slide index tracking
- Conversation transcript storage
- Content injection tracking
- Session metadata management
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class InjectionRecord:
    """Record of content injected into a slide."""
    timestamp: datetime
    slide_index: int
    placeholder: str
    content_type: str  # "image", "text", "summary"
    content: Any
    

class StateManager:
    """
    Manages presentation state across tools and sessions.
    
    Tracks:
    - Current slide position
    - Conversation history/transcript
    - Injected content
    - Session metadata
    """
    
    def __init__(self, total_slides: int = 0):
        """
        Initialize the state manager.
        
        Args:
            total_slides: Total number of slides in the presentation
        """
        self.total_slides = total_slides
        self.current_slide = 0
        self.transcript: List[Dict[str, Any]] = []
        self.injections: List[InjectionRecord] = []
        self.session_metadata: Dict[str, Any] = {
            "started_at": datetime.now(),
            "session_id": None
        }
        self._lock = asyncio.Lock()
    
    async def set_current_slide(self, index: int) -> None:
        """
        Set the current slide index.
        
        Args:
            index: Slide index (0-based)
            
        Raises:
            ValueError: If index is out of range
        """
        async with self._lock:
            if self.total_slides > 0 and (index < 0 or index >= self.total_slides):
                raise ValueError(f"Slide index {index} out of range (0-{self.total_slides-1})")
            self.current_slide = index
    
    async def get_current_slide(self) -> int:
        """Get the current slide index."""
        async with self._lock:
            return self.current_slide
    
    async def navigate(self, direction: str, index: Optional[int] = None) -> int:
        """
        Navigate slides.
        
        Args:
            direction: "next", "prev", or "jump"
            index: Target slide index (required for "jump")
            
        Returns:
            New slide index
            
        Raises:
            ValueError: If navigation is invalid
        """
        async with self._lock:
            if direction == "next":
                new_index = min(self.current_slide + 1, self.total_slides - 1 if self.total_slides > 0 else 0)
            elif direction == "prev":
                new_index = max(self.current_slide - 1, 0)
            elif direction == "jump":
                if index is None:
                    raise ValueError("Index required for 'jump' navigation")
                new_index = index
            else:
                raise ValueError(f"Invalid direction: {direction}")
            
            # Validate range
            if self.total_slides > 0 and (new_index < 0 or new_index >= self.total_slides):
                raise ValueError(f"Cannot navigate to slide {new_index} (range: 0-{self.total_slides-1})")
            
            self.current_slide = new_index
            return new_index
    
    async def add_transcript_entry(
        self, 
        text: str, 
        speaker: str = "user",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add an entry to the conversation transcript.
        
        Args:
            text: Transcript text
            speaker: Speaker identifier ("user", "assistant", etc.)
            metadata: Optional metadata dict
        """
        async with self._lock:
            entry = {
                "timestamp": datetime.now(),
                "text": text,
                "speaker": speaker,
                "slide_index": self.current_slide,
                "metadata": metadata or {}
            }
            self.transcript.append(entry)
    
    async def get_recent_transcript(self, n: int = 10) -> List[Dict[str, Any]]:
        """
        Get the n most recent transcript entries.
        
        Args:
            n: Number of recent entries to retrieve
            
        Returns:
            List of transcript entries
        """
        async with self._lock:
            return self.transcript[-n:] if self.transcript else []
    
    async def get_transcript_for_slide(self, slide_index: int) -> List[Dict[str, Any]]:
        """
        Get all transcript entries for a specific slide.
        
        Args:
            slide_index: Slide index to filter by
            
        Returns:
            List of transcript entries for that slide
        """
        async with self._lock:
            return [
                entry for entry in self.transcript 
                if entry["slide_index"] == slide_index
            ]
    
    async def track_injection(
        self,
        placeholder: str,
        content_type: str,
        content: Any,
        slide_index: Optional[int] = None
    ) -> None:
        """
        Track content injection.
        
        Args:
            placeholder: Placeholder identifier (e.g., "AI:IMAGE")
            content_type: Type of content ("image", "text", "summary")
            content: The actual content
            slide_index: Slide index (defaults to current slide)
        """
        async with self._lock:
            injection = InjectionRecord(
                timestamp=datetime.now(),
                slide_index=slide_index if slide_index is not None else self.current_slide,
                placeholder=placeholder,
                content_type=content_type,
                content=content
            )
            self.injections.append(injection)
    
    async def get_injections_for_slide(self, slide_index: int) -> List[InjectionRecord]:
        """
        Get all injections for a specific slide.
        
        Args:
            slide_index: Slide index
            
        Returns:
            List of injection records
        """
        async with self._lock:
            return [
                inj for inj in self.injections 
                if inj.slide_index == slide_index
            ]
    
    async def get_all_injections(self) -> List[InjectionRecord]:
        """Get all injection records."""
        async with self._lock:
            return self.injections.copy()
    
    async def set_total_slides(self, total: int) -> None:
        """
        Set the total number of slides.
        
        Args:
            total: Total slide count
        """
        async with self._lock:
            self.total_slides = total
    
    async def get_total_slides(self) -> int:
        """Get the total number of slides."""
        async with self._lock:
            return self.total_slides
    
    async def get_context(self) -> Dict[str, Any]:
        """
        Get presentation context summary.
        
        Returns:
            Dict with current state information
        """
        async with self._lock:
            return {
                "current_slide": self.current_slide,
                "total_slides": self.total_slides,
                "transcript_entries": len(self.transcript),
                "injections_count": len(self.injections),
                "recent_transcript": self.transcript[-5:] if self.transcript else [],
                "session_metadata": self.session_metadata
            }
    
    async def set_metadata(self, key: str, value: Any) -> None:
        """
        Set session metadata.
        
        Args:
            key: Metadata key
            value: Metadata value
        """
        async with self._lock:
            self.session_metadata[key] = value
    
    async def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Get session metadata.
        
        Args:
            key: Metadata key
            default: Default value if key not found
            
        Returns:
            Metadata value or default
        """
        async with self._lock:
            return self.session_metadata.get(key, default)
    
    async def clear_transcript(self) -> None:
        """Clear all transcript entries."""
        async with self._lock:
            self.transcript.clear()
    
    async def clear_injections(self) -> None:
        """Clear all injection records."""
        async with self._lock:
            self.injections.clear()
    
    async def reset(self) -> None:
        """Reset all state to initial values."""
        async with self._lock:
            self.current_slide = 0
            self.transcript.clear()
            self.injections.clear()
            self.session_metadata = {
                "started_at": datetime.now(),
                "session_id": None
            }


# Convenience factory function
def create_state_manager(total_slides: int = 0) -> StateManager:
    """
    Factory function to create a StateManager instance.
    
    Args:
        total_slides: Total number of slides
        
    Returns:
        Configured StateManager instance
    """
    return StateManager(total_slides=total_slides)
