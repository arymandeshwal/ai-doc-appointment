"""
Load configuration from root .env file.
This allows all services to use a single unified .env file.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load from root .env file (one level up from app-backend)
root_dir = Path(__file__).parent.parent
env_path = root_dir / '.env'

if env_path.exists():
    load_dotenv(env_path)
    print(f"✓ Loaded config from: {env_path}")
else:
    print(f"⚠ Warning: {env_path} not found")
    # Try local .env as fallback
    load_dotenv()

# Twilio Configuration
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
NGROK_URL = os.getenv('NGROK_URL')

# Server Configuration
SERVER_HOST = os.getenv('SERVER_HOST', '0.0.0.0')
SERVER_PORT = int(os.getenv('SERVER_PORT', 5000))
