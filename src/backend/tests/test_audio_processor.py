"""
Unit tests for AudioProcessor

Tests audio capture, queue management, and lifecycle operations.
"""

import asyncio
import sys
from pathlib import Path
import pytest
from unittest.mock import Mock, patch, AsyncMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from audio_processor import AudioProcessor


@pytest.fixture
def mock_pyaudio():
    """Mock pyaudio for testing without actual audio hardware."""
    with patch('audio_processor.pyaudio.PyAudio') as mock:
        # Mock the PyAudio instance
        mock_instance = Mock()
        mock.return_value = mock_instance
        
        # Mock get_default_input_device_info
        mock_instance.get_default_input_device_info.return_value = {
            "index": 0,
            "name": "Test Microphone"
        }
        
        # Mock the audio stream
        mock_stream = Mock()
        mock_stream.read = Mock(return_value=b'\x00\x01' * 1600)  # Mock audio data
        mock_instance.open.return_value = mock_stream
        
        yield mock_instance


@pytest.mark.asyncio
async def test_audio_processor_initialization():
    """Test that AudioProcessor initializes correctly."""
    processor = AudioProcessor(queue_maxsize=10)
    
    assert processor.audio_queue.maxsize == 10
    assert not processor.is_running
    assert processor.audio_stream is None


@pytest.mark.asyncio
async def test_start_capture(mock_pyaudio):
    """Test starting audio capture."""
    processor = AudioProcessor()
    
    await processor.start_capture()
    
    # Verify audio stream was opened
    assert mock_pyaudio.open.called
    assert processor.is_running
    
    # Clean up
    await processor.stop_capture()


@pytest.mark.asyncio
async def test_audio_queue_receives_data(mock_pyaudio):
    """Test that audio data is placed into the queue."""
    processor = AudioProcessor()
    
    await processor.start_capture()
    
    # Wait a bit for audio to be captured
    await asyncio.sleep(0.2)
    
    # Check that queue has audio data
    assert not processor.audio_queue.empty()
    
    # Get an audio message
    audio_msg = await processor.audio_queue.get()
    assert "data" in audio_msg
    assert "mime_type" in audio_msg
    assert audio_msg["mime_type"] == "audio/pcm"
    
    # Clean up
    await processor.stop_capture()


@pytest.mark.asyncio
async def test_stop_capture(mock_pyaudio):
    """Test stopping audio capture."""
    processor = AudioProcessor()
    
    await processor.start_capture()
    assert processor.is_running
    
    await processor.stop_capture()
    assert not processor.is_running
    
    # Verify cleanup was called
    mock_stream = mock_pyaudio.open.return_value
    assert mock_stream.close.called
    assert mock_pyaudio.terminate.called


@pytest.mark.asyncio
async def test_get_audio_queue():
    """Test getting the audio queue."""
    processor = AudioProcessor(queue_maxsize=5)
    
    queue = processor.get_audio_queue()
    assert isinstance(queue, asyncio.Queue)
    assert queue.maxsize == 5


@pytest.mark.asyncio
async def test_double_start_warning(mock_pyaudio, capsys):
    """Test that starting capture twice shows a warning."""
    processor = AudioProcessor()
    
    await processor.start_capture()
    await processor.start_capture()  # Second start
    
    # Check that warning was printed
    captured = capsys.readouterr()
    assert "already running" in captured.err
    
    # Clean up
    await processor.stop_capture()


@pytest.mark.asyncio
async def test_audio_processor_context_usage(mock_pyaudio):
    """Test using AudioProcessor in a typical async context."""
    processor = AudioProcessor()
    
    # Start capture
    await processor.start_capture()
    
    # Simulate consuming audio
    audio_msg = await asyncio.wait_for(
        processor.audio_queue.get(), 
        timeout=1.0
    )
    
    assert audio_msg is not None
    assert "data" in audio_msg
    
    # Stop capture
    await processor.stop_capture()
    assert not processor.is_running
