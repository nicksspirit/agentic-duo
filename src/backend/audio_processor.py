"""
Audio Processor Module

Handles audio capture from microphone and streaming to audio queue.
Extracted from intent_client.py for reusability across the application.

This module provides:
- Async audio capture using pyaudio
- PCM audio format configuration (16kHz, 16-bit, Mono)
- Queue-based audio streaming
- Lifecycle management (start/stop)
"""

import asyncio
import sys
from typing import Optional
import pyaudio


class AudioProcessor:
    """
    Manages audio capture and streaming for the Gemini Live API.
    
    Captures audio at 16kHz, 16-bit, Mono PCM format as required by Gemini Live API.
    Audio chunks are placed into an async queue for consumption by other components.
    """
    
    # Audio configuration constants
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    SAMPLE_RATE = 16000  # 16kHz required by Gemini Live API
    CHUNK_SIZE = 1600    # ~100ms of audio at 16kHz
    
    def __init__(self, queue_maxsize: int = 5):
        """
        Initialize the audio processor.
        
        Args:
            queue_maxsize: Maximum size of the audio queue (default: 5)
        """
        self.pya = pyaudio.PyAudio()
        self.audio_queue: asyncio.Queue = asyncio.Queue(maxsize=queue_maxsize)
        self.audio_stream: Optional[pyaudio.Stream] = None
        self._capture_task: Optional[asyncio.Task] = None
        self._is_running = False
    
    async def start_capture(self) -> None:
        """
        Start capturing audio from the default microphone.
        
        Creates an audio stream and begins capturing audio chunks,
        placing them into the audio queue.
        
        Raises:
            Exception: If audio input setup fails
        """
        if self._is_running:
            print("Warning: Audio capture is already running", file=sys.stderr)
            return
        
        try:
            # Get default input device
            mic_info = self.pya.get_default_input_device_info()
            
            # Open audio stream
            self.audio_stream = await asyncio.to_thread(
                self.pya.open,
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.SAMPLE_RATE,
                input=True,
                input_device_index=mic_info["index"],
                frames_per_buffer=self.CHUNK_SIZE,
            )
            
            self._is_running = True
            
            # Start the capture loop
            self._capture_task = asyncio.create_task(self._capture_loop())
            
        except Exception as e:
            print(f"Error setting up audio input: {e}", file=sys.stderr, flush=True)
            raise
    
    async def _capture_loop(self) -> None:
        """
        Internal loop that continuously captures audio chunks.
        
        Runs until stop_capture() is called.
        """
        # Suppress overflow exceptions in debug mode
        kwargs = {"exception_on_overflow": False} if __debug__ else {}
        
        try:
            while self._is_running:
                try:
                    # Read audio chunk from stream
                    data = await asyncio.to_thread(
                        self.audio_stream.read, 
                        self.CHUNK_SIZE, 
                        **kwargs
                    )
                    
                    # Package for Gemini Live API format
                    audio_msg = {
                        "data": data,
                        "mime_type": "audio/pcm"
                    }
                    
                    # Put into queue for consumption
                    await self.audio_queue.put(audio_msg)
                    
                except Exception as e:
                    if self._is_running:  # Only log if not shutting down
                        print(f"Error reading audio: {e}", file=sys.stderr, flush=True)
                        await asyncio.sleep(0.1)
                    continue
                    
        except asyncio.CancelledError:
            # Clean shutdown
            pass
    
    async def stop_capture(self) -> None:
        """
        Stop capturing audio and clean up resources.
        
        Closes the audio stream and terminates pyaudio.
        """
        self._is_running = False
        
        # Cancel the capture task
        if self._capture_task:
            self._capture_task.cancel()
            try:
                await self._capture_task
            except asyncio.CancelledError:
                pass
        
        # Close audio stream
        if self.audio_stream:
            try:
                self.audio_stream.close()
            except Exception as e:
                print(f"Error closing audio stream: {e}", file=sys.stderr)
        
        # Terminate pyaudio
        try:
            self.pya.terminate()
        except Exception as e:
            print(f"Error terminating pyaudio: {e}", file=sys.stderr)
    
    def get_audio_queue(self) -> asyncio.Queue:
        """
        Get the audio queue for consuming audio chunks.
        
        Returns:
            asyncio.Queue containing audio messages in Gemini Live API format
        """
        return self.audio_queue
    
    @property
    def is_running(self) -> bool:
        """Check if audio capture is currently running."""
        return self._is_running


# Convenience function for backward compatibility
async def create_audio_processor(queue_maxsize: int = 5) -> AudioProcessor:
    """
    Factory function to create and return an AudioProcessor instance.
    
    Args:
        queue_maxsize: Maximum size of the audio queue
        
    Returns:
        Configured AudioProcessor instance
    """
    return AudioProcessor(queue_maxsize=queue_maxsize)
