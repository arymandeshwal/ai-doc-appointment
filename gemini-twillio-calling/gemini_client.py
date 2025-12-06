"""Gemini Live API WebSocket client for real-time audio conversations."""

import asyncio
import json
import base64
import logging
from typing import Callable, Optional, Awaitable, Any
import websockets
from websockets.asyncio.client import ClientConnection

from config import GEMINI_WS_URL, GEMINI_MODEL, get_system_instruction
from audio_utils import gemini_audio_to_base64
from tools import TOOL_DEFINITIONS

logger = logging.getLogger(__name__)


class GeminiLiveClient:
    """
    Manages WebSocket connection to Gemini Live API.

    Handles:
    - Session setup with configuration and tools
    - Sending audio in real-time
    - Receiving and forwarding audio responses
    - Tool call handling
    """

    def __init__(
        self,
        on_audio_response: Callable[[bytes], Awaitable[None]],
        on_tool_call: Optional[Callable[[str, dict], Awaitable[dict]]] = None,
        on_end_call: Optional[Callable[[str], Awaitable[None]]] = None,
        on_ai_audio: Optional[Callable[[str], None]] = None,
        user_info: Optional[dict] = None
    ):
        """
        Initialize Gemini client.

        Args:
            on_audio_response: Async callback invoked with PCM audio bytes
                               when Gemini sends audio response
            on_tool_call: Async callback for tool execution. Receives (tool_name, args),
                          returns result dict
            on_end_call: Async callback when end_call tool is invoked
            on_ai_audio: Optional sync callback for logging AI audio (receives base64 string)
            user_info: Optional dict with patient info for system instruction:
                       - patient_name: Patient's full name
                       - date_of_birth: Patient's DOB
                       - symptoms: Patient's symptoms
                       - doctor_name: Doctor being called
                       - insurance_type: 'public', 'private', or 'none'
        """
        self.ws: Optional[ClientConnection] = None
        self.on_audio_response = on_audio_response
        self.on_tool_call = on_tool_call
        self.on_end_call = on_end_call
        self.on_ai_audio = on_ai_audio
        self.user_info = user_info
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

            # Build tools list for Gemini
            tools_config = [{
                "functionDeclarations": TOOL_DEFINITIONS
            }]

            # Send setup message with tools
            # Get fresh system instruction with current date/time and user info
            system_instruction = get_system_instruction(self.user_info)

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
                        "parts": [{"text": system_instruction}]
                    },
                    "tools": tools_config
                }
            }

            await self.ws.send(json.dumps(setup_message))

            # Wait for setup confirmation
            response = await self.ws.recv()
            response_data = json.loads(response)

            if "setupComplete" in response_data:
                logger.info("Gemini session setup complete (with tools)")
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

    async def send_tool_response(self, function_call_id: str, result: dict) -> None:
        """
        Send tool execution result back to Gemini.

        Args:
            function_call_id: The ID of the function call to respond to
            result: The result dictionary from tool execution
        """
        if not self._connected or not self.ws:
            return

        message = {
            "toolResponse": {
                "functionResponses": [{
                    "id": function_call_id,
                    "response": result
                }]
            }
        }

        try:
            await self.ws.send(json.dumps(message))
            logger.info(f"Sent tool response for {function_call_id}")
        except Exception as e:
            logger.error(f"Error sending tool response: {e}")

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

            # Handle tool calls
            if "toolCall" in data:
                await self._handle_tool_call(data["toolCall"])
                return

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

                            # Log AI audio if callback provided
                            if self.on_ai_audio:
                                self.on_ai_audio(audio_b64)

                            await self.on_audio_response(audio_bytes)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini message: {e}")
        except Exception as e:
            logger.error(f"Error handling Gemini message: {e}")

    async def _handle_tool_call(self, tool_call: dict) -> None:
        """
        Handle a tool call from Gemini.

        Args:
            tool_call: The toolCall object from Gemini
        """
        function_calls = tool_call.get("functionCalls", [])

        for fc in function_calls:
            tool_name = fc.get("name")
            tool_args = fc.get("args", {})
            call_id = fc.get("id")

            logger.info(f"Tool call received: {tool_name}({tool_args})")

            # Special handling for end_call
            if tool_name == "end_call":
                reason = tool_args.get("reason", "conversation_complete")
                logger.info(f"End call requested: {reason}")

                # Send success response first
                await self.send_tool_response(call_id, {
                    "success": True,
                    "message": "Call will be ended"
                })

                # Then trigger the end call callback
                if self.on_end_call:
                    await self.on_end_call(reason)
                return

            # Execute other tools via callback
            if self.on_tool_call:
                result = await self.on_tool_call(tool_name, tool_args)
                await self.send_tool_response(call_id, result)
            else:
                # No tool handler configured
                await self.send_tool_response(call_id, {
                    "error": "Tool execution not configured"
                })

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
