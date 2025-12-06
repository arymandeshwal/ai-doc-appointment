import React from 'react';
import { useApp } from '../context/AppContext';

const CallFailed = () => {
  const { failureReason, retryCall, startOver, selectedDoctor } = useApp();

  return (
    <div className="card failure-card">
      <div className="failure-icon">
        <svg width="80" height="80" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="12" cy="12" r="10" stroke="#EF4444" strokeWidth="2" fill="none"/>
          <path d="M15 9L9 15M9 9L15 15" stroke="#EF4444" strokeWidth="2" strokeLinecap="round"/>
        </svg>
      </div>

      <h2>Booking Unsuccessful</h2>

      <p className="failure-reason">{failureReason}</p>

      {selectedDoctor && (
        <p className="failure-doctor">
          Last attempted: <strong>{selectedDoctor.name}</strong>
        </p>
      )}

      <div className="failure-info">
        <p>This can happen when:</p>
        <ul>
          <li>The doctor's office is busy or unavailable</li>
          <li>No appointment slots match your calendar</li>
          <li>Connection issues during the call</li>
        </ul>
      </div>

      <div className="failure-actions">
        <button onClick={retryCall} className="btn btn-primary">
          Retry Call
        </button>
        <button onClick={startOver} className="btn btn-outline">
          Start Over
        </button>
      </div>
    </div>
  );
};

export default CallFailed;
