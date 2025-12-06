"""
FastAPI server for Twilio-Gemini voice integration.

Endpoints:
- POST /outgoing-call: TwiML webhook for outgoing calls
- WebSocket /media-stream: Bidirectional audio stream handler
"""

import asyncio
import json
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import Response

from config import SERVER_HOST, SERVER_PORT, NGROK_URL, LOG_LEVEL
from audio_utils import StreamingAudioConverter
from gemini_client import GeminiLiveClient

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Gemini-Twilio Voice Integration")


@app.post("/outgoing-call")
async def outgoing_call(request: Request):
    """
    TwiML webhook for outgoing calls.

    Returns TwiML that connects the call to our WebSocket stream.
    """
    logger.info(">>> Webhook /outgoing-call hit!")

    # Construct WebSocket URL (wss for secure)
    ws_url = NGROK_URL.replace("https://", "wss://").replace("http://", "ws://")
    stream_url = f"{ws_url}/media-stream"

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Connected</Say>
    <Connect>
        <Stream url="{stream_url}" />
    </Connect>
    <Say>Disconnected</Say>
</Response>"""

    logger.info(f"Returning TwiML with stream URL: {stream_url}")
    return Response(content=twiml, media_type="application/xml")


@app.websocket("/media-stream")
async def media_stream(websocket: WebSocket):
    """
    WebSocket endpoint for Twilio Media Streams.

    Handles bidirectional audio:
    - Receives audio from phone (Twilio -> Gemini)
    - Sends AI responses back (Gemini -> Twilio)
    """
    await websocket.accept()
    logger.info("Twilio WebSocket connected")

    stream_sid: str = ""
    gemini_client: GeminiLiveClient = None
    audio_converter = StreamingAudioConverter()

    async def send_audio_to_twilio(pcm_bytes: bytes) -> None:
        """Callback to send Gemini audio to Twilio."""
        nonlocal stream_sid
        if not stream_sid:
            return

        # Convert Gemini PCM (24kHz) to Twilio mu-law (8kHz)
        mulaw_b64 = audio_converter.gemini_to_twilio(pcm_bytes)

        # Send to Twilio
        message = {
            "event": "media",
            "streamSid": stream_sid,
            "media": {
                "payload": mulaw_b64
            }
        }

        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending audio to Twilio: {e}")

    try:
        # Initialize Gemini client with callback
        gemini_client = GeminiLiveClient(on_audio_response=send_audio_to_twilio)

        async for message in websocket.iter_text():
            data = json.loads(message)
            event = data.get("event")

            if event == "connected":
                logger.info("Twilio stream connected")

            elif event == "start":
                # Extract stream SID for sending responses
                stream_sid = data.get("streamSid", "")
                start_data = data.get("start", {})
                logger.info(f"Stream started: {stream_sid}")
                logger.debug(f"Media format: {start_data.get('mediaFormat')}")

                # Connect to Gemini now that we have the stream
                connected = await gemini_client.connect()
                if not connected:
                    logger.error("Failed to connect to Gemini")
                    break

                # Make Gemini start the conversation
                await gemini_client.start_conversation()

            elif event == "media":
                # Extract and convert audio
                media_data = data.get("media", {})
                payload = media_data.get("payload", "")

                if payload:
                    # Convert Twilio mu-law (8kHz) to Gemini PCM (16kHz)
                    pcm_audio = audio_converter.twilio_to_gemini(payload)

                    # Send to Gemini
                    await gemini_client.send_audio(pcm_audio)

            elif event == "mark":
                # Audio playback completed
                mark_name = data.get("mark", {}).get("name", "")
                logger.debug(f"Mark received: {mark_name}")

            elif event == "stop":
                logger.info("Twilio stream stopped")
                break

    except WebSocketDisconnect:
        logger.info("Twilio WebSocket disconnected")
    except Exception as e:
        logger.error(f"Error in media stream handler: {e}")
    finally:
        # Clean up Gemini connection
        if gemini_client:
            await gemini_client.disconnect()
        logger.info("Media stream session ended")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/")
async def root():
    """Root endpoint with info."""
    return {
        "service": "Gemini-Twilio Voice Integration",
        "endpoints": {
            "/outgoing-call": "POST - TwiML webhook for outgoing calls",
            "/media-stream": "WebSocket - Bidirectional audio stream",
            "/health": "GET - Health check"
        }
    }


if __name__ == "__main__":
    import uvicorn

    if not NGROK_URL:
        logger.warning("NGROK_URL not set! Update .env with your ngrok URL")

    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)
