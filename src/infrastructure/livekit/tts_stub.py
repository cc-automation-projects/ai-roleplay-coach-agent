"""TTS (Text-to-Speech) stub — placeholder for Silero."""

from __future__ import annotations

import logging
import os

# Default model path — overridden by env var TTS_MODEL_PATH or constructor arg.
_DEFAULT_MODEL_PATH = "/models/silero-v5"

logger = logging.getLogger(__name__)


class TTSStub:
    """Stub TTS engine — returns dummy audio bytes.

    Will be replaced with Silero TTS v5 in Phase 3.
    """

    def __init__(self, model_path: str | None = None) -> None:
        self._model_path = model_path or os.environ.get(
            "TTS_MODEL_PATH",
            _DEFAULT_MODEL_PATH,
        )
        self._loaded = False

    async def load(self) -> None:
        """Load the TTS model (stub)."""
        logger.info("TTSStub.load — would load model from %s", self._model_path)
        self._loaded = True

    async def synthesize(self, text: str, voice: str = "neutral") -> bytes:
        """Synthesize text to audio bytes (stub)."""
        logger.debug("TTSStub.synthesize — %d chars, voice=%s", len(text), voice)
        return b"[stub audio data]"

    async def unload(self) -> None:
        """Release model resources."""
        self._loaded = False
        logger.info("TTSStub unloaded")
