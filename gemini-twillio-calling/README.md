# Gemini-Twilio Voice Integration

Real-time voice calling system that connects phone calls to Google's Gemini AI assistant.

## How It Works

1. You run `make_call.py` to call a phone number
2. When the call connects, Twilio streams audio to your server
3. Your server converts audio and sends it to Gemini Live API
4. Gemini responds with AI-generated speech
5. Response audio streams back through Twilio to the caller

## Prerequisites

- Python 3.11+
- Twilio account with a phone number
- Google API key with Gemini access
- ngrok (for local development)

## Setup

### 1. Create and activate virtual environment

```bash
cd gemini-twillio-calling
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required values:
- `TWILIO_ACCOUNT_SID` - From Twilio Console
- `TWILIO_AUTH_TOKEN` - From Twilio Console
- `TWILIO_PHONE_NUMBER` - Your Twilio phone number
- `GOOGLE_API_KEY` - From Google AI Studio
- `NGROK_URL` - Your ngrok HTTPS URL (set after starting ngrok)

### 4. Start ngrok

```bash
ngrok http 8080
```

Copy the HTTPS URL (e.g., `https://abc123.ngrok.app`) and add it to `.env`:

```
NGROK_URL=https://abc123.ngrok.app
```

### 5. Start the server

```bash
python main.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8080
```

### 6. Make a test call

In a new terminal (with venv activated):

```bash
python make_call.py +1234567890
```

Replace `+1234567890` with the phone number you want to call.

## Project Structure

```
gemini-twillio-calling/
├── main.py              # FastAPI server with WebSocket handler
├── gemini_client.py     # Gemini Live API WebSocket client
├── audio_utils.py       # Audio format conversion (mu-law <-> PCM)
├── config.py            # Configuration and environment variables
├── make_call.py         # Script to initiate outgoing calls
├── requirements.txt     # Python dependencies
├── .env                 # Your credentials (don't commit!)
└── .env.example         # Credential template
```

## Audio Format Conversion

| Direction | From | To |
|-----------|------|-----|
| Twilio → Gemini | mu-law 8kHz | PCM 16kHz |
| Gemini → Twilio | PCM 24kHz | mu-law 8kHz |

## Troubleshooting

### "NGROK_URL not set"
Make sure you've started ngrok and added the URL to your `.env` file.

### Call connects but no AI response
- Check the server logs for errors
- Verify your Google API key is valid
- Make sure ngrok is running and the URL is correct

### Audio quality issues
The audio conversion uses Python's `audioop` module. For better quality, consider using `soxr` for resampling.

## API Endpoints

- `POST /outgoing-call` - TwiML webhook (called by Twilio)
- `WebSocket /media-stream` - Bidirectional audio stream
- `GET /health` - Health check
- `GET /` - Service info
