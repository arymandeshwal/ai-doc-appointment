import React from 'react';
import { useApp } from '../context/AppContext';

const Confirmation = () => {
  const {
    selectedDoctor,
    selectedSlot,
    confirmAppointment,
    comparisonData
  } = useApp();

  if (!selectedDoctor || !selectedSlot) return null;

  const bestMatch = comparisonData.find(item => item.doctor.id === selectedDoctor.id);

  return (
    <div className="card">
      <h2>✅ AI Has Selected the Best Doctor</h2>
      <p className="subtitle">Review the appointment details below</p>

      {/* AI Decision Summary */}
      <div className="ai-decision-box">
        <div className="decision-header">
          <span className="robot-icon">🤖</span>
          <div>
            <h3>AI Recommendation</h3>
            <p>After comparing all available doctors, here's the best match:</p>
          </div>
        </div>
      </div>

      {/* Selected Doctor Details */}
      <div className="selected-doctor-card">
        <div className="doctor-main-info">
          <div className="doctor-avatar">
            <span className="avatar-icon">👨‍⚕️</span>
          </div>
          <div>
            <h3>{selectedDoctor.name}</h3>
            <div className="doctor-specialty">{selectedDoctor.specialty}</div>
            <div className="doctor-education">🎓 {selectedDoctor.education}</div>
          </div>
          {bestMatch && (
            <div className="score-badge-large">
              <span className="score-value">{bestMatch.score}</span>
              <span className="score-label">AI Score</span>
            </div>
          )}
        </div>

        {/* Why This Doctor */}
        {bestMatch && (
          <div className="why-section">
            <h4>Why This Doctor?</h4>
            <div className="reasons-list">
              {bestMatch.reasons.map((reason, idx) => (
                <div key={idx} className="reason-chip">
                  ✓ {reason}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Appointment Details */}
        <div className="appointment-info">
          <div className="info-row">
            <span className="info-label">📅 Date & Time:</span>
            <span className="info-value">{selectedSlot.date} at {selectedSlot.time}</span>
          </div>
          <div className="info-row">
            <span className="info-label">📍 Location:</span>
            <span className="info-value">{selectedDoctor.address}</span>
          </div>
          <div className="info-row">
            <span className="info-label">📞 Phone:</span>
            <span className="info-value">{selectedDoctor.phone}</span>
          </div>
          <div className="info-row">
            <span className="info-label">💰 Cost:</span>
            <span className="info-value">
              ${selectedDoctor.insurance ? (selectedDoctor.price * 0.2).toFixed(0) + ' (copay)' : selectedDoctor.price}
            </span>
          </div>
        </div>
      </div>

      <div className="confirmation-actions">
        <button className="btn btn-primary btn-large" onClick={confirmAppointment}>
          ✓ Confirm Appointment
        </button>
        <p className="confirmation-note">
          A confirmation will be sent to your email and added to your calendar
        </p>
      </div>
    </div>
  );
};

export default Confirmation;
