"""ASR (Automatic Speech Recognition) stub — placeholder for Whisper."""

from __future__ import annotations

import logging
import os

# Default model path — overridden by env var ASR_MODEL_PATH or constructor arg.
_DEFAULT_MODEL_PATH = "/models/whisper-large-v3"

logger = logging.getLogger(__name__)


class ASRStub:
    """Stub ASR engine — returns dummy transcription.

    Will be replaced with fine-tuned Whisper-Large-V3 in Phase 3.
    """

    def __init__(self, model_path: str | None = None) -> None:
        self._model_path = model_path or os.environ.get(
            "ASR_MODEL_PATH",
            _DEFAULT_MODEL_PATH,
        )
        self._loaded = False

    async def load(self) -> None:
        """Load the ASR model (stub)."""
        logger.info("ASRStub.load — would load model from %s", self._model_path)
        self._loaded = True

    async def transcribe(self, audio_data: bytes) -> str:
        """Transcribe audio bytes to text (stub)."""
        logger.debug("ASRStub.transcribe — %d bytes", len(audio_data))
        return "[stub transcription]"

    async def unload(self) -> None:
        """Release model resources."""
        self._loaded = False
        logger.info("ASRStub unloaded")
