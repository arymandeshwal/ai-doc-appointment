"""
Tool definitions and execution handlers for Gemini Live API.

Tools:
- get_current_datetime: Get the current date and time
- check_availability: Check if Aryman is available at a proposed appointment time
- find_available_slots: Search for available time slots within a date/time range
- book_appointment: Book an appointment in the calendar
"""

import datetime
import os
import logging
from typing import Any
from zoneinfo import ZoneInfo

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

# Google Calendar API scope
SCOPES = ["https://www.googleapis.com/auth/calendar"]

# Calendar ID to use (user's email or 'primary' if delegated)
# For service accounts, you need to share the calendar with the service account email
CALENDAR_ID = os.environ.get("GOOGLE_CALENDAR_ID", "primary")

# Timezone for calendar operations (default: Europe/Berlin for Germany)
TIMEZONE = os.environ.get("TIMEZONE", "Europe/Berlin")

# Simple cache for recent tool calls to avoid duplicate API requests
_tool_cache: dict = {}
_cache_ttl_seconds = 30  # Cache results for 30 seconds


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
        "name": "get_current_datetime",
        "description": "Get the current date and time. Use this when you need to know today's date or the current time to help schedule appointments.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
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
        "name": "find_available_slots",
        "description": "Search for available appointment slots within a specific time range on a given date. Use this when you need to find what times Aryman is free between certain hours, or when the doctor asks what times work for the patient.",
        "parameters": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "The date to search for available slots in YYYY-MM-DD format"
                },
                "start_time": {
                    "type": "string",
                    "description": "The earliest time to consider in HH:MM format, 24-hour (e.g., 09:00)"
                },
                "end_time": {
                    "type": "string",
                    "description": "The latest time to consider in HH:MM format, 24-hour (e.g., 17:00)"
                },
                "slot_duration_minutes": {
                    "type": "integer",
                    "description": "Duration of each slot in minutes. Default is 30."
                }
            },
            "required": ["date", "start_time", "end_time"]
        }
    },
    {
        "name": "end_call",
        "description": "End the phone call. IMPORTANT: You MUST speak a verbal goodbye message BEFORE calling this tool. Say something like 'Thank you, have a great day, goodbye!' or 'Vielen Dank, auf Wiederhören!' first, then call this tool. Never call this tool without saying goodbye first.",
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
# Utility Functions
# =============================================================================

def get_current_datetime() -> dict:
    """
    Get the current date and time in the configured timezone.

    Returns:
        dict with current date, time, day of week, and timezone info
    """
    tz = ZoneInfo(TIMEZONE)
    now = datetime.datetime.now(tz)
    return {
        "current_date": now.strftime("%Y-%m-%d"),
        "current_time": now.strftime("%H:%M"),
        "day_of_week": now.strftime("%A"),
        "timezone": TIMEZONE,
        "formatted": now.strftime("%A, %B %d, %Y at %I:%M %p"),
        "message": f"Today is {now.strftime('%A, %B %d, %Y')} and the current time is {now.strftime('%I:%M %p')} ({TIMEZONE})"
    }


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


def check_availability(date: str, time: str, duration_minutes: int = 30, buffer_minutes: int = 60) -> dict:
    """
    Check if Aryman is available at the proposed appointment time.
    Requires at least 1 hour gap between appointments.

    Args:
        date: Date in YYYY-MM-DD format
        time: Time in HH:MM format (24-hour)
        duration_minutes: Duration of appointment
        buffer_minutes: Required gap before and after appointment (default: 60 minutes)

    Returns:
        dict with 'available' (bool) and 'conflicts' (list) or 'error' (str)
    """
    # Check cache first to avoid duplicate API calls
    cache_key = f"check:{date}:{time}:{duration_minutes}"
    now = datetime.datetime.now()
    if cache_key in _tool_cache:
        cached_time, cached_result = _tool_cache[cache_key]
        if (now - cached_time).total_seconds() < _cache_ttl_seconds:
            logger.info(f"Returning cached result for {date} at {time}")
            return cached_result

    try:
        # Parse date and time with configured timezone
        tz = ZoneInfo(TIMEZONE)
        event_datetime = datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        event_datetime = event_datetime.replace(tzinfo=tz)

        logger.info(f"Checking availability for {event_datetime.isoformat()} (timezone: {TIMEZONE})")

        service = get_calendar_service()
        if not service:
            return {"available": True, "conflicts": [], "note": "Calendar not configured, assuming available"}

        # Define time window with buffer (1 hour before and after)
        # This ensures there's at least 1 hour gap between appointments
        check_start = event_datetime - datetime.timedelta(minutes=buffer_minutes)
        check_end = event_datetime + datetime.timedelta(minutes=duration_minutes + buffer_minutes)

        start_time = check_start.isoformat()
        end_time = check_end.isoformat()

        logger.info(f"Querying calendar {CALENDAR_ID} from {start_time} to {end_time} (with {buffer_minutes}min buffer)")

        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=start_time,
            timeMax=end_time,
            singleEvents=True,
            orderBy="startTime"
        ).execute()

        raw_events = events_result.get("items", [])

        if not raw_events:
            result = {
                "available": True,
                "conflicts": [],
                "message": f"Aryman is available on {date} at {time}"
            }
            _tool_cache[cache_key] = (datetime.datetime.now(), result)
            return result

        # There are conflicts within the buffer zone
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

        result = {
            "available": False,
            "conflicts": conflicts,
            "message": f"Aryman is not available on {date} at {time}. There needs to be at least a 1-hour gap between appointments. Please ask for another time."
        }
        _tool_cache[cache_key] = (datetime.datetime.now(), result)
        return result

    except ValueError as e:
        return {"available": False, "error": f"Invalid date/time format: {e}"}
    except HttpError as e:
        logger.error(f"Calendar API error: {e}")
        return {"available": True, "conflicts": [], "note": "Calendar check failed, assuming available"}


def find_available_slots(date: str, start_time: str, end_time: str,
                         slot_duration_minutes: int = 30, buffer_minutes: int = 60) -> dict:
    """
    Find available appointment slots within a time range on a given date.
    Considers the 1-hour buffer requirement between appointments.

    Args:
        date: Date in YYYY-MM-DD format
        start_time: Start of search range in HH:MM format (24-hour)
        end_time: End of search range in HH:MM format (24-hour)
        slot_duration_minutes: Duration of each slot in minutes (default: 30)
        buffer_minutes: Required gap before and after appointments (default: 60)

    Returns:
        dict with 'available_slots' (list) or 'error' (str)
    """
    # Check cache first
    cache_key = f"slots:{date}:{start_time}:{end_time}:{slot_duration_minutes}"
    now = datetime.datetime.now()
    if cache_key in _tool_cache:
        cached_time, cached_result = _tool_cache[cache_key]
        if (now - cached_time).total_seconds() < _cache_ttl_seconds:
            logger.info(f"Returning cached slots for {date} {start_time}-{end_time}")
            return cached_result

    try:
        tz = ZoneInfo(TIMEZONE)

        # Parse the date and time range
        range_start = datetime.datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
        range_start = range_start.replace(tzinfo=tz)
        range_end = datetime.datetime.strptime(f"{date} {end_time}", "%Y-%m-%d %H:%M")
        range_end = range_end.replace(tzinfo=tz)

        if range_end <= range_start:
            return {"available_slots": [], "error": "End time must be after start time"}

        logger.info(f"Finding available slots on {date} from {start_time} to {end_time}")

        service = get_calendar_service()
        if not service:
            # If calendar not configured, assume all slots are available
            slots = []
            current = range_start
            while current + datetime.timedelta(minutes=slot_duration_minutes) <= range_end:
                slots.append({
                    "time": current.strftime("%H:%M"),
                    "formatted": current.strftime("%I:%M %p")
                })
                current += datetime.timedelta(minutes=slot_duration_minutes)
            return {
                "available_slots": slots,
                "note": "Calendar not configured, showing all slots as available",
                "message": f"Found {len(slots)} available slots on {date} between {start_time} and {end_time}"
            }

        # Query calendar for events in the range (with buffer on both ends)
        query_start = range_start - datetime.timedelta(minutes=buffer_minutes)
        query_end = range_end + datetime.timedelta(minutes=buffer_minutes)

        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=query_start.isoformat(),
            timeMax=query_end.isoformat(),
            singleEvents=True,
            orderBy="startTime"
        ).execute()

        events = events_result.get("items", [])

        # Parse events into busy periods (with buffer)
        busy_periods = []
        for event in events:
            if "dateTime" in event["start"]:
                ev_start = datetime.datetime.fromisoformat(event["start"]["dateTime"])
                ev_end = datetime.datetime.fromisoformat(event["end"]["dateTime"])
            else:
                # All-day event - skip for now (or treat as blocking whole day)
                continue

            # Add buffer around the event
            busy_start = ev_start - datetime.timedelta(minutes=buffer_minutes)
            busy_end = ev_end + datetime.timedelta(minutes=buffer_minutes)
            busy_periods.append((busy_start, busy_end))

        # Sort busy periods by start time
        busy_periods.sort(key=lambda x: x[0])

        # Find available slots
        available_slots = []
        current = range_start

        while current + datetime.timedelta(minutes=slot_duration_minutes) <= range_end:
            slot_end = current + datetime.timedelta(minutes=slot_duration_minutes)

            # Check if this slot conflicts with any busy period
            is_available = True
            for busy_start, busy_end in busy_periods:
                # Slot conflicts if it overlaps with busy period
                if current < busy_end and slot_end > busy_start:
                    is_available = False
                    # Jump to end of this busy period
                    current = busy_end
                    break

            if is_available:
                available_slots.append({
                    "time": current.strftime("%H:%M"),
                    "formatted": current.strftime("%I:%M %p")
                })
                current += datetime.timedelta(minutes=slot_duration_minutes)

        if available_slots:
            result = {
                "available_slots": available_slots,
                "count": len(available_slots),
                "message": f"Found {len(available_slots)} available slot(s) on {date} between {start_time} and {end_time}: " +
                          ", ".join([s["formatted"] for s in available_slots[:5]]) +
                          ("..." if len(available_slots) > 5 else "")
            }
        else:
            result = {
                "available_slots": [],
                "count": 0,
                "message": f"No available slots found on {date} between {start_time} and {end_time}. Please try a different date or time range."
            }

        _tool_cache[cache_key] = (datetime.datetime.now(), result)
        return result

    except ValueError as e:
        return {"available_slots": [], "error": f"Invalid date/time format: {e}"}
    except HttpError as e:
        logger.error(f"Calendar API error: {e}")
        return {"available_slots": [], "error": f"Calendar API error: {e}"}


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
        # Parse date and time with configured timezone
        tz = ZoneInfo(TIMEZONE)
        event_datetime = datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        event_datetime = event_datetime.replace(tzinfo=tz)
        end_datetime = event_datetime + datetime.timedelta(minutes=duration_minutes)

        service = get_calendar_service()
        if not service:
            return {"success": False, "error": "Calendar not configured"}

        event = {
            "summary": f"Doctor Appointment - {doctor_name}",
            "description": f"Appointment booked by AI assistant.\n{notes}",
            "start": {
                "dateTime": event_datetime.isoformat(),
                "timeZone": TIMEZONE
            },
            "end": {
                "dateTime": end_datetime.isoformat(),
                "timeZone": TIMEZONE
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

        # Format time for display (convert 24h to 12h)
        display_time = event_datetime.strftime("%I:%M %p")
        display_date = event_datetime.strftime("%B %d, %Y")

        return {
            "success": True,
            "event_id": created_event.get("id"),
            "date": display_date,
            "time": display_time,
            "message": f"Appointment booked with {doctor_name} on {display_date} at {display_time}"
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
    import json

    # Get current timestamp for logging
    tz = ZoneInfo(TIMEZONE)
    current_time = datetime.datetime.now(tz)
    timestamp = current_time.strftime("%Y-%m-%d %H:%M:%S %Z")

    # Log tool call with timestamp and parameters
    logger.info("=" * 60)
    logger.info(f"TOOL CALL: {tool_name}")
    logger.info(f"TIMESTAMP: {timestamp}")
    logger.info(f"PARAMETERS: {json.dumps(args, indent=2, default=str)}")
    logger.info("-" * 60)

    result = None

    if tool_name == "get_current_datetime":
        result = get_current_datetime()

    elif tool_name == "check_availability":
        result = check_availability(
            date=args.get("date"),
            time=args.get("time"),
            duration_minutes=args.get("duration_minutes", 30)
        )

    elif tool_name == "book_appointment":
        result = book_appointment(
            date=args.get("date"),
            time=args.get("time"),
            doctor_name=args.get("doctor_name"),
            duration_minutes=args.get("duration_minutes", 30),
            notes=args.get("notes", "")
        )

    elif tool_name == "find_available_slots":
        result = find_available_slots(
            date=args.get("date"),
            start_time=args.get("start_time"),
            end_time=args.get("end_time"),
            slot_duration_minutes=args.get("slot_duration_minutes", 30)
        )

    elif tool_name == "end_call":
        result = end_call(reason=args.get("reason", "conversation_complete"))

    else:
        logger.warning(f"Unknown tool: {tool_name}")
        result = {"error": f"Unknown tool: {tool_name}"}

    # Log the result
    logger.info(f"RESULT: {json.dumps(result, indent=2, default=str)}")
    logger.info("=" * 60)

    return result
