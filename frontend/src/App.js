import React from 'react';
import { AppProvider, useApp } from './context/AppContext';
import PersonaSetup from './components/PersonaSetup';
import SymptomInput from './components/SymptomInput';
import AIProcessing from './components/AIProcessing';
import Confirmation from './components/Confirmation';
import Success from './components/Success';
import './App.css';

const AppContent = () => {
  const { currentStep } = useApp();

  return (
    <div className="container">
      
      {/* Header */}
      <header className="header">
        <div className="logo">
          <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
            <path d="M20 5L25 15H15L20 5Z" fill="#4F46E5"/>
            <rect x="18" y="15" width="4" height="10" fill="#4F46E5"/>
            <circle cx="20" cy="30" r="5" fill="#4F46E5"/>
          </svg>
          <h1>AI Doctor Appointment</h1>
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content">
        {currentStep === 'persona' && <PersonaSetup />}
        {currentStep === 'symptom' && <SymptomInput />}
        {currentStep === 'processing' && <AIProcessing />}
        {currentStep === 'confirmation' && <Confirmation />}
        {currentStep === 'success' && <Success />}
      </main>

      {/* Footer */}
      <footer className="footer">
        <p>© 2025 AI Doctor Appointment. Powered by Advanced AI Technology.</p>
      </footer>
    </div>
  );
};

function App() {
  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  );
}

export default App;
