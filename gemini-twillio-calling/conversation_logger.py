"""
Conversation logger for capturing call transcripts.

Captures:
- User audio (from Twilio)
- AI audio (from Gemini)
- Tool calls with parameters and results
- Call metadata
"""

import os
import json
import datetime
import logging
from typing import Optional, Any
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

TIMEZONE = os.environ.get("TIMEZONE", "Europe/Berlin")
TRANSCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "transcripts")


class ConversationLogger:
    """Logger for capturing bidirectional conversation data."""

    def __init__(self, call_sid: str, stream_sid: str):
        """
        Initialize the conversation logger.

        Args:
            call_sid: Twilio call SID
            stream_sid: Twilio stream SID
        """
        self.call_sid = call_sid
        self.stream_sid = stream_sid
        self.tz = ZoneInfo(TIMEZONE)
        self.started_at = datetime.datetime.now(self.tz)
        self.ended_at: Optional[datetime.datetime] = None
        self.conversation: list[dict[str, Any]] = []
        self._sequence = 0

        # Ensure transcripts directory exists
        os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)

        logger.info(f"ConversationLogger initialized for call {call_sid}")

    def _next_sequence(self) -> int:
        """Get the next sequence number."""
        self._sequence += 1
        return self._sequence

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.datetime.now(self.tz).isoformat()

    def log_user_audio(self, audio_b64: str) -> None:
        """
        Log audio from the user (Twilio).

        Args:
            audio_b64: Base64-encoded mu-law audio from Twilio
        """
        self.conversation.append({
            "seq": self._next_sequence(),
            "timestamp": self._get_timestamp(),
            "type": "user_audio",
            "audio_b64": audio_b64,
            "format": "mulaw@8kHz"
        })

    def log_ai_audio(self, audio_b64: str) -> None:
        """
        Log audio from the AI (Gemini).

        Args:
            audio_b64: Base64-encoded PCM audio from Gemini
        """
        self.conversation.append({
            "seq": self._next_sequence(),
            "timestamp": self._get_timestamp(),
            "type": "ai_audio",
            "audio_b64": audio_b64,
            "format": "pcm@24kHz"
        })

    def log_tool_call(self, name: str, args: dict, result: dict) -> None:
        """
        Log a tool call with its arguments and result.

        Args:
            name: Tool name
            args: Tool arguments
            result: Tool result
        """
        self.conversation.append({
            "seq": self._next_sequence(),
            "timestamp": self._get_timestamp(),
            "type": "tool_call",
            "name": name,
            "args": args,
            "result": result
        })
        logger.info(f"Logged tool call: {name}")

    def save(self) -> str:
        """
        Save the conversation transcript to a JSON file.

        Returns:
            Path to the saved transcript file
        """
        self.ended_at = datetime.datetime.now(self.tz)

        transcript = {
            "call_metadata": {
                "call_sid": self.call_sid,
                "stream_sid": self.stream_sid,
                "started_at": self.started_at.isoformat(),
                "ended_at": self.ended_at.isoformat(),
                "duration_seconds": (self.ended_at - self.started_at).total_seconds(),
                "timezone": TIMEZONE
            },
            "conversation": self.conversation
        }

        # Generate filename with timestamp
        timestamp_str = self.started_at.strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp_str}_{self.call_sid}.json"
        filepath = os.path.join(TRANSCRIPTS_DIR, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(transcript, f, indent=2, ensure_ascii=False)

        logger.info(f"Conversation transcript saved to {filepath}")
        logger.info(f"Total events logged: {len(self.conversation)}")

        return filepath
