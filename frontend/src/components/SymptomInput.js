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
  { id: 10, label: '🌡️ Body Ache', value: 'body ache' },
  { id: 11, label: '🦷 Toothache', value: 'toothache dental pain' },
  { id: 12, label: '👁️ Eye Problems', value: 'eye pain vision problem' },
  { id: 13, label: '🩹 Skin Rash', value: 'skin rash itching' },
  { id: 14, label: '💔 Chest Pain', value: 'chest pain' }
];

const SymptomInput = () => {
  const { 
    patientPersona,
    searchInfo,
    setSearchInfo,
    symptoms, 
    setSymptoms, 
    analyzeAndFindDoctors, 
    isLoading,
    useGooglePlaces,
    setUseGooglePlaces,
    setCurrentStep
  } = useApp();

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!searchInfo.location || !symptoms) {
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

  const getAge = () => {
    if (!patientPersona.dateOfBirth) return null;
    const today = new Date();
    const birthDate = new Date(patientPersona.dateOfBirth);
    let age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
      age--;
    }
    return age;
  };

  return (
    <div className="card">
      {/* Patient Persona Display */}
      <div className="persona-header">
        <div className="persona-info">
          <h3>👤 {patientPersona.name}</h3>
          <div className="persona-details">
            <span>🎂 Age: {getAge()} years</span>
          </div>
        </div>
        <button 
          type="button" 
          className="btn btn-secondary btn-small"
          onClick={() => setCurrentStep('persona')}
        >
          ✏️ Edit Profile
        </button>
      </div>

      <h2>What are your symptoms today?</h2>
      <p className="subtitle">AI will automatically detect the right specialist and book an appointment</p>
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="patient-location">Where are you located?</label>
          <input
            type="text"
            id="patient-location"
            placeholder="Enter your address or zip code"
            value={searchInfo.location}
            onChange={(e) => setSearchInfo({ ...searchInfo, location: e.target.value })}
            required
          />
        </div>

        <div className="form-group">
          <label>Common symptoms</label>
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

        <div className="ai-info-box">
          <div className="info-icon">🤖</div>
          <div className="info-content">
            <strong>AI will handle everything</strong>
            <p>The AI will call the 3rd doctor (your test number), check your calendar, and book appointments automatically</p>
          </div>
        </div>

        <div className="form-group">
          <label className="permission-label">
            <input
              type="checkbox"
              checked={useGooglePlaces}
              onChange={(e) => setUseGooglePlaces(e.target.checked)}
            />
            <span>
              <strong>Search real doctors via Google Places</strong>
              <small>
                {process.env.REACT_APP_GOOGLE_PLACES_API_KEY
                  ? '✓ API Key configured - Real doctors will be searched' 
                  : '⚠️ API Key not configured - Using mock data'}
              </small>
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
