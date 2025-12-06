"""Test script to debug Google Calendar integration."""

import os
import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv()

from tools import get_calendar_service, check_availability, book_appointment, CALENDAR_ID, TIMEZONE

def test_calendar():
    print("=" * 50)
    print("CALENDAR DEBUG TEST")
    print("=" * 50)

    # Check environment variables
    print("\n1. Checking environment variables...")
    print(f"   CALENDAR_ID: {CALENDAR_ID}")
    print(f"   TIMEZONE: {TIMEZONE}")
    print(f"   SERVICE_ACCOUNT_EMAIL: {os.environ.get('GOOGLE_SERVICE_ACCOUNT_CLIENT_EMAIL', 'NOT SET')}")

    # Test service connection
    print("\n2. Testing calendar service connection...")
    service = get_calendar_service()
    if service:
        print("   ✓ Calendar service connected successfully!")
    else:
        print("   ✗ Failed to connect to calendar service")
        return

    # List upcoming events
    print("\n3. Listing upcoming events in calendar...")
    try:
        tz = ZoneInfo(TIMEZONE)
        now = datetime.datetime.now(tz).isoformat()
        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=now,
            maxResults=10,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])

        if not events:
            print("   No upcoming events found.")
        else:
            print(f"   Found {len(events)} upcoming event(s):")
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                print(f"   - {event.get('summary', 'No title')} at {start}")
    except Exception as e:
        print(f"   ✗ Error listing events: {e}")

    # Test check_availability
    print("\n4. Testing check_availability (with 1-hour buffer)...")
    # Test with tomorrow's date
    tz = ZoneInfo(TIMEZONE)
    tomorrow = (datetime.datetime.now(tz) + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    test_time = "10:00"

    print(f"   Checking availability for {tomorrow} at {test_time}...")
    result = check_availability(tomorrow, test_time)
    print(f"   Result: {result}")

    # Test with a specific date if you have events
    print("\n5. Enter a date/time to test (or press Enter to skip):")
    test_date = input("   Date (YYYY-MM-DD): ").strip()
    if test_date:
        test_time_input = input("   Time (HH:MM): ").strip()
        if test_time_input:
            result = check_availability(test_date, test_time_input)
            print(f"   Result: {result}")

if __name__ == "__main__":
    test_calendar()
