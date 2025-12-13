"""
Unit tests for SlideTools

Tests all 5 slide control tools with StateManager integration.
"""

import asyncio
import sys
from pathlib import Path
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from state_manager import StateManager
from slide_tools import SlideTools


@pytest.fixture
def state_manager():
    """Create a StateManager instance for testing."""
    return StateManager(total_slides=10)


@pytest.fixture
def slide_tools(state_manager):
    """Create a SlideTools instance for testing."""
    return SlideTools(state_manager)


@pytest.mark.asyncio
async def test_navigate_slide_next(slide_tools, state_manager):
    """Test navigating to next slide."""
    await state_manager.set_current_slide(3)
    
    result = await slide_tools.navigate_slide("next")
    
    assert result["success"] is True
    assert result["action"] == "navigate"
    assert result["direction"] == "next"
    assert result["current_slide"] == 4
    assert result["total_slides"] == 10


@pytest.mark.asyncio
async def test_navigate_slide_prev(slide_tools, state_manager):
    """Test navigating to previous slide."""
    await state_manager.set_current_slide(5)
    
    result = await slide_tools.navigate_slide("prev")
    
    assert result["success"] is True
    assert result["current_slide"] == 4


@pytest.mark.asyncio
async def test_navigate_slide_jump(slide_tools):
    """Test jumping to specific slide."""
    result = await slide_tools.navigate_slide("jump", index=7)
    
    assert result["success"] is True
    assert result["current_slide"] == 7


@pytest.mark.asyncio
async def test_navigate_slide_invalid(slide_tools):
    """Test navigation with invalid parameters."""
    result = await slide_tools.navigate_slide("jump")  # Missing index
    
    assert result["success"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_inject_image_stub(slide_tools, state_manager):
    """Test image injection (stub implementation)."""
    await state_manager.set_current_slide(2)
    
    result = await slide_tools.inject_image(
        prompt="architecture diagram",
        target_placeholder="AI:IMAGE"
    )
    
    assert result["success"] is True
    assert result["action"] == "inject_image"
    assert result["prompt"] == "architecture diagram"
    assert result["slide_index"] == 2
    assert result["stub"] is True
    
    # Verify injection was tracked
    injections = await state_manager.get_injections_for_slide(2)
    assert len(injections) == 1
    assert injections[0].content_type == "image"


@pytest.mark.asyncio
async def test_add_content(slide_tools, state_manager):
    """Test adding text content to slide."""
    await state_manager.set_current_slide(1)
    
    result = await slide_tools.add_content(
        content="This is a new bullet point",
        target_placeholder="AI:CONTENT"
    )
    
    assert result["success"] is True
    assert result["action"] == "inject_content"
    assert result["content"] == "This is a new bullet point"
    assert result["slide_index"] == 1
    
    # Verify injection was tracked
    injections = await state_manager.get_injections_for_slide(1)
    assert len(injections) == 1
    assert injections[0].content_type == "text"


@pytest.mark.asyncio
async def test_generate_summary_with_transcript(slide_tools, state_manager):
    """Test generating summary from transcript."""
    # Add some transcript entries
    await state_manager.add_transcript_entry("First key point about the topic", speaker="user")
    await state_manager.add_transcript_entry("Second important observation", speaker="user")
    await state_manager.add_transcript_entry("Third critical detail", speaker="user")
    
    result = await slide_tools.generate_summary()
    
    assert result["success"] is True
    assert result["action"] == "inject_summary"
    assert "summary" in result
    assert result["stub"] is True
    
    # Verify injection was tracked
    injections = await state_manager.get_all_injections()
    assert len(injections) == 1
    assert injections[0].content_type == "summary"


@pytest.mark.asyncio
async def test_generate_summary_no_transcript(slide_tools):
    """Test generating summary with no transcript."""
    result = await slide_tools.generate_summary()
    
    assert result["success"] is False
    assert "error" in result
    assert "No transcript" in result["error"]


@pytest.mark.asyncio
async def test_get_presentation_context(slide_tools, state_manager):
    """Test getting presentation context."""
    await state_manager.set_current_slide(5)
    await state_manager.add_transcript_entry("Test entry", speaker="user")
    await slide_tools.add_content("Test content")
    
    result = await slide_tools.get_presentation_context()
    
    assert result["success"] is True
    assert result["action"] == "get_context"
    assert result["current_slide"] == 5
    assert result["total_slides"] == 10
    assert result["transcript_entries"] == 1
    assert result["injections_count"] == 1


@pytest.mark.asyncio
async def test_multiple_injections_same_slide(slide_tools, state_manager):
    """Test multiple injections on the same slide."""
    await state_manager.set_current_slide(0)
    
    await slide_tools.inject_image("diagram 1", "AI:IMAGE")
    await slide_tools.add_content("content 1", "AI:CONTENT")
    await slide_tools.add_content("content 2", "AI:CONTENT_2")
    
    injections = await state_manager.get_injections_for_slide(0)
    assert len(injections) == 3
    
    # Check types
    types = [inj.content_type for inj in injections]
    assert "image" in types
    assert types.count("text") == 2


@pytest.mark.asyncio
async def test_slide_tools_integration(slide_tools, state_manager):
    """Test full integration of multiple tools."""
    # Navigate to slide 2
    result = await slide_tools.navigate_slide("jump", index=2)
    assert result["current_slide"] == 2
    
    # Add some content
    await slide_tools.add_content("Key point 1")
    
    # Add transcript
    await state_manager.add_transcript_entry("Discussing key points", speaker="user")
    
    # Get context
    context = await slide_tools.get_presentation_context()
    assert context["current_slide"] == 2
    assert context["injections_count"] == 1
    assert context["transcript_entries"] == 1
    
    # Navigate to next slide
    result = await slide_tools.navigate_slide("next")
    assert result["current_slide"] == 3
