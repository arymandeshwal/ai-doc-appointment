import React, { useState } from 'react';
import { useApp } from '../context/AppContext';

const DoctorResults = () => {
  const {
    setCurrentStep,
    diagnosis,
    allDoctors,
    filteredDoctors,
    setFilteredDoctors,
    patientInfo,
    selectDoctorAndCall,
    isCalling,
    callingProgress
  } = useApp();

  const [sortBy, setSortBy] = useState('match');
  const [filterDistance, setFilterDistance] = useState(100);
  const [filterRating, setFilterRating] = useState(0);

  const handleSort = (value) => {
    setSortBy(value);
    let sorted = [...filteredDoctors];

    switch(value) {
      case 'distance':
        sorted.sort((a, b) => a.distance - b.distance);
        break;
      case 'rating':
        sorted.sort((a, b) => b.rating - a.rating);
        break;
      case 'education':
        sorted.sort((a, b) => b.experience - a.experience);
        break;
      case 'price':
        sorted.sort((a, b) => a.price - b.price);
        break;
      case 'availability':
        sorted.sort((a, b) => new Date(a.availability[0].date) - new Date(b.availability[0].date));
        break;
      default:
        sorted.sort((a, b) => b.matchScore - a.matchScore);
    }

    setFilteredDoctors(sorted);
  };

  const handleFilter = (distance, rating) => {
    const filtered = allDoctors.filter(doctor => 
      doctor.distance <= distance && doctor.rating >= rating
    );
    setFilteredDoctors(filtered);
  };

  const onFilterChange = (type, value) => {
    if (type === 'distance') {
      setFilterDistance(value);
      handleFilter(value, filterRating);
    } else {
      setFilterRating(value);
      handleFilter(filterDistance, value);
    }
  };

  return (
    <div className="card">
      <div className="section-header">
        <h2>AI Analysis & Recommended Doctors</h2>
        <button className="btn btn-secondary btn-small" onClick={() => setCurrentStep('symptom')}>
          ← Back
        </button>
      </div>

      {/* AI Analysis */}
      <div className="ai-analysis">
        <div className="analysis-header">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L15 8L22 9L17 14L18 21L12 18L6 21L7 14L2 9L9 8L12 2Z" fill="#F59E0B"/>
          </svg>
          <h3>AI Analysis Results</h3>
        </div>
        <div className="analysis-content">
          <p><strong>Condition:</strong> {diagnosis.condition}</p>
          <p><strong>Severity:</strong> {diagnosis.severity}</p>
          <p><strong>Recommendations:</strong> {diagnosis.recommendations}</p>
          <p><strong>Suggested Specialties:</strong> {diagnosis.specialties.join(', ')}</p>
        </div>
      </div>

      {/* Controls */}
      <div className="controls">
        <div className="control-group">
          <label>Sort by:</label>
          <select value={sortBy} onChange={(e) => handleSort(e.target.value)}>
            <option value="match">Best Match</option>
            <option value="distance">Distance</option>
            <option value="rating">Rating</option>
            <option value="education">Education Level</option>
            <option value="price">Price (Low to High)</option>
            <option value="availability">Earliest Available</option>
          </select>
        </div>

        <div className="control-group">
          <label>Max Distance:</label>
          <select value={filterDistance} onChange={(e) => onFilterChange('distance', parseFloat(e.target.value))}>
            <option value="100">Any Distance</option>
            <option value="5">Within 5 miles</option>
            <option value="10">Within 10 miles</option>
            <option value="25">Within 25 miles</option>
          </select>
        </div>

        <div className="control-group">
          <label>Min Rating:</label>
          <select value={filterRating} onChange={(e) => onFilterChange('rating', parseFloat(e.target.value))}>
            <option value="0">Any Rating</option>
            <option value="3">3+ Stars</option>
            <option value="4">4+ Stars</option>
            <option value="4.5">4.5+ Stars</option>
          </select>
        </div>
      </div>

      {/* Doctor Cards */}
      <div className="doctor-list">
        {filteredDoctors.length === 0 ? (
          <p style={{ textAlign: 'center', padding: '40px', color: '#6B7280' }}>
            No doctors found matching your criteria.
          </p>
        ) : (
          filteredDoctors.map(doctor => (
            <div key={doctor.id} className="doctor-card" onClick={() => selectDoctorAndCall(doctor)}>
              <div className="doctor-header">
                <div className="doctor-info">
                  <h3>{doctor.name}</h3>
                  <div className="doctor-specialty">{doctor.specialty}</div>
                </div>
                <div className="doctor-badge">
                  {doctor.experience} Years Exp
                </div>
              </div>
              
              <div className="doctor-education">
                🎓 {doctor.education}
              </div>

              <div className="doctor-details">
                <div className="detail-item">
                  <span>📍</span>
                  <span><strong>{doctor.distance} miles</strong> away</span>
                </div>
                <div className="detail-item rating">
                  <span className="stars">{'⭐'.repeat(Math.floor(doctor.rating))}</span>
                  <span><strong>{doctor.rating}</strong> ({doctor.reviews} reviews)</span>
                </div>
                <div className="detail-item">
                  <span>💬</span>
                  <span>{doctor.languages.join(', ')}</span>
                </div>
                <div className="detail-item">
                  <span>🏥</span>
                  <span>{doctor.insurance ? 'Accepts Insurance' : 'Cash Only'}</span>
                </div>
              </div>

              <div className="availability-info">
                <strong>Next Available:</strong>
                {doctor.availability.slice(0, 3).map((slot, idx) => (
                  <span key={idx} className="time-slot">
                    {slot.date} at {slot.time}
                  </span>
                ))}
              </div>

              <div className="price-tag">
                {patientInfo.privateInsurance && doctor.insurance 
                  ? `$${(doctor.price * 0.2).toFixed(0)} copay`
                  : `$${doctor.price}`}
              </div>

              <div className="match-score">
                {doctor.matchScore}% Match
              </div>
            </div>
          ))
        )}
      </div>

      {/* AI Calling Status */}
      {isCalling && (
        <div className="ai-status">
          <div className="status-icon">
            <span className="spinner"></span>
          </div>
          <div className="status-content">
            <h3>AI is contacting doctors...</h3>
            <p>{callingProgress}</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default DoctorResults;
