/**
 * Service for making real phone calls via backend API
 */

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:5000';

/**
 * Make a call to a doctor's phone number
 * @param {Object} callData - Call information
 * @param {string} callData.doctor_name - Doctor's name
 * @param {string} callData.phone_number - Doctor's phone number
 * @param {string} callData.patient_name - Patient's name
 * @param {string} callData.symptoms - Patient's symptoms
 * @returns {Promise<Object>} Call result with call_sid and status
 */
export const makeCallToDoctor = async (callData) => {
  try {
    const response = await fetch(`${BACKEND_URL}/api/call-doctor`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(callData),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to initiate call');
    }

    return await response.json();
  } catch (error) {
    console.error('Error calling doctor:', error);
    throw error;
  }
};

/**
 * Get the current status of a call
 * @param {string} callSid - Twilio call SID
 * @returns {Promise<Object>} Call status information
 */
export const getCallStatus = async (callSid) => {
  try {
    const response = await fetch(`${BACKEND_URL}/api/call-status/${callSid}`);
    
    if (!response.ok) {
      throw new Error('Failed to get call status');
    }

    return await response.json();
  } catch (error) {
    console.error('Error getting call status:', error);
    throw error;
  }
};

/**
 * Poll call status until it reaches a terminal state
 * @param {string} callSid - Twilio call SID
 * @param {Function} onStatusUpdate - Callback for status updates
 * @param {number} maxAttempts - Maximum polling attempts
 * @returns {Promise<Object>} Final call status
 */
export const pollCallStatus = async (callSid, onStatusUpdate, maxAttempts = 60) => {
  const pollInterval = 2000; // 2 seconds
  let attempts = 0;

  return new Promise((resolve, reject) => {
    const interval = setInterval(async () => {
      attempts++;

      try {
        const status = await getCallStatus(callSid);
        
        if (onStatusUpdate) {
          onStatusUpdate(status);
        }

        // Terminal states
        if (['completed', 'busy', 'no-answer', 'failed', 'canceled'].includes(status.status)) {
          clearInterval(interval);
          resolve(status);
        }

        if (attempts >= maxAttempts) {
          clearInterval(interval);
          reject(new Error('Call status polling timeout'));
        }
      } catch (error) {
        clearInterval(interval);
        reject(error);
      }
    }, pollInterval);
  });
};

/**
 * End an active call
 * @param {string} callSid - Twilio call SID
 * @returns {Promise<Object>} End call result
 */
export const endCall = async (callSid) => {
  try {
    const response = await fetch(`${BACKEND_URL}/api/end-call/${callSid}`, {
      method: 'POST',
    });

    if (!response.ok) {
      throw new Error('Failed to end call');
    }

    return await response.json();
  } catch (error) {
    console.error('Error ending call:', error);
    throw error;
  }
};

/**
 * Check if backend is available and configured
 * @returns {Promise<Object>} Health check result
 */
export const checkBackendHealth = async () => {
  try {
    const response = await fetch(`${BACKEND_URL}/api/health`);
    
    if (!response.ok) {
      throw new Error('Backend health check failed');
    }

    return await response.json();
  } catch (error) {
    console.error('Backend health check error:', error);
    return {
      status: 'error',
      twilio_configured: false,
      ngrok_configured: false,
      error: error.message
    };
  }
};
