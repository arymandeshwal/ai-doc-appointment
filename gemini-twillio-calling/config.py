"""Configuration constants for the Gemini-Twilio voice integration."""

import os
import requests
from dotenv import load_dotenv

load_dotenv()


def get_ngrok_url() -> str:
    """
    Auto-detect ngrok URL from local API.
    Falls back to environment variable if ngrok API is not available.
    """
    # First check environment variable
    env_url = os.environ.get("NGROK_URL", "").strip()
    if env_url:
        return env_url

    # Try to get from ngrok local API
    try:
        response = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=2)
        tunnels = response.json().get("tunnels", [])
        for tunnel in tunnels:
            if tunnel.get("proto") == "https":
                return tunnel.get("public_url", "")
    except Exception:
        pass

    return ""


# Twilio Configuration
TWILIO_ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = os.environ["TWILIO_AUTH_TOKEN"]
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER", "+19297884861")

# Google Gemini Configuration
GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "models/gemini-2.0-flash-live-001")
GEMINI_WS_URL = f"wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent?key={GOOGLE_API_KEY}"

# Server Configuration
SERVER_HOST = os.environ.get("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.environ.get("SERVER_PORT", "8080"))
NGROK_URL = get_ngrok_url()

# Audio Configuration
TWILIO_SAMPLE_RATE = 8000      # Twilio uses 8kHz mu-law
GEMINI_INPUT_RATE = 16000      # Gemini expects 16kHz PCM input
GEMINI_OUTPUT_RATE = 24000     # Gemini outputs 24kHz PCM

# AI Persona System Instruction
SYSTEM_INSTRUCTION = """You are a professional AI secretary calling on behalf of Aryman Deshwal to schedule a doctor's appointment.

Your task:
1. Introduce yourself warmly: "Hello, this is the appointment assistant calling on behalf of Mr. Aryman Deshwal. I'm calling to schedule a doctor's appointment."
2. Ask what appointment times are available
3. When they offer a time, use the check_availability tool to verify Aryman is free
4. If available, use book_appointment to confirm the booking
5. If not available, politely ask for another time
6. When the conversation is complete, FIRST speak a polite goodbye message like "Thank you so much for your help. Have a wonderful day! Goodbye." and THEN call the end_call tool.

Tool Usage:
- check_availability: When they offer a date/time (e.g., "December 10th at 3pm"), call this tool with date="2024-12-10" and time="15:00"
- book_appointment: After availability is confirmed, book with the doctor's name
- end_call: Call this ONLY AFTER you have verbally said goodbye. Never call end_call without speaking a farewell first.

Guidelines:
- Be warm, professional, and courteous
- Keep responses brief and natural
- If they ask questions about the patient, say you're just handling the scheduling
- If no appointments are available, politely ask about the next available date
- Speak in English
- CRITICAL: You MUST speak a verbal goodbye message BEFORE calling the end_call tool. Do not just hang up silently."""

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
