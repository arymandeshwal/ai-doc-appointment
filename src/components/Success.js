import React from 'react';
import { useApp } from '../context/AppContext';
import { downloadICS } from '../utils/helpers';

const Success = () => {
  const {
    selectedDoctor,
    selectedSlot,
    patientInfo,
    symptoms,
    startOver,
    comparisonData
  } = useApp();

  if (!selectedDoctor || !selectedSlot) return null;

  const price = selectedDoctor.insurance 
    ? (selectedDoctor.price * 0.2).toFixed(0) 
    : selectedDoctor.price;

  const handleDownload = () => {
    downloadICS(selectedDoctor, selectedSlot, symptoms);
  };

  const bestMatch = comparisonData.find(item => item.doctor.id === selectedDoctor.id);

  return (
    <div className="card success-card">
      <div className="success-icon">
        <svg width="80" height="80" viewBox="0 0 80 80" fill="none">
          <circle cx="40" cy="40" r="40" fill="#10B981" opacity="0.1"/>
          <circle cx="40" cy="40" r="30" fill="#10B981"/>
          <path d="M25 40L35 50L55 30" stroke="white" strokeWidth="4" strokeLinecap="round"/>
        </svg>
      </div>
      
      <h2>🎉 Appointment Confirmed!</h2>
      <p className="success-subtitle">
        {patientInfo.autoBook 
          ? 'AI has automatically booked your appointment' 
          : 'Your appointment has been successfully confirmed'}
      </p>

      <div className="success-details">
        <div className="success-doctor-card">
          <div className="doctor-header-success">
            <div className="doctor-avatar-large">👨‍⚕️</div>
            <div className="doctor-info-success">
              <h3>{selectedDoctor.name}</h3>
              <p>{selectedDoctor.specialty}</p>
              {bestMatch && (
                <div className="score-badge-success">
                  AI Score: {bestMatch.score}/100
                </div>
              )}
            </div>
          </div>

          <div className="appointment-summary-success">
            <div className="summary-row">
              <span className="summary-icon">📅</span>
              <div>
                <div className="summary-label">Date & Time</div>
                <div className="summary-value">{selectedSlot.date} at {selectedSlot.time}</div>
              </div>
            </div>
            <div className="summary-row">
              <span className="summary-icon">📍</span>
              <div>
                <div className="summary-label">Location</div>
                <div className="summary-value">{selectedDoctor.address}</div>
              </div>
            </div>
            <div className="summary-row">
              <span className="summary-icon">📞</span>
              <div>
                <div className="summary-label">Contact</div>
                <div className="summary-value">{selectedDoctor.phone}</div>
              </div>
            </div>
            <div className="summary-row">
              <span className="summary-icon">💰</span>
              <div>
                <div className="summary-label">Cost</div>
                <div className="summary-value">
                  ${price}{selectedDoctor.insurance ? ' (copay)' : ''}
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="success-notifications">
          <div className="notification-item">
            <span className="notification-icon">✓</span>
            <span>Confirmation email sent</span>
          </div>
          <div className="notification-item">
            <span className="notification-icon">✓</span>
            <span>Calendar event created</span>
          </div>
          <div className="notification-item">
            <span className="notification-icon">✓</span>
            <span>Reminder notifications set</span>
          </div>
        </div>
      </div>

      <div className="success-actions">
        <button className="btn btn-primary btn-large" onClick={handleDownload}>
          📥 Download Calendar File (.ics)
        </button>
        <button className="btn btn-outline" onClick={startOver}>
          ← Book Another Appointment
        </button>
      </div>
    </div>
  );
};

export default Success;
