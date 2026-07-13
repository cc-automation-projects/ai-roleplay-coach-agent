"""Tests for LiveKit stubs — edge cases included."""

import asyncio
import logging

import pytest

logger = logging.getLogger(__name__)


class TestEchoAgent:
    @pytest.mark.asyncio
    async def test_start_stop(self):
        from infrastructure.livekit.echo_agent import EchoAgent

        agent = EchoAgent()
        await agent.start()
        assert await agent.health() is True
        await agent.stop()

    @pytest.mark.asyncio
    async def test_echo_audio(self):
        from infrastructure.livekit.echo_agent import EchoAgent

        agent = EchoAgent()
        data = b"test audio bytes"
        result = await agent.echo_audio(data)
        assert result == data

    @pytest.mark.asyncio
    async def test_echo_empty_audio(self):
        """Edge: empty audio bytes should echo back as-is."""
        from infrastructure.livekit.echo_agent import EchoAgent

        agent = EchoAgent()
        result = await agent.echo_audio(b"")
        assert result == b""

    @pytest.mark.asyncio
    async def test_echo_large_audio(self):
        """Edge: large audio payload (1 MB) should not crash."""
        from infrastructure.livekit.echo_agent import EchoAgent

        agent = EchoAgent()
        data = b"x" * 1_048_576
        result = await agent.echo_audio(data)
        assert len(result) == 1_048_576

    @pytest.mark.asyncio
    async def test_stop_before_start(self):
        """Edge: calling stop without start should not raise."""
        from infrastructure.livekit.echo_agent import EchoAgent

        agent = EchoAgent()
        await agent.stop()  # no-op, must not crash

    @pytest.mark.asyncio
    async def test_health_default(self):
        """Edge: health before start returns True (stub behaviour)."""
        from infrastructure.livekit.echo_agent import EchoAgent

        agent = EchoAgent()
        assert await agent.health() is True

    @pytest.mark.asyncio
    async def test_concurrent_echo(self):
        """Edge: concurrent echo_audio calls should interleave safely."""
        from infrastructure.livekit.echo_agent import EchoAgent

        agent = EchoAgent()
        results = await asyncio.gather(
            agent.echo_audio(b"aaa"),
            agent.echo_audio(b"bbb"),
            agent.echo_audio(b"ccc"),
        )
        assert results == [b"aaa", b"bbb", b"ccc"]


class TestASRStub:
    @pytest.mark.asyncio
    async def test_transcribe(self):
        from infrastructure.livekit.asr_stub import ASRStub

        stub = ASRStub()
        await stub.load()
        text = await stub.transcribe(b"audio data")
        assert isinstance(text, str)
        assert len(text) > 0
        await stub.unload()

    @pytest.mark.asyncio
    async def test_transcribe_empty_audio(self):
        """Edge: empty audio returns stub transcription (no crash)."""
        from infrastructure.livekit.asr_stub import ASRStub

        stub = ASRStub()
        await stub.load()
        text = await stub.transcribe(b"")
        assert isinstance(text, str)
        assert len(text) > 0  # stub always returns placeholder
        await stub.unload()

    @pytest.mark.asyncio
    async def test_transcribe_large_audio(self):
        """Edge: 10 MB audio should not crash."""
        from infrastructure.livekit.asr_stub import ASRStub

        stub = ASRStub()
        await stub.load()
        text = await stub.transcribe(b"x" * 10_485_760)
        assert isinstance(text, str)
        await stub.unload()

    @pytest.mark.asyncio
    async def test_default_model_path(self):
        """Edge: default model path should be set from constant."""
        from infrastructure.livekit.asr_stub import ASRStub

        stub = ASRStub()
        assert stub._model_path is not None
        assert isinstance(stub._model_path, str)


class TestTTSStub:
    @pytest.mark.asyncio
    async def test_synthesize(self):
        from infrastructure.livekit.tts_stub import TTSStub

        stub = TTSStub()
        await stub.load()
        audio = await stub.synthesize("Hello world")
        assert isinstance(audio, bytes)
        await stub.unload()

    @pytest.mark.asyncio
    async def test_synthesize_empty_text(self):
        """Edge: empty text returns stub audio bytes (no crash)."""
        from infrastructure.livekit.tts_stub import TTSStub

        stub = TTSStub()
        await stub.load()
        audio = await stub.synthesize("")
        assert isinstance(audio, bytes)
        await stub.unload()

    @pytest.mark.asyncio
    async def test_synthesize_long_text(self):
        """Edge: very long text (10k chars) should not crash."""
        from infrastructure.livekit.tts_stub import TTSStub

        stub = TTSStub()
        await stub.load()
        audio = await stub.synthesize("Hello world! " * 1_000)
        assert isinstance(audio, bytes)
        await stub.unload()

    @pytest.mark.asyncio
    async def test_synthesize_special_chars(self):
        """Edge: special characters, unicode, emoji."""
        from infrastructure.livekit.tts_stub import TTSStub

        stub = TTSStub()
        await stub.load()
        audio = await stub.synthesize("Café résumé 日本語 😊 \n\t")
        assert isinstance(audio, bytes)
        await stub.unload()

    @pytest.mark.asyncio
    async def test_unload_without_load(self):
        """Edge: unload without load should not crash."""
        from infrastructure.livekit.tts_stub import TTSStub

        stub = TTSStub()
        await stub.unload()  # no-op, must not crash

    @pytest.mark.asyncio
    async def test_default_model_path(self):
        """Edge: default model path should be set from constant."""
        from infrastructure.livekit.tts_stub import TTSStub

        stub = TTSStub()
        assert stub._model_path is not None
        assert isinstance(stub._model_path, str)
