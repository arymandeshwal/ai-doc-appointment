"""Audio format conversion utilities for Twilio <-> Gemini integration."""

import audioop
import base64
from config import TWILIO_SAMPLE_RATE, GEMINI_INPUT_RATE, GEMINI_OUTPUT_RATE


def twilio_mulaw_to_gemini_pcm(mulaw_base64: str) -> bytes:
    """
    Convert Twilio's mu-law 8kHz audio to Gemini's PCM 16kHz format.

    Args:
        mulaw_base64: Base64-encoded mu-law audio from Twilio

    Returns:
        Raw PCM bytes at 16kHz, 16-bit, mono
    """
    # Decode base64 to raw mu-law bytes
    mulaw_bytes = base64.b64decode(mulaw_base64)

    # Convert mu-law to 16-bit linear PCM
    pcm_8k = audioop.ulaw2lin(mulaw_bytes, 2)

    # Upsample from 8kHz to 16kHz
    pcm_16k, _ = audioop.ratecv(pcm_8k, 2, 1, TWILIO_SAMPLE_RATE, GEMINI_INPUT_RATE, None)

    return pcm_16k


def gemini_pcm_to_twilio_mulaw(pcm_bytes: bytes) -> str:
    """
    Convert Gemini's PCM 24kHz audio to Twilio's mu-law 8kHz format.

    Args:
        pcm_bytes: Raw PCM bytes at 24kHz, 16-bit, mono from Gemini

    Returns:
        Base64-encoded mu-law audio for Twilio
    """
    # Downsample from 24kHz to 8kHz
    pcm_8k, _ = audioop.ratecv(pcm_bytes, 2, 1, GEMINI_OUTPUT_RATE, TWILIO_SAMPLE_RATE, None)

    # Convert 16-bit linear PCM to mu-law
    mulaw_bytes = audioop.lin2ulaw(pcm_8k, 2)

    # Encode as base64 for Twilio
    return base64.b64encode(mulaw_bytes).decode("utf-8")


def gemini_audio_to_base64(pcm_bytes: bytes) -> str:
    """Encode PCM audio as base64 for Gemini API."""
    return base64.b64encode(pcm_bytes).decode("utf-8")


class StreamingAudioConverter:
    """
    Maintains state for continuous audio streaming conversion.

    Use this class when converting audio in a streaming context
    to ensure smooth audio without artifacts at chunk boundaries.
    """

    def __init__(self):
        self.upsample_state = None
        self.downsample_state = None

    def twilio_to_gemini(self, mulaw_base64: str) -> bytes:
        """
        Convert Twilio mu-law to Gemini PCM with state continuity.

        Args:
            mulaw_base64: Base64-encoded mu-law audio chunk

        Returns:
            PCM bytes at 16kHz
        """
        mulaw_bytes = base64.b64decode(mulaw_base64)
        pcm_8k = audioop.ulaw2lin(mulaw_bytes, 2)
        pcm_16k, self.upsample_state = audioop.ratecv(
            pcm_8k, 2, 1, TWILIO_SAMPLE_RATE, GEMINI_INPUT_RATE, self.upsample_state
        )
        return pcm_16k

    def gemini_to_twilio(self, pcm_bytes: bytes) -> str:
        """
        Convert Gemini PCM to Twilio mu-law with state continuity.

        Args:
            pcm_bytes: PCM bytes at 24kHz from Gemini

        Returns:
            Base64-encoded mu-law audio
        """
        pcm_8k, self.downsample_state = audioop.ratecv(
            pcm_bytes, 2, 1, GEMINI_OUTPUT_RATE, TWILIO_SAMPLE_RATE, self.downsample_state
        )
        mulaw_bytes = audioop.lin2ulaw(pcm_8k, 2)
        return base64.b64encode(mulaw_bytes).decode("utf-8")

    def reset(self):
        """Reset converter state for a new stream."""
        self.upsample_state = None
        self.downsample_state = None
