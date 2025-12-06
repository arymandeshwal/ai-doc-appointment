"""Gemini Live API WebSocket client for real-time audio conversations."""

import asyncio
import json
import base64
import logging
from typing import Callable, Optional, Awaitable
import websockets
from websockets.asyncio.client import ClientConnection

from config import GEMINI_WS_URL, GEMINI_MODEL, SYSTEM_INSTRUCTION
from audio_utils import gemini_audio_to_base64

logger = logging.getLogger(__name__)


class GeminiLiveClient:
    """
    Manages WebSocket connection to Gemini Live API.

    Handles:
    - Session setup with configuration
    - Sending audio in real-time
    - Receiving and forwarding audio responses
    """

    def __init__(self, on_audio_response: Callable[[bytes], Awaitable[None]]):
        """
        Initialize Gemini client.

        Args:
            on_audio_response: Async callback invoked with PCM audio bytes
                               when Gemini sends audio response
        """
        self.ws: Optional[ClientConnection] = None
        self.on_audio_response = on_audio_response
        self._receive_task: Optional[asyncio.Task] = None
        self._connected = False

    async def connect(self) -> bool:
        """
        Establish WebSocket connection and send setup message.

        Returns:
            True if connection and setup successful, False otherwise
        """
        try:
            self.ws = await websockets.connect(GEMINI_WS_URL)
            logger.info("Connected to Gemini Live API")

            # Send setup message
            setup_message = {
                "setup": {
                    "model": GEMINI_MODEL,
                    "generationConfig": {
                        "responseModalities": ["AUDIO"],
                        "speechConfig": {
                            "voiceConfig": {
                                "prebuiltVoiceConfig": {
                                    "voiceName": "Kore"
                                }
                            }
                        }
                    },
                    "systemInstruction": {
                        "parts": [{"text": SYSTEM_INSTRUCTION}]
                    }
                }
            }

            await self.ws.send(json.dumps(setup_message))

            # Wait for setup confirmation
            response = await self.ws.recv()
            response_data = json.loads(response)

            if "setupComplete" in response_data:
                logger.info("Gemini session setup complete")
                self._connected = True

                # Start background task to receive responses
                self._receive_task = asyncio.create_task(self._receive_loop())
                return True
            else:
                logger.error(f"Unexpected setup response: {response_data}")
                return False

        except Exception as e:
            logger.error(f"Failed to connect to Gemini: {e}")
            return False

    async def send_audio(self, pcm_bytes: bytes) -> None:
        """
        Send audio chunk to Gemini.

        Args:
            pcm_bytes: Raw PCM audio bytes (16kHz, 16-bit, mono)
        """
        if not self._connected or not self.ws:
            return

        message = {
            "realtimeInput": {
                "mediaChunks": [{
                    "mimeType": "audio/pcm;rate=16000",
                    "data": gemini_audio_to_base64(pcm_bytes)
                }]
            }
        }

        try:
            await self.ws.send(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending audio to Gemini: {e}")

    async def send_text(self, text: str) -> None:
        """
        Send a text message to Gemini to trigger a response.

        Args:
            text: Text prompt to send
        """
        if not self._connected or not self.ws:
            return

        message = {
            "clientContent": {
                "turns": [{
                    "role": "user",
                    "parts": [{"text": text}]
                }],
                "turnComplete": True
            }
        }

        try:
            await self.ws.send(json.dumps(message))
            logger.info(f"Sent text to Gemini: {text}")
        except Exception as e:
            logger.error(f"Error sending text to Gemini: {e}")

    async def start_conversation(self) -> None:
        """Trigger Gemini to start the conversation by introducing itself."""
        await self.send_text("Start now. Introduce yourself and ask about available appointments.")

    async def _receive_loop(self) -> None:
        """Background task to receive and process Gemini responses."""
        try:
            async for message in self.ws:
                await self._handle_message(message)
        except websockets.ConnectionClosed:
            logger.info("Gemini connection closed")
        except Exception as e:
            logger.error(f"Error in Gemini receive loop: {e}")
        finally:
            self._connected = False

    async def _handle_message(self, message: str) -> None:
        """Process incoming message from Gemini."""
        try:
            data = json.loads(message)

            # Check for audio in serverContent.modelTurn.parts
            if "serverContent" in data:
                server_content = data["serverContent"]

                # Check for turn completion
                if server_content.get("turnComplete"):
                    logger.debug("Gemini turn complete")

                # Extract audio from model turn
                model_turn = server_content.get("modelTurn", {})
                parts = model_turn.get("parts", [])

                for part in parts:
                    if "inlineData" in part:
                        inline_data = part["inlineData"]
                        if inline_data.get("mimeType", "").startswith("audio/"):
                            # Decode audio and send to callback
                            audio_b64 = inline_data.get("data", "")
                            audio_bytes = base64.b64decode(audio_b64)
                            await self.on_audio_response(audio_bytes)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini message: {e}")
        except Exception as e:
            logger.error(f"Error handling Gemini message: {e}")

    async def disconnect(self) -> None:
        """Close the Gemini connection."""
        self._connected = False

        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass

        if self.ws:
            await self.ws.close()
            logger.info("Disconnected from Gemini")
