"""Configuration constants for the Gemini-Twilio voice integration."""

import os
from dotenv import load_dotenv

load_dotenv()

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
NGROK_URL = os.environ.get("NGROK_URL", "")

# Audio Configuration
TWILIO_SAMPLE_RATE = 8000      # Twilio uses 8kHz mu-law
GEMINI_INPUT_RATE = 16000      # Gemini expects 16kHz PCM input
GEMINI_OUTPUT_RATE = 24000     # Gemini outputs 24kHz PCM

# AI Persona System Instruction
SYSTEM_INSTRUCTION = """You are a professional AI secretary calling on behalf of Aryman Deshwal to schedule a doctor's appointment.

Your task:
1. Introduce yourself warmly: "Hello, this is the appointment assistant calling on behalf of Mr. Aryman Deshwal. I'm calling to schedule a doctor's appointment."
2. Ask what appointment times are available
3. When they offer times, confirm the details (date, time)
4. Thank them politely and end the call professionally

Guidelines:
- Be warm, professional, and courteous
- Keep responses brief and natural
- If they ask questions about the patient, say you're just handling the scheduling
- If no appointments are available, politely ask about the next available date
- Talk in english"""

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
