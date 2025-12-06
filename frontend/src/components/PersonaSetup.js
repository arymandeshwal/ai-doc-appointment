import React from 'react';
import { useApp } from '../context/AppContext';

const PersonaSetup = () => {
  const { patientPersona, setPatientPersona, setCurrentStep } = useApp();

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!patientPersona.name || !patientPersona.dateOfBirth || !patientPersona.insuranceType) {
      alert('Please fill in all required fields.');
      return;
    }
    setCurrentStep('symptom'); // Move to symptom input after persona is set
  };

  return (
    <div className="card">
      <h2>Welcome! Let's set up your profile</h2>
      <p className="subtitle">This information will be saved and reused for all your doctor searches</p>
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="patient-name">Your Full Name *</label>
          <input
            type="text"
            id="patient-name"
            placeholder="Enter your full name"
            value={patientPersona.name}
            onChange={(e) => setPatientPersona({ ...patientPersona, name: e.target.value })}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="patient-dob">Date of Birth *</label>
          <input
            type="date"
            id="patient-dob"
            value={patientPersona.dateOfBirth}
            onChange={(e) => setPatientPersona({ ...patientPersona, dateOfBirth: e.target.value })}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="insurance-type">Insurance Type *</label>
          <select
            id="insurance-type"
            value={patientPersona.insuranceType}
            onChange={(e) => setPatientPersona({ ...patientPersona, insuranceType: e.target.value })}
            required
          >
            <option value="public">Public Insurance</option>
            <option value="private">Private Insurance</option>
            <option value="none">No Insurance</option>
          </select>
        </div>

        <div className="persona-info-box">
          <h4>ℹ️ Why do we need this?</h4>
          <ul>
            <li><strong>Name:</strong> For appointment bookings and confirmations</li>
            <li><strong>Date of Birth:</strong> For medical records and age-appropriate care</li>
            <li><strong>Insurance:</strong> To find doctors that accept your insurance type</li>
          </ul>
          <p className="note">💾 Your information is saved locally and will be remembered for future searches</p>
        </div>

        <button type="submit" className="btn btn-primary btn-large">
          ✓ Save Profile & Continue
        </button>
      </form>
    </div>
  );
};

export default PersonaSetup;
