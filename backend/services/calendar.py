import datetime
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account

# Google Calendar API scope
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
calendar_id = "41a68850cc35f8233d323d7b59cc1b05336db4387c7ce48ae765db3c6df9ccb3@group.calendar.google.com"
SERVICE_ACCOUNT_FILE = "credentials.json"


def get_calendar_service():
    """Authenticate and return a Google Calendar service object."""
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service = build("calendar", "v3", credentials=credentials)
    return service
    
def check_for_conflicts(event_datetime: datetime.datetime, duration_minutes: int = 30):
    """Return a list of events around the proposed appointment time."""
    service = get_calendar_service()
    start_time = event_datetime.isoformat()
    end_time = (event_datetime + datetime.timedelta(minutes=duration_minutes)).isoformat()

    try:
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=start_time,
            timeMax=end_time,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        
        raw_events = events_result.get("items", [])
        relevant_events = []

        for event in raw_events:
            if "dateTime" in event["start"]:
                ev_start = event["start"]["dateTime"]
                ev_end = event["end"]["dateTime"]
            else:
                ev_start = event["start"]["date"]
                ev_end = event["end"]["date"]

            ev_type = "offline"
            if "online" in (event.get("location") or "").lower() or \
               "online" in (event.get("description") or "").lower():
                ev_type = "online"

            relevant_events.append({
                "summary": event.get("summary", "No title"),
                "start": ev_start,
                "end": ev_end,
                "type": ev_type
            })

        return relevant_events

    except HttpError as error:
        print(f"An error occurred while checking conflicts: {error}")
        return []

def add_event_to_calendar(event_subject: str, event_datetime: datetime.datetime, duration_minutes: int = 30):
    """Add an event to Google Calendar."""
    service = get_calendar_service()
    event = {
        "summary": event_subject,
        "start": {"dateTime": event_datetime.isoformat(), "timeZone": "UTC"},
        "end": {
            "dateTime": (event_datetime + datetime.timedelta(minutes=duration_minutes)).isoformat(),
            "timeZone": "UTC"
        }
    }

    try:
        created_event = service.events().insert(calendarId=calendar_id, body=event).execute()
        print(f"Event created: {created_event.get('htmlLink')}")
        return created_event
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None

# ------------------ MAIN ------------------
if __name__ == "__main__":
    # 1️⃣ Pre-populate calendar with a few appointments
    initial_appointments = [
        ("Team Meeting", datetime.datetime(2025, 12, 10, 10, 0, tzinfo=datetime.timezone.utc)),
        ("Lunch with Friend", datetime.datetime(2025, 12, 10, 13, 0, tzinfo=datetime.timezone.utc)),
        ("Project Demo", datetime.datetime(2025, 12, 11, 16, 0, tzinfo=datetime.timezone.utc)),
        ("Yoga Class", datetime.datetime(2025, 12, 12, 8, 0, tzinfo=datetime.timezone.utc))
    ]

    for subject, dt in initial_appointments:
        add_event_to_calendar(subject, dt)

    # 2️⃣ Use Case 1: Add a doctor appointment where no conflicts exist
    appointment1 = datetime.datetime(2025, 12, 12, 15, 0, tzinfo=datetime.timezone.utc)
    conflicts1 = check_for_conflicts(appointment1)
    if not conflicts1:
        print("\nNo conflicts found for Use Case 1. Adding Doctor Appointment.")
        add_event_to_calendar("Doctor Consultation", appointment1)
    else:
        print("\nConflicts found for Use Case 1:")
        for ev in conflicts1:
            print(ev)

    # 3️⃣ Use Case 2: Add a doctor appointment where a conflict exists
    appointment2 = datetime.datetime(2025, 12, 10, 10, 15, tzinfo=datetime.timezone.utc)  # overlaps with Team Meeting
    conflicts2 = check_for_conflicts(appointment2)
    if not conflicts2:
        print("\nNo conflicts found for Use Case 2. Adding Doctor Appointment.")
        add_event_to_calendar("Doctor Consultation", appointment2)
    else:
        print("\nConflicts found for Use Case 2:")
        for ev in conflicts2:
            print(ev)
