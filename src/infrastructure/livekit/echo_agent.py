"""LiveKit echo agent stub — placeholder for ASR/TTS pipeline.

This module provides a minimal LiveKit Agent that:
  - Connects to a LiveKit room
  - Listens for audio tracks (operator microphone)
  - Echoes the audio back (placeholder for Whisper ASR → LLM → Silero TTS)

In Phase 2+ this will be replaced with the actual ASR→LLM→TTS pipeline.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

_LIVEKIT_URL = os.environ.get("LIVEKIT_URL", "ws://localhost:7880")
_LIVEKIT_API_KEY = os.environ.get("LIVEKIT_API_KEY", "devkey")
_LIVEKIT_API_SECRET = os.environ.get("LIVEKIT_API_SECRET", "secret")


class EchoAgent:
    """Minimal LiveKit agent that echoes audio (ASR/TTS stub)."""

    def __init__(
        self,
        room_name: str | None = None,
        identity: str = "coach-agent",
    ) -> None:
        self._room_name = room_name or os.environ.get("LIVEKIT_ROOM", "coaching-room")
        self._identity = identity
        self._participant: object | None = None
        self._room: object | None = None

    async def start(self) -> None:
        """Connect to LiveKit room and start listening."""
        logger.info(
            "EchoAgent starting — connecting to %s (room=%s)",
            _LIVEKIT_URL,
            self._room_name,
        )
        # Phase 2: integrate actual LiveKit Agent connection
        #   from livekit import rtc
        #   room = rtc.Room()
        #   await room.connect(_LIVEKIT_URL, token)
        #   room.on("track_subscribed", self._on_track)
        logger.info("EchoAgent connected (stub)")

    async def stop(self) -> None:
        """Disconnect from the room."""
        logger.info("EchoAgent disconnecting (stub)")

    async def echo_audio(self, audio_data: bytes) -> bytes:
        """Stub: return the same audio data (placeholder for ASR→LLM→TTS)."""
        logger.debug("echo_audio called — %d bytes", len(audio_data))
        return audio_data

    async def health(self) -> bool:
        """Return True if connected (stub)."""
        return True
