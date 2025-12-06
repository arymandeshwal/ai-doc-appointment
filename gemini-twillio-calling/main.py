"""
FastAPI server for Twilio-Gemini voice integration.

Endpoints:
- POST /outgoing-call: TwiML webhook for outgoing calls
- WebSocket /media-stream: Bidirectional audio stream handler
- POST /api/initiate-call: Initiate a call to a doctor's office
- GET /api/call-status/{call_sid}: Get call status and result
- GET /api/call-events/{call_sid}: SSE stream for real-time call events
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import Response, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from twilio.rest import Client
from pydantic import BaseModel

from config import SERVER_HOST, SERVER_PORT, NGROK_URL, LOG_LEVEL, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER
from audio_utils import StreamingAudioConverter
from gemini_client import GeminiLiveClient
from tools import execute_tool
from conversation_logger import ConversationLogger

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Gemini-Twilio Voice Integration")

# Add CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Twilio client for call control
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Global state for tracking calls (call_sid -> call state)
call_states: Dict[str, Dict[str, Any]] = {}


# Pydantic models for API
class InitiateCallRequest(BaseModel):
    doctor_name: str
    doctor_phone: str = "+4915510744774"  # Default test number
    patient_name: str = "Aryman Deshwal"


class CallStatusResponse(BaseModel):
    call_sid: str
    status: str
    events: list
    result: Optional[dict] = None


def add_call_event(call_sid: str, event: dict) -> None:
    """Add an event to a call's event list for SSE streaming."""
    if call_sid in call_states:
        call_states[call_sid]["events"].append(event)
        logger.info(f"Added event to call {call_sid}: {event}")


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
    - Executes tools (calendar checks, booking)
    - Handles call termination
    """
    await websocket.accept()
    logger.info("Twilio WebSocket connected")

    stream_sid: str = ""
    call_sid: str = ""
    gemini_client: GeminiLiveClient = None
    audio_converter = StreamingAudioConverter()
    should_end_call = False
    conversation_logger: ConversationLogger = None

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

    async def handle_tool_call(tool_name: str, args: dict) -> dict:
        """Execute a tool and return the result."""
        nonlocal conversation_logger, call_sid
        logger.info(f"Executing tool: {tool_name}")

        # Push event to frontend via call_states
        if call_sid and call_sid in call_states:
            add_call_event(call_sid, {
                "type": "tool_call",
                "tool": tool_name,
                "args": args,
                "status": "executing"
            })

        # Run synchronous tool in executor to not block
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, execute_tool, tool_name, args)
        logger.info(f"Tool result: {result}")

        # Log tool call to conversation transcript
        if conversation_logger:
            conversation_logger.log_tool_call(tool_name, args, result)

        # Push tool result to frontend
        if call_sid and call_sid in call_states:
            event = {
                "type": "tool_call",
                "tool": tool_name,
                "result": result
            }
            add_call_event(call_sid, event)

            # If booking was successful, store the result
            if tool_name == "book_appointment" and result.get("success"):
                call_states[call_sid]["result"] = {
                    "type": "call_ended",
                    "outcome": "success",
                    "details": {
                        "date": result.get("date"),
                        "time": result.get("time"),
                        "doctor_name": call_states[call_sid].get("doctor_name"),
                        "event_id": result.get("event_id"),
                    }
                }

        return result

    async def handle_end_call(reason: str) -> None:
        """Handle request to end the call."""
        nonlocal should_end_call, call_sid
        logger.info(f"End call requested: {reason}")
        should_end_call = True

        # Update call state for frontend
        if call_sid and call_sid in call_states:
            state = call_states[call_sid]

            # Determine outcome based on reason and whether booking succeeded
            if state.get("result") and state["result"].get("outcome") == "success":
                # Booking was successful
                state["status"] = "completed"
                add_call_event(call_sid, {
                    "type": "status",
                    "message": "Appointment booked successfully!"
                })
            else:
                # No successful booking
                state["status"] = "ended"
                state["result"] = {
                    "type": "call_ended",
                    "outcome": "failed",
                    "reason": reason or "no_booking"
                }
                add_call_event(call_sid, {
                    "type": "status",
                    "message": f"Call ended: {reason}"
                })

        # Give a moment for final audio to play
        await asyncio.sleep(2)

        # End the call via Twilio API
        if call_sid:
            try:
                twilio_client.calls(call_sid).update(status="completed")
                logger.info(f"Call {call_sid} terminated successfully")
            except Exception as e:
                logger.error(f"Failed to terminate call: {e}")

    def log_ai_audio(audio_b64: str) -> None:
        """Callback to log AI audio to transcript."""
        if conversation_logger:
            conversation_logger.log_ai_audio(audio_b64)

    try:
        # Initialize Gemini client with callbacks
        gemini_client = GeminiLiveClient(
            on_audio_response=send_audio_to_twilio,
            on_tool_call=handle_tool_call,
            on_end_call=handle_end_call,
            on_ai_audio=log_ai_audio
        )

        async for message in websocket.iter_text():
            if should_end_call:
                break

            data = json.loads(message)
            event = data.get("event")

            if event == "connected":
                logger.info("Twilio stream connected")

            elif event == "start":
                # Extract stream SID and call SID
                stream_sid = data.get("streamSid", "")
                start_data = data.get("start", {})
                call_sid = start_data.get("callSid", "")

                logger.info(f"Stream started: {stream_sid}")
                logger.info(f"Call SID: {call_sid}")
                logger.debug(f"Media format: {start_data.get('mediaFormat')}")

                # Update call state for frontend
                if call_sid in call_states:
                    call_states[call_sid]["status"] = "connected"
                    add_call_event(call_sid, {
                        "type": "status",
                        "message": "Connected! AI is speaking..."
                    })

                # Initialize conversation logger
                conversation_logger = ConversationLogger(call_sid, stream_sid)

                # Connect to Gemini now that we have the stream
                connected = await gemini_client.connect()
                if not connected:
                    logger.error("Failed to connect to Gemini")
                    if call_sid in call_states:
                        call_states[call_sid]["status"] = "failed"
                        add_call_event(call_sid, {
                            "type": "status",
                            "message": "Failed to connect to AI"
                        })
                    break

                # Make Gemini start the conversation
                await gemini_client.start_conversation()

            elif event == "media":
                # Extract and convert audio
                media_data = data.get("media", {})
                payload = media_data.get("payload", "")

                if payload:
                    # Log user audio to transcript
                    if conversation_logger:
                        conversation_logger.log_user_audio(payload)

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
        # Save conversation transcript
        if conversation_logger:
            try:
                filepath = conversation_logger.save()
                logger.info(f"Transcript saved: {filepath}")
            except Exception as e:
                logger.error(f"Failed to save transcript: {e}")

        # Clean up Gemini connection
        if gemini_client:
            await gemini_client.disconnect()
        logger.info("Media stream session ended")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# ============== Frontend Integration API ==============

@app.post("/api/initiate-call")
async def initiate_call(request: InitiateCallRequest):
    """
    Initiate a call to a doctor's office.

    Returns the call_sid which can be used to track the call status.
    """
    if not NGROK_URL:
        return {"error": "NGROK_URL not configured. Start ngrok first."}

    webhook_url = f"{NGROK_URL}/outgoing-call"

    logger.info(f"Initiating call to {request.doctor_phone} for {request.doctor_name}")

    try:
        call = twilio_client.calls.create(
            url=webhook_url,
            to=request.doctor_phone,
            from_=TWILIO_PHONE_NUMBER,
        )

        # Initialize call state tracking
        call_states[call.sid] = {
            "status": "initiated",
            "doctor_name": request.doctor_name,
            "patient_name": request.patient_name,
            "events": [{"type": "status", "message": "Call initiated..."}],
            "result": None,
            "event_index": 0,  # For SSE tracking
        }

        logger.info(f"Call initiated with SID: {call.sid}")

        return {
            "call_sid": call.sid,
            "status": "initiated",
            "message": f"Calling {request.doctor_name}..."
        }

    except Exception as e:
        logger.error(f"Failed to initiate call: {e}")
        return {"error": str(e)}


@app.get("/api/call-status/{call_sid}")
async def get_call_status(call_sid: str):
    """Get the current status of a call."""
    if call_sid not in call_states:
        return {"error": "Call not found", "call_sid": call_sid}

    state = call_states[call_sid]
    return {
        "call_sid": call_sid,
        "status": state["status"],
        "doctor_name": state.get("doctor_name"),
        "events": state["events"],
        "result": state.get("result"),
    }


@app.get("/api/call-events/{call_sid}")
async def call_events_sse(call_sid: str):
    """
    Server-Sent Events endpoint for real-time call updates.

    Frontend subscribes to this to get live updates as the call progresses.
    """
    async def event_generator():
        if call_sid not in call_states:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Call not found'})}\n\n"
            return

        last_index = 0
        max_wait = 300  # 5 minutes max
        wait_count = 0

        while wait_count < max_wait:
            state = call_states.get(call_sid)
            if not state:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Call state lost'})}\n\n"
                break

            # Send any new events
            events = state["events"]
            while last_index < len(events):
                event = events[last_index]
                yield f"data: {json.dumps(event)}\n\n"
                last_index += 1

            # Check if call ended
            if state["status"] in ["ended", "failed", "completed"]:
                # Send final result
                if state.get("result"):
                    yield f"data: {json.dumps(state['result'])}\n\n"
                break

            await asyncio.sleep(0.5)
            wait_count += 0.5

        # Clean up old call state after streaming ends (keep for 5 minutes)
        # We don't delete immediately in case frontend reconnects

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.get("/")
async def root():
    """Root endpoint with info."""
    return {
        "service": "Gemini-Twilio Voice Integration",
        "endpoints": {
            "/outgoing-call": "POST - TwiML webhook for outgoing calls",
            "/media-stream": "WebSocket - Bidirectional audio stream",
            "/health": "GET - Health check",
            "/api/initiate-call": "POST - Initiate a call (frontend integration)",
            "/api/call-status/{call_sid}": "GET - Get call status",
            "/api/call-events/{call_sid}": "GET - SSE stream for real-time events",
        },
        "features": [
            "Real-time voice conversation with Gemini AI",
            "Calendar availability checking",
            "Appointment booking",
            "Automatic call termination",
            "Frontend integration via REST API + SSE",
        ]
    }


if __name__ == "__main__":
    import uvicorn

    if not NGROK_URL:
        logger.warning("NGROK_URL not detected! Make sure ngrok is running: ngrok http 8080")
    else:
        logger.info(f"Using ngrok URL: {NGROK_URL}")

    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)
