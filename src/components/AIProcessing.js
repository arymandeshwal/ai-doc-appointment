import React from 'react';
import { useApp } from '../context/AppContext';

const AIProcessing = () => {
  const { aiProgress, comparisonData } = useApp();

  return (
    <div className="card">
      <h2>🤖 AI is Working</h2>
      <p className="subtitle">Please wait while our AI finds the best doctor for you</p>

      {/* Progress Log */}
      <div className="ai-progress-container">
        {aiProgress.map((item, index) => (
          <div key={index} className={`ai-progress-item ${item.type}`}>
            <div className="progress-icon">
              {item.type === 'processing' && <span className="spinner-small"></span>}
              {item.type === 'success' && <span className="check-icon">✓</span>}
              {item.type === 'info' && <span className="info-icon">ℹ</span>}
            </div>
            <div className="progress-message">{item.message}</div>
          </div>
        ))}
      </div>

      {/* Comparison Data */}
      {comparisonData.length > 0 && (
        <div className="comparison-section">
          <h3>🔍 AI Doctor Comparison</h3>
          <div className="comparison-grid">
            {comparisonData.map((item, index) => (
              <div key={index} className={`comparison-card ${index === 0 ? 'best-choice' : ''}`}>
                {index === 0 && <div className="best-badge">🏆 Best Match</div>}
                <div className="comparison-header">
                  <h4>{item.doctor.name}</h4>
                  <div className="comparison-score">
                    <span className="score-value">{item.score}</span>
                    <span className="score-label">Score</span>
                  </div>
                </div>
                <div className="comparison-specialty">{item.doctor.specialty}</div>
                <div className="comparison-reasons">
                  {item.reasons.map((reason, idx) => (
                    <div key={idx} className="reason-item">
                      <span className="reason-bullet">•</span>
                      <span>{reason}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AIProcessing;
