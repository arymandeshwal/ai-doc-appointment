"""
Backend API for AI Doctor Appointment System.

Provides endpoints for:
- Initiating calls to doctors via Twilio + Gemini
- Checking call status
- Managing appointments
"""

import os
import sys
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
from twilio.rest import Client
from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER, NGROK_URL

# Add gemini-twillio-calling to path to import make_call
sys.path.insert(0, str(Path(__file__).parent.parent / 'gemini-twillio-calling'))

try:
    from make_call import make_call
    USE_MAKE_CALL_MODULE = True
except ImportError:
    print("Warning: Could not import make_call module, using direct Twilio calls")
    USE_MAKE_CALL_MODULE = False

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Twilio client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Store call status (in production, use a database)
call_status = {}


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'twilio_configured': bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN),
        'ngrok_configured': bool(NGROK_URL)
    })


@app.route('/api/call-doctor', methods=['POST'])
def call_doctor():
    """
    Initiate a call to a doctor's phone number.
    
    Request body:
    {
        "doctor_name": "Dr. Smith",
        "phone_number": "+1234567890",
        "patient_name": "John Doe",
        "patient_dob": "1990-01-15",
        "symptoms": "headache, fever"
    }
    
    The AI assistant will:
    1. Call the doctor/receptionist
    2. Request an appointment
    3. Use tools.py to check patient's Google Calendar
    4. Book the appointment if time is available
    """
    try:
        data = request.json
        doctor_name = data.get('doctor_name')
        phone_number = data.get('phone_number')
        patient_name = data.get('patient_name')
        patient_dob = data.get('patient_dob')
        symptoms = data.get('symptoms')
        
        if not phone_number:
            return jsonify({'error': 'Phone number is required'}), 400
        
        if not NGROK_URL:
            return jsonify({'error': 'NGROK_URL not configured. Start ngrok and update .env'}), 500
        
        # Use make_call module if available, otherwise use direct Twilio call
        if USE_MAKE_CALL_MODULE:
            print(f"Using make_call module to call {phone_number}")
            print(f"Patient: {patient_name} (DOB: {patient_dob})")
            print(f"AI will check patient's calendar and book appointment during call")
            call_sid = make_call(phone_number)
            call = twilio_client.calls(call_sid).fetch()
        else:
            # Fallback: Direct Twilio call
            webhook_url = f"{NGROK_URL}/outgoing-call"
            call = twilio_client.calls.create(
                url=webhook_url,
                to=phone_number,
                from_=TWILIO_PHONE_NUMBER,
                status_callback=f"{NGROK_URL}/api/call-status",
                status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
                status_callback_method='POST'
            )
        
        # Store call info
        call_status[call.sid] = {
            'doctor_name': doctor_name,
            'phone_number': phone_number,
            'patient_name': patient_name,
            'patient_dob': patient_dob,
            'symptoms': symptoms,
            'status': 'initiated',
            'call_sid': call.sid
        }
        
        return jsonify({
            'success': True,
            'call_sid': call.sid,
            'status': 'initiated',
            'message': f'Calling {doctor_name} at {phone_number}...'
        })
        
    except Exception as e:
        print(f"Error making call: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/call-status/<call_sid>', methods=['GET'])
def get_call_status(call_sid):
    """Get the current status of a call."""
    try:
        # Fetch real-time status from Twilio
        call = twilio_client.calls(call_sid).fetch()
        
        # Update our local status
        if call_sid in call_status:
            call_status[call_sid]['status'] = call.status
            call_status[call_sid]['duration'] = call.duration
        
        return jsonify({
            'call_sid': call_sid,
            'status': call.status,
            'duration': call.duration,
            'direction': call.direction,
            'answered_by': call.answered_by
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 404


@app.route('/api/call-status', methods=['POST'])
def call_status_webhook():
    """Webhook to receive call status updates from Twilio."""
    call_sid = request.form.get('CallSid')
    status = request.form.get('CallStatus')
    
    if call_sid in call_status:
        call_status[call_sid]['status'] = status
        print(f"Call {call_sid} status updated to: {status}")
    
    return '', 200


@app.route('/api/end-call/<call_sid>', methods=['POST'])
def end_call(call_sid):
    """End an active call."""
    try:
        call = twilio_client.calls(call_sid).update(status='completed')
        
        return jsonify({
            'success': True,
            'call_sid': call_sid,
            'status': call.status
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        print("Error: Twilio credentials not set in .env file!")
        sys.exit(1)
    
    print(f"Starting backend server...")
    print(f"Twilio configured: ✓")
    print(f"NGROK URL: {NGROK_URL or 'Not set (required for calls)'}")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
