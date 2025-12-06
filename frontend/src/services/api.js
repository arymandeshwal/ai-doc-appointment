/**
 * API service for communicating with the Gemini-Twilio backend.
 */

const API_URL = 'http://localhost:8080';

/**
 * Initiate a call to a doctor's office.
 * @param {object} params - Call parameters
 * @param {string} params.doctorName - The name of the doctor to call
 * @param {string} params.patientName - The patient's full name
 * @param {string} params.dateOfBirth - The patient's date of birth (YYYY-MM-DD)
 * @param {string} params.symptoms - The patient's symptoms
 * @param {string} params.insuranceType - The patient's insurance type (public/private/none)
 * @returns {Promise<{call_sid: string, status: string, message: string}>}
 */
export const initiateCall = async ({ doctorName, patientName, dateOfBirth, symptoms, insuranceType }) => {
  const response = await fetch(`${API_URL}/api/initiate-call`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      doctor_name: doctorName,
      doctor_phone: '+4915510744774',  // Test number - all calls go here
      patient_name: patientName,
      date_of_birth: dateOfBirth,
      symptoms: symptoms,
      insurance_type: insuranceType
    })
  });

  if (!response.ok) {
    throw new Error(`Failed to initiate call: ${response.statusText}`);
  }

  return response.json();
};

/**
 * Subscribe to real-time call events via Server-Sent Events.
 * @param {string} callSid - The call SID to subscribe to
 * @param {function} onEvent - Callback for each event received
 * @returns {EventSource} - The EventSource instance (call .close() to unsubscribe)
 */
export const subscribeToCallEvents = (callSid, onEvent) => {
  const eventSource = new EventSource(`${API_URL}/api/call-events/${callSid}`);

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onEvent(data);
    } catch (e) {
      console.error('Failed to parse SSE event:', e);
    }
  };

  eventSource.onerror = (error) => {
    console.error('SSE connection error:', error);
    onEvent({ type: 'error', message: 'Connection lost' });
  };

  return eventSource;
};

/**
 * Get the current status of a call.
 * @param {string} callSid - The call SID to check
 * @returns {Promise<{call_sid: string, status: string, events: array, result: object}>}
 */
export const getCallStatus = async (callSid) => {
  const response = await fetch(`${API_URL}/api/call-status/${callSid}`);

  if (!response.ok) {
    throw new Error(`Failed to get call status: ${response.statusText}`);
  }

  return response.json();
};
