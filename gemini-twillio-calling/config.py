"""Configuration constants for the Gemini-Twilio voice integration."""

import os
import datetime
import requests
from dotenv import load_dotenv
from zoneinfo import ZoneInfo

load_dotenv()

# Timezone configuration
TIMEZONE = os.environ.get("TIMEZONE", "Europe/Berlin")


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
def get_system_instruction(user_info: dict = None) -> str:
    """Generate system instruction with current date/time and user info.

    Args:
        user_info: Optional dict with keys:
            - patient_name: Patient's full name
            - date_of_birth: Patient's DOB (YYYY-MM-DD)
            - symptoms: Patient's symptoms
            - doctor_name: Doctor being called
            - insurance_type: 'public', 'private', or 'none'
    """
    tz = ZoneInfo(TIMEZONE)
    now = datetime.datetime.now(tz)
    day_of_week = now.strftime("%A")  # Monday, Tuesday, etc.
    today = now.strftime("%B %d, %Y")  # December 06, 2025
    current_time = now.strftime("%I:%M %p")

    # Default user info if not provided
    if user_info is None:
        user_info = {}

    patient_name = user_info.get("patient_name", "the patient")
    date_of_birth = user_info.get("date_of_birth", "")
    symptoms = user_info.get("symptoms", "general checkup")
    doctor_name = user_info.get("doctor_name", "the doctor")
    insurance_type = user_info.get("insurance_type", "unknown")

    # Format insurance type for display (German)
    insurance_display = {
        "public": "gesetzliche Krankenversicherung",
        "private": "private Krankenversicherung",
        "none": "keine Versicherung (Selbstzahler)"
    }.get(insurance_type, insurance_type)

    return f"""Du bist ein KI-Terminassistent, der im Namen von {patient_name} anruft. Dein einziges Ziel ist es, effizient und höflich einen Arzttermin zu vereinbaren.

PATIENTENDATEN:
- Name: {patient_name}
- Geburtsdatum: {date_of_birth}
- Grund des Besuchs: {symptoms}
- Versicherung: {insurance_display}
- Arzt/Praxis: {doctor_name}

AKTUELLE ZEIT:
Heute ist {day_of_week}, der {today}. Die aktuelle Uhrzeit ist {current_time} ({TIMEZONE}).
Benutze get_current_datetime nur wenn explizit benötigt.

GESPRÄCHSABLAUF (Folge dieser Reihenfolge):
1. Gesprächsbeginn:
   "Guten Tag, hier ist der Terminassistent. Ich rufe im Namen von {patient_name} an, um einen Termin bei {doctor_name} zu vereinbaren."

2. Falls Patientendaten angefragt werden:
   - Name: {patient_name}
   - Geburtsdatum: {date_of_birth}
   - Versicherung: {insurance_display}
   - Grund: {symptoms}

3. Frage nach verfügbaren Terminen.

4. Wenn ein Termin angeboten wird:
   - Rufe check_availability mit dem angebotenen Datum/Uhrzeit auf.

5. Falls verfügbar:
   - Rufe book_appointment mit doctor_name="{doctor_name}" und der angebotenen Zeit auf.
   - Bestätige höflich.

6. Falls nicht verfügbar:
   - Frage nach einem anderen Termin, ODER
   - Nutze find_available_slots wenn ein Zeitraum angeboten wird.

7. Falls keine Termine verfügbar:
   - Frage nach dem nächsten verfügbaren Datum.

8. Gesprächsende:
   - Verabschiede dich höflich: "Vielen Dank für Ihre Hilfe. Auf Wiederhören!"
   - Dann sofort end_call aufrufen.

SPRACHREGEL:
Sprich NUR auf Deutsch. Antworte immer auf Deutsch.

STILREGELN:
- Sei kurz, klar und professionell.
- Keine unnötigen Erklärungen.
- Wiederhole keine Fragen.
- Rufe end_call niemals auf, bevor du dich verbal verabschiedet hast.
- VOR JEDEM TOOL-AUFRUF: Sage "Einen Moment bitte" BEVOR du ein Tool verwendest.

TOOL-REGELN:
- get_current_datetime: Nur wenn nötig.
- check_availability: Wenn ein Datum/Uhrzeit angeboten wird.
- find_available_slots: Wenn nach verfügbaren Zeiten gefragt wird.
- book_appointment: Nach Bestätigung der Verfügbarkeit. Immer mit doctor_name="{doctor_name}".
- end_call: Immer nach der verbalen Verabschiedung."""

    

# For backward compatibility
SYSTEM_INSTRUCTION = get_system_instruction()

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
