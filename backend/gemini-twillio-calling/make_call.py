"""
Script to initiate outgoing calls via Twilio.

Usage:
    python make_call.py +1234567890
"""

import sys
from twilio.rest import Client
from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER, NGROK_URL


def make_call(to_number: str) -> str:
    """
    Initiate an outgoing call.

    Args:
        to_number: Phone number to call (E.164 format, e.g., +1234567890)

    Returns:
        Call SID
    """
    if not NGROK_URL:
        print("Error: NGROK_URL not set in .env file!")
        print("Start ngrok and update .env with the URL")
        sys.exit(1)

    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    # URL that Twilio will request for TwiML
    webhook_url = f"{NGROK_URL}/outgoing-call"

    print(f"Initiating call...")
    print(f"  To: {to_number}")
    print(f"  From: {TWILIO_PHONE_NUMBER}")
    print(f"  Webhook: {webhook_url}")

    call = client.calls.create(
        url=webhook_url,
        to=to_number,
        from_=TWILIO_PHONE_NUMBER,
    )

    print(f"\nCall initiated successfully!")
    print(f"  Call SID: {call.sid}")
    print(f"  Status: {call.status}")

    return call.sid


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python make_call.py +1234567890")
        print("\nPhone number must be in E.164 format (e.g., +1234567890)")
        sys.exit(1)

    to_number = sys.argv[1]

    # Validate E.164 format
    if not to_number.startswith("+"):
        print("Error: Phone number must be in E.164 format (e.g., +1234567890)")
        sys.exit(1)

    make_call(to_number)
