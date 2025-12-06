import React from 'react';
import { useApp } from '../context/AppContext';

const commonSymptoms = [
  { id: 1, label: '🤒 Fever', value: 'fever' },
  { id: 2, label: '🤧 Cough & Cold', value: 'cough and cold' },
  { id: 3, label: '😷 Sore Throat', value: 'sore throat' },
  { id: 4, label: '🤕 Headache', value: 'headache' },
  { id: 5, label: '💊 Stomach Pain', value: 'stomach pain' },
  { id: 6, label: '🦴 Back Pain', value: 'back pain' },
  { id: 7, label: '🫁 Breathing Issues', value: 'breathing difficulty' },
  { id: 8, label: '😴 Fatigue', value: 'fatigue and tiredness' },
  { id: 9, label: '🤢 Nausea', value: 'nausea and vomiting' },
  { id: 10, label: '🌡️ Body Ache', value: 'body ache' }
];

const SymptomInput = () => {
  const { patientInfo, setPatientInfo, symptoms, setSymptoms, analyzeAndFindDoctors, isLoading } = useApp();

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!patientInfo.location || !symptoms) {
      alert('Please enter your location and symptoms.');
      return;
    }
    analyzeAndFindDoctors();
  };

  const handleSymptomClick = (symptom) => {
    if (symptoms.includes(symptom.value)) {
      // Remove if already selected
      setSymptoms(symptoms.replace(symptom.value, '').replace(/,\s*,/g, ',').replace(/^,\s*|,\s*$/g, '').trim());
    } else {
      // Add to symptoms
      setSymptoms(symptoms ? `${symptoms}, ${symptom.value}` : symptom.value);
    }
  };

  const isSymptomSelected = (symptom) => symptoms.includes(symptom.value);

  return (
    <div className="card">
      <h2>What are your symptoms?</h2>
      <p className="subtitle">Our AI will automatically find and book the best doctor for you</p>
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="patient-location">Your Location</label>
          <input
            type="text"
            id="patient-location"
            placeholder="Enter your address or zip code"
            value={patientInfo.location}
            onChange={(e) => setPatientInfo({ ...patientInfo, location: e.target.value })}
            required
          />
        </div>

        <div className="form-group">
          <label>Quick Select Symptoms (Click to add/remove)</label>
          <div className="symptom-chips">
            {commonSymptoms.map(symptom => (
              <button
                key={symptom.id}
                type="button"
                className={`symptom-chip ${isSymptomSelected(symptom) ? 'selected' : ''}`}
                onClick={() => handleSymptomClick(symptom)}
              >
                {symptom.label}
              </button>
            ))}
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="symptoms">Or describe your symptoms</label>
          <textarea
            id="symptoms"
            rows="4"
            placeholder="Describe any other symptoms or provide more details..."
            value={symptoms}
            onChange={(e) => setSymptoms(e.target.value)}
          />
        </div>

        <div className="form-group calendar-permission">
          <label className="permission-label">
            <input
              type="checkbox"
              checked={patientInfo.autoBook}
              onChange={(e) => setPatientInfo({ ...patientInfo, autoBook: e.target.checked })}
            />
            <span>
              <strong>Let AI book directly to my calendar</strong>
              <small>AI will automatically select and book the best appointment without asking</small>
            </span>
          </label>
        </div>

        <button type="submit" className="btn btn-primary btn-large" disabled={isLoading}>
          {isLoading ? (
            <>
              <span className="spinner"></span> AI is working...
            </>
          ) : (
            '🤖 Let AI Find & Book Doctor'
          )}
        </button>
      </form>
    </div>
  );
};

export default SymptomInput;
