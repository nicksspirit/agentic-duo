"""
Integration test for refactored intent_client.py

Verifies that the refactored client using AudioProcessor and ToolExecutor
components still works correctly.
"""

import asyncio
import sys
from pathlib import Path
import pytest
from unittest.mock import Mock, patch, AsyncMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# We'll just do basic import and structure tests
# Full integration with Gemini API requires credentials

def test_intent_client_imports():
    """Test that intent_client imports successfully with new components."""
    try:
        import intent_client
        assert intent_client is not None
        assert hasattr(intent_client, 'run')
        assert hasattr(intent_client, 'print_hello')
        assert hasattr(intent_client, 'print_goodbye')
        assert hasattr(intent_client, 'print_test')
        assert hasattr(intent_client, 'print_status')
    except Exception as e:
        pytest.fail(f"Failed to import intent_client: {e}")


@pytest.mark.asyncio
async def test_print_functions():
    """Test that print functions still work."""
    import intent_client
    
    # Test each print function
    result = await intent_client.print_hello()
    assert result == "Hello!"
    
    result = await intent_client.print_goodbye()
    assert result == "Goodbye!"
    
    result = await intent_client.print_test()
    assert result == "Test executed"
    
    result = await intent_client.print_status()
    assert result == "Status: Ready"


def test_system_instruction_exists():
    """Test that system instruction is defined."""
    import intent_client
    
    assert intent_client.SYSTEM_INSTRUCTION is not None
    assert "speech-to-action" in intent_client.SYSTEM_INSTRUCTION.lower()
    assert "RULES" in intent_client.SYSTEM_INSTRUCTION


def test_model_config():
    """Test that model configuration is correct."""
    import intent_client
    
    assert intent_client.MODEL == "gemini-2.5-flash-native-audio-preview-12-2025"
    assert intent_client.EXECUTION_LOG == "execution.log"


@pytest.mark.asyncio
async def test_audio_processor_integration():
    """Test that AudioProcessor is correctly imported and can be instantiated."""
    from audio_processor import AudioProcessor
    
    processor = AudioProcessor(queue_maxsize=5)
    assert processor is not None
    assert not processor.is_running
    
    # Don't start actual capture in tests
    assert processor.get_audio_queue() is not None


@pytest.mark.asyncio
async def test_tool_executor_integration():
    """Test that ToolExecutor is correctly imported and can be used."""
    from tool_executor import ToolExecutor
    from google.genai.types import FunctionDeclaration
    
    executor = ToolExecutor(verbose=False)
    
    # Test registering a simple tool
    async def test_tool():
        return "test"
    
    declaration = FunctionDeclaration(
        name="test_tool",
        description="A test tool"
    )
    
    executor.register_tool("test_tool", test_tool, declaration)
    assert executor.has_tool("test_tool")
    assert len(executor.get_tool_declarations()) == 1
