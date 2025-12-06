import datetime
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Google Calendar API scope
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

def get_calendar_service():
    """Authenticate and return a Google Calendar service object."""
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    service = build("calendar", "v3", credentials=creds)
    return service

def check_for_conflicts(event_datetime: datetime.datetime, duration_minutes: int = 30):
    """
    Returns a list of events happening around the proposed appointment time.

    Each event in the list contains:
        - summary: title of the event
        - start: start datetime (or date for all-day)
        - end: end datetime (or date for all-day)
        - type: "online" or "offline" (determined from event metadata or default)
    
    Parameters:
        event_datetime: datetime.datetime object of proposed appointment
        duration_minutes: length of appointment in minutes
    
    Returns:
        List[dict] of relevant events
    """
    service = get_calendar_service()
    
    # Define the window: start_time and end_time for overlap check
    start_time = event_datetime.isoformat()
    end_time = (event_datetime + datetime.timedelta(minutes=duration_minutes)).isoformat()

    try:
        events_result = service.events().list(
            calendarId="primary",
            timeMin=start_time,
            timeMax=end_time,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        
        raw_events = events_result.get("items", [])
        relevant_events = []

        for event in raw_events:
            # Handle all-day events
            if "dateTime" in event["start"]:
                ev_start = event["start"]["dateTime"]
                ev_end = event["end"]["dateTime"]
            else:
                # all-day events only have 'date'
                ev_start = event["start"]["date"]
                ev_end = event["end"]["date"]

            # Determine type (example: if location or description contains "online")
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
    """
    Add an event to Google Calendar.

    Parameters:
        event_subject (str): Title of the event
        event_datetime (datetime.datetime): Start time of the event (UTC)
        duration_minutes (int): Event duration in minutes (default 30)
    """
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
        created_event = service.events().insert(calendarId="primary", body=event).execute()
        print(f"Event created: {created_event.get('htmlLink')}")
        return created_event
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None

# Example usage
if __name__ == "__main__":
    appointment_datetime = datetime.datetime(2025, 12, 12, 15, 0, tzinfo=datetime.timezone.utc)
    conflicts = check_for_conflicts(appointment_datetime, duration_minutes=30)
    if not conflicts:
        print("No conflicts found. Adding event to calendar.")
        add_event_to_calendar("Test Event", appointment_datetime, duration_minutes=30)


    for ev in conflicts:
        print(ev)
