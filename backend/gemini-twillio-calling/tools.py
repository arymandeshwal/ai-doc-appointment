"""
Tool definitions and execution handlers for Gemini Live API.

Tools:
- check_availability: Check if Aryman is available at a proposed appointment time
- book_appointment: Book an appointment in the calendar
- end_call: End the phone call
"""

import datetime
import os
import logging
from typing import Any

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

# Google Calendar API scope
SCOPES = ["https://www.googleapis.com/auth/calendar"]

# Calendar ID to use (user's email or 'primary' if delegated)
# For service accounts, you need to share the calendar with the service account email
CALENDAR_ID = os.environ.get("GOOGLE_CALENDAR_ID", "primary")


def _get_service_account_info() -> dict:
    """Build service account info dict from environment variables."""
    private_key = os.environ.get("GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY", "")
    # Handle escaped newlines in the private key
    if private_key:
        private_key = private_key.replace("\\n", "\n")

    return {
        "type": "service_account",
        "project_id": os.environ.get("GOOGLE_SERVICE_ACCOUNT_PROJECT_ID", ""),
        "private_key_id": os.environ.get("GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY_ID", ""),
        "private_key": private_key,
        "client_email": os.environ.get("GOOGLE_SERVICE_ACCOUNT_CLIENT_EMAIL", ""),
        "client_id": os.environ.get("GOOGLE_SERVICE_ACCOUNT_CLIENT_ID", ""),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "universe_domain": "googleapis.com"
    }


# =============================================================================
# Tool Definitions for Gemini
# =============================================================================

TOOL_DEFINITIONS = [
    {
        "name": "check_availability",
        "description": "Check if Aryman Deshwal is available at the proposed appointment date and time. Use this when the doctor offers an appointment time.",
        "parameters": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "The proposed date in YYYY-MM-DD format (e.g., 2024-12-10)"
                },
                "time": {
                    "type": "string",
                    "description": "The proposed time in HH:MM format, 24-hour (e.g., 15:00 for 3 PM)"
                },
                "duration_minutes": {
                    "type": "integer",
                    "description": "Duration of the appointment in minutes. Default is 30."
                }
            },
            "required": ["date", "time"]
        }
    },
    {
        "name": "book_appointment",
        "description": "Book and confirm an appointment in the calendar after availability is confirmed.",
        "parameters": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "The appointment date in YYYY-MM-DD format"
                },
                "time": {
                    "type": "string",
                    "description": "The appointment time in HH:MM format, 24-hour"
                },
                "doctor_name": {
                    "type": "string",
                    "description": "Name of the doctor or clinic"
                },
                "duration_minutes": {
                    "type": "integer",
                    "description": "Duration of the appointment in minutes. Default is 30."
                },
                "notes": {
                    "type": "string",
                    "description": "Any additional notes about the appointment"
                }
            },
            "required": ["date", "time", "doctor_name"]
        }
    },
    {
        "name": "end_call",
        "description": "End the phone call. IMPORTANT: You MUST speak a verbal goodbye message BEFORE calling this tool. Say something like 'Thank you, have a great day, goodbye!' first, then call this tool. Never call this tool without saying goodbye first.",
        "parameters": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Reason for ending the call (e.g., 'appointment_booked', 'no_availability', 'conversation_complete')"
                }
            },
            "required": ["reason"]
        }
    }
]


# =============================================================================
# Google Calendar Functions
# =============================================================================

def get_calendar_service():
    """Authenticate using service account and return a Google Calendar service object."""
    try:
        service_account_info = _get_service_account_info()

        # Check if required credentials are present
        if not service_account_info.get("private_key") or not service_account_info.get("client_email"):
            logger.warning("Google Calendar credentials not configured in environment variables")
            return None

        creds = service_account.Credentials.from_service_account_info(
            service_account_info, scopes=SCOPES
        )

        service = build("calendar", "v3", credentials=creds)
        return service

    except Exception as e:
        logger.error(f"Failed to create calendar service: {e}")
        return None


def check_availability(date: str, time: str, duration_minutes: int = 30) -> dict:
    """
    Check if Aryman is available at the proposed appointment time.

    Args:
        date: Date in YYYY-MM-DD format
        time: Time in HH:MM format (24-hour)
        duration_minutes: Duration of appointment

    Returns:
        dict with 'available' (bool) and 'conflicts' (list) or 'error' (str)
    """
    try:
        # Parse date and time
        event_datetime = datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        # Add timezone (assuming local timezone)
        event_datetime = event_datetime.replace(tzinfo=datetime.timezone.utc)

        service = get_calendar_service()
        if not service:
            return {"available": True, "conflicts": [], "note": "Calendar not configured, assuming available"}

        # Define time window
        start_time = event_datetime.isoformat()
        end_time = (event_datetime + datetime.timedelta(minutes=duration_minutes)).isoformat()

        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=start_time,
            timeMax=end_time,
            singleEvents=True,
            orderBy="startTime"
        ).execute()

        raw_events = events_result.get("items", [])

        if not raw_events:
            return {
                "available": True,
                "conflicts": [],
                "message": f"Aryman is available on {date} at {time}"
            }

        # There are conflicts
        conflicts = []
        for event in raw_events:
            if "dateTime" in event["start"]:
                ev_start = event["start"]["dateTime"]
                ev_end = event["end"]["dateTime"]
            else:
                ev_start = event["start"]["date"]
                ev_end = event["end"]["date"]

            conflicts.append({
                "summary": event.get("summary", "Busy"),
                "start": ev_start,
                "end": ev_end
            })

        return {
            "available": False,
            "conflicts": conflicts,
            "message": f"Aryman has a conflict on {date} at {time}. Please ask for another time."
        }

    except ValueError as e:
        return {"available": False, "error": f"Invalid date/time format: {e}"}
    except HttpError as e:
        logger.error(f"Calendar API error: {e}")
        return {"available": True, "conflicts": [], "note": "Calendar check failed, assuming available"}


def book_appointment(date: str, time: str, doctor_name: str,
                     duration_minutes: int = 30, notes: str = "") -> dict:
    """
    Book an appointment in Google Calendar.

    Args:
        date: Date in YYYY-MM-DD format
        time: Time in HH:MM format (24-hour)
        doctor_name: Name of the doctor/clinic
        duration_minutes: Duration of appointment
        notes: Additional notes

    Returns:
        dict with 'success' (bool) and 'event_id' or 'error'
    """
    try:
        event_datetime = datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        event_datetime = event_datetime.replace(tzinfo=datetime.timezone.utc)
        end_datetime = event_datetime + datetime.timedelta(minutes=duration_minutes)

        service = get_calendar_service()
        if not service:
            return {"success": False, "error": "Calendar not configured"}

        event = {
            "summary": f"Doctor Appointment - {doctor_name}",
            "description": f"Appointment booked by AI assistant.\n{notes}",
            "start": {
                "dateTime": event_datetime.isoformat(),
                "timeZone": "UTC"
            },
            "end": {
                "dateTime": end_datetime.isoformat(),
                "timeZone": "UTC"
            },
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": 60},
                    {"method": "popup", "minutes": 10}
                ]
            }
        }

        created_event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()

        return {
            "success": True,
            "event_id": created_event.get("id"),
            "message": f"Appointment booked with {doctor_name} on {date} at {time}"
        }

    except ValueError as e:
        return {"success": False, "error": f"Invalid date/time format: {e}"}
    except HttpError as e:
        logger.error(f"Calendar API error: {e}")
        return {"success": False, "error": str(e)}


def end_call(reason: str) -> dict:
    """
    Signal to end the phone call.

    Args:
        reason: Reason for ending the call

    Returns:
        dict indicating the call should end
    """
    return {
        "action": "end_call",
        "reason": reason
    }


# =============================================================================
# Tool Execution Router
# =============================================================================

def execute_tool(tool_name: str, args: dict) -> dict:
    """
    Execute a tool by name with given arguments.

    Args:
        tool_name: Name of the tool to execute
        args: Arguments for the tool

    Returns:
        Result dictionary from the tool
    """
    logger.info(f"Executing tool: {tool_name} with args: {args}")

    if tool_name == "check_availability":
        return check_availability(
            date=args.get("date"),
            time=args.get("time"),
            duration_minutes=args.get("duration_minutes", 30)
        )

    elif tool_name == "book_appointment":
        return book_appointment(
            date=args.get("date"),
            time=args.get("time"),
            doctor_name=args.get("doctor_name"),
            duration_minutes=args.get("duration_minutes", 30),
            notes=args.get("notes", "")
        )

    elif tool_name == "end_call":
        return end_call(reason=args.get("reason", "conversation_complete"))

    else:
        logger.warning(f"Unknown tool: {tool_name}")
        return {"error": f"Unknown tool: {tool_name}"}
