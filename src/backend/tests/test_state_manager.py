"""
Unit tests for StateManager

Tests slide tracking, transcript management, injection tracking, and state operations.
"""

import asyncio
import sys
from pathlib import Path
import pytest
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from state_manager import StateManager, InjectionRecord


@pytest.fixture
def state_manager():
    """Create a StateManager instance for testing."""
    return StateManager(total_slides=10)


@pytest.mark.asyncio
async def test_state_manager_initialization():
    """Test that StateManager initializes correctly."""
    manager = StateManager(total_slides=10)
    
    assert manager.total_slides == 10
    assert manager.current_slide == 0
    assert len(manager.transcript) == 0
    assert len(manager.injections) == 0


@pytest.mark.asyncio
async def test_set_and_get_current_slide(state_manager):
    """Test setting and getting current slide."""
    await state_manager.set_current_slide(5)
    current = await state_manager.get_current_slide()
    
    assert current == 5


@pytest.mark.asyncio
async def test_set_current_slide_out_of_range(state_manager):
    """Test that setting invalid slide index raises error."""
    with pytest.raises(ValueError, match="out of range"):
        await state_manager.set_current_slide(15)


@pytest.mark.asyncio
async def test_navigate_next(state_manager):
    """Test navigating to next slide."""
    await state_manager.set_current_slide(5)
    new_index = await state_manager.navigate("next")
    
    assert new_index == 6
    assert await state_manager.get_current_slide() == 6


@pytest.mark.asyncio
async def test_navigate_prev(state_manager):
    """Test navigating to previous slide."""
    await state_manager.set_current_slide(5)
    new_index = await state_manager.navigate("prev")
    
    assert new_index == 4
    assert await state_manager.get_current_slide() == 4


@pytest.mark.asyncio
async def test_navigate_jump(state_manager):
    """Test jumping to specific slide."""
    new_index = await state_manager.navigate("jump", index=7)
    
    assert new_index == 7
    assert await state_manager.get_current_slide() == 7


@pytest.mark.asyncio
async def test_navigate_boundaries(state_manager):
    """Test navigation at slide boundaries."""
    # At first slide, can't go prev
    await state_manager.set_current_slide(0)
    new_index = await state_manager.navigate("prev")
    assert new_index == 0
    
    # At last slide, can't go next
    await state_manager.set_current_slide(9)
    new_index = await state_manager.navigate("next")
    assert new_index == 9


@pytest.mark.asyncio
async def test_add_transcript_entry(state_manager):
    """Test adding transcript entries."""
    await state_manager.add_transcript_entry("Hello, world!", speaker="user")
    
    transcript = await state_manager.get_recent_transcript(n=10)
    assert len(transcript) == 1
    assert transcript[0]["text"] == "Hello, world!"
    assert transcript[0]["speaker"] == "user"
    assert transcript[0]["slide_index"] == 0


@pytest.mark.asyncio
async def test_get_recent_transcript(state_manager):
    """Test getting recent transcript entries."""
    # Add multiple entries
    for i in range(15):
        await state_manager.add_transcript_entry(f"Entry {i}", speaker="user")
    
    # Get last 10
    recent = await state_manager.get_recent_transcript(n=10)
    assert len(recent) == 10
    assert recent[-1]["text"] == "Entry 14"


@pytest.mark.asyncio
async def test_get_transcript_for_slide(state_manager):
    """Test getting transcript for specific slide."""
    await state_manager.set_current_slide(0)
    await state_manager.add_transcript_entry("On slide 0", speaker="user")
    
    await state_manager.set_current_slide(1)
    await state_manager.add_transcript_entry("On slide 1", speaker="user")
    
    slide_0_transcript = await state_manager.get_transcript_for_slide(0)
    assert len(slide_0_transcript) == 1
    assert slide_0_transcript[0]["text"] == "On slide 0"


@pytest.mark.asyncio
async def test_track_injection(state_manager):
    """Test tracking content injections."""
    await state_manager.track_injection(
        placeholder="AI:IMAGE",
        content_type="image",
        content="base64_data_here"
    )
    
    injections = await state_manager.get_all_injections()
    assert len(injections) == 1
    assert injections[0].placeholder == "AI:IMAGE"
    assert injections[0].content_type == "image"


@pytest.mark.asyncio
async def test_get_injections_for_slide(state_manager):
    """Test getting injections for specific slide."""
    await state_manager.set_current_slide(0)
    await state_manager.track_injection("AI:IMAGE", "image", "data1")
    
    await state_manager.set_current_slide(1)
    await state_manager.track_injection("AI:TEXT", "text", "data2")
    
    slide_0_injections = await state_manager.get_injections_for_slide(0)
    assert len(slide_0_injections) == 1
    assert slide_0_injections[0].content == "data1"


@pytest.mark.asyncio
async def test_set_and_get_total_slides(state_manager):
    """Test setting and getting total slides."""
    await state_manager.set_total_slides(20)
    total = await state_manager.get_total_slides()
    
    assert total == 20


@pytest.mark.asyncio
async def test_get_context(state_manager):
    """Test getting presentation context."""
    await state_manager.set_current_slide(3)
    await state_manager.add_transcript_entry("Test entry", speaker="user")
    await state_manager.track_injection("AI:IMAGE", "image", "data")
    
    context = await state_manager.get_context()
    
    assert context["current_slide"] == 3
    assert context["total_slides"] == 10
    assert context["transcript_entries"] == 1
    assert context["injections_count"] == 1


@pytest.mark.asyncio
async def test_metadata_operations(state_manager):
    """Test session metadata operations."""
    await state_manager.set_metadata("session_id", "abc123")
    await state_manager.set_metadata("presenter", "John Doe")
    
    session_id = await state_manager.get_metadata("session_id")
    presenter = await state_manager.get_metadata("presenter")
    missing = await state_manager.get_metadata("missing_key", default="default_value")
    
    assert session_id == "abc123"
    assert presenter == "John Doe"
    assert missing == "default_value"


@pytest.mark.asyncio
async def test_clear_transcript(state_manager):
    """Test clearing transcript."""
    await state_manager.add_transcript_entry("Entry 1", speaker="user")
    await state_manager.add_transcript_entry("Entry 2", speaker="user")
    
    await state_manager.clear_transcript()
    
    transcript = await state_manager.get_recent_transcript(n=10)
    assert len(transcript) == 0


@pytest.mark.asyncio
async def test_clear_injections(state_manager):
    """Test clearing injections."""
    await state_manager.track_injection("AI:IMAGE", "image", "data1")
    await state_manager.track_injection("AI:TEXT", "text", "data2")
    
    await state_manager.clear_injections()
    
    injections = await state_manager.get_all_injections()
    assert len(injections) == 0


@pytest.mark.asyncio
async def test_reset(state_manager):
    """Test resetting all state."""
    await state_manager.set_current_slide(5)
    await state_manager.add_transcript_entry("Entry", speaker="user")
    await state_manager.track_injection("AI:IMAGE", "image", "data")
    await state_manager.set_metadata("key", "value")
    
    await state_manager.reset()
    
    assert await state_manager.get_current_slide() == 0
    assert len(await state_manager.get_recent_transcript(n=10)) == 0
    assert len(await state_manager.get_all_injections()) == 0
    assert await state_manager.get_metadata("key") is None


@pytest.mark.asyncio
async def test_concurrent_access():
    """Test that state manager handles concurrent access safely."""
    manager = StateManager(total_slides=10)
    
    async def navigate_task():
        for _ in range(10):
            await manager.navigate("next")
            await asyncio.sleep(0.001)
    
    async def transcript_task():
        for i in range(10):
            await manager.add_transcript_entry(f"Entry {i}", speaker="user")
            await asyncio.sleep(0.001)
    
    # Run tasks concurrently
    await asyncio.gather(navigate_task(), transcript_task())
    
    # Verify state is consistent
    current = await manager.get_current_slide()
    transcript = await manager.get_recent_transcript(n=20)
    
    assert current >= 0
    assert len(transcript) == 10
