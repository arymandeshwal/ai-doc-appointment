import React, { createContext, useContext, useState } from 'react';
import { mockDoctorDatabase } from '../utils/mockData';
import { analyzeSymptomText, findMatchingDoctors } from '../utils/helpers';

const AppContext = createContext();

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within AppProvider');
  }
  return context;
};

export const AppProvider = ({ children }) => {
  const [currentStep, setCurrentStep] = useState('symptom');
  const [patientInfo, setPatientInfo] = useState({
    location: '',
    autoBook: false
  });
  const [symptoms, setSymptoms] = useState('');
  const [diagnosis, setDiagnosis] = useState(null);
  const [allDoctors, setAllDoctors] = useState([]);
  const [selectedDoctor, setSelectedDoctor] = useState(null);
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [aiProgress, setAiProgress] = useState([]);
  const [comparisonData, setComparisonData] = useState([]);

  const addAiProgress = (message, type = 'info') => {
    setAiProgress(prev => [...prev, { message, type, timestamp: new Date().toISOString() }]);
  };

  const analyzeAndFindDoctors = async () => {
    setIsLoading(true);
    setAiProgress([]);
    setCurrentStep('processing');
    
    addAiProgress('🔍 Analyzing your symptoms...', 'processing');
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    const diagnosisResult = analyzeSymptomText(symptoms);
    setDiagnosis(diagnosisResult);
    addAiProgress(`✅ Diagnosis: ${diagnosisResult.condition}`, 'success');
    addAiProgress(`📋 Recommended specialties: ${diagnosisResult.specialties.join(', ')}`, 'info');
    
    await new Promise(resolve => setTimeout(resolve, 1000));
    addAiProgress('🔎 Searching for qualified doctors in your area...', 'processing');
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    const matchedDoctors = findMatchingDoctors(symptoms, true, mockDoctorDatabase);
    setAllDoctors(matchedDoctors);
    addAiProgress(`✅ Found ${matchedDoctors.length} qualified doctors`, 'success');
    
    // AI decides which doctors to call
    await new Promise(resolve => setTimeout(resolve, 1000));
    addAiProgress('🤖 AI is evaluating doctors based on multiple parameters...', 'processing');
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    // AI calls top 3 doctors
    const topDoctors = matchedDoctors.slice(0, 3);
    addAiProgress(`📞 Calling top ${topDoctors.length} doctors to check availability...`, 'processing');
    
    const comparisons = [];
    for (let i = 0; i < topDoctors.length; i++) {
      await new Promise(resolve => setTimeout(resolve, 1200));
      const doctor = topDoctors[i];
      addAiProgress(`📞 Calling ${doctor.name}...`, 'processing');
      
      await new Promise(resolve => setTimeout(resolve, 800));
      addAiProgress(`✅ ${doctor.name} is available`, 'success');
      
      // Calculate score for comparison
      const score = calculateDoctorScore(doctor);
      comparisons.push({
        doctor,
        score,
        reasons: getScoreReasons(doctor, score)
      });
    }
    
    setComparisonData(comparisons);
    
    // AI compares and makes decision
    await new Promise(resolve => setTimeout(resolve, 1000));
    addAiProgress('🤔 Comparing all available options...', 'processing');
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    // Sort by score and pick best
    comparisons.sort((a, b) => b.score - a.score);
    const bestDoctor = comparisons[0].doctor;
    const bestSlot = bestDoctor.availability[0];
    
    setSelectedDoctor(bestDoctor);
    setSelectedSlot(bestSlot);
    
    addAiProgress(`🏆 Best match found: ${bestDoctor.name}`, 'success');
    addAiProgress(`📅 Best available time: ${bestSlot.date} at ${bestSlot.time}`, 'success');
    
    setIsLoading(false);
    
    // Auto-book or ask for confirmation
    if (patientInfo.autoBook) {
      await new Promise(resolve => setTimeout(resolve, 1000));
      addAiProgress('📅 Automatically booking appointment to your calendar...', 'processing');
      await new Promise(resolve => setTimeout(resolve, 1500));
      addAiProgress('✅ Appointment confirmed and added to calendar!', 'success');
      setCurrentStep('success');
    } else {
      setCurrentStep('confirmation');
    }
  };

  const calculateDoctorScore = (doctor) => {
    let score = 0;
    
    // Match score (40 points)
    score += doctor.matchScore * 0.4;
    
    // Rating (25 points)
    score += (doctor.rating / 5) * 25;
    
    // Distance (20 points - closer is better)
    score += Math.max(0, (10 - doctor.distance) * 2);
    
    // Experience (15 points)
    score += Math.min(15, doctor.experience * 0.75);
    
    return Math.round(score);
  };

  const getScoreReasons = (doctor, score) => {
    const reasons = [];
    
    if (doctor.matchScore >= 80) {
      reasons.push('Excellent specialty match for your condition');
    }
    if (doctor.rating >= 4.7) {
      reasons.push(`Highly rated (${doctor.rating}⭐ from ${doctor.reviews} reviews)`);
    }
    if (doctor.distance <= 5) {
      reasons.push(`Very close to you (${doctor.distance} miles)`);
    }
    if (doctor.experience >= 15) {
      reasons.push(`${doctor.experience} years of experience`);
    }
    if (doctor.insurance) {
      reasons.push('Accepts insurance');
    }
    reasons.push(`Available: ${doctor.availability[0].date} at ${doctor.availability[0].time}`);
    
    return reasons;
  };

  const confirmAppointment = () => {
    setCurrentStep('success');
  };

  const startOver = () => {
    setCurrentStep('symptom');
    setPatientInfo({
      location: '',
      autoBook: false
    });
    setSymptoms('');
    setDiagnosis(null);
    setAllDoctors([]);
    setSelectedDoctor(null);
    setSelectedSlot(null);
    setIsLoading(false);
    setAiProgress([]);
    setComparisonData([]);
  };

  const value = {
    currentStep,
    setCurrentStep,
    patientInfo,
    setPatientInfo,
    symptoms,
    setSymptoms,
    diagnosis,
    allDoctors,
    selectedDoctor,
    selectedSlot,
    isLoading,
    aiProgress,
    comparisonData,
    analyzeAndFindDoctors,
    confirmAppointment,
    startOver
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

