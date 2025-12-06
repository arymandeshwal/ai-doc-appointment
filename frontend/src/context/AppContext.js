import React, { createContext, useContext, useState } from 'react';
import { mockDoctorDatabase } from '../utils/mockData';
import { analyzeSymptomText, findMatchingDoctors } from '../utils/helpers';
import { searchDoctorsByTextSearch, transformNewPlaceToDoctor } from '../utils/googlePlacesApi';

const AppContext = createContext();

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within AppProvider');
  }
  return context;
};

export const AppProvider = ({ children }) => {
  const [currentStep, setCurrentStep] = useState('persona'); // Start with persona setup
  
  // Patient Persona (set once, persists across searches)
  const [patientPersona, setPatientPersona] = useState({
    name: '',
    dateOfBirth: ''
  });
  
  // Search Info (changes per search)
  const [searchInfo, setSearchInfo] = useState({
    location: '',
    symptoms: '',
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
  const [useGooglePlaces, setUseGooglePlaces] = useState(true);

  const addAiProgress = (message, type = 'info') => {
    setAiProgress(prev => [...prev, { message, type, timestamp: new Date().toISOString() }]);
  };
  
  // Intelligent specialty detection based on symptoms
  const detectSpecialty = (symptomsText) => {
    const lowerSymptoms = symptomsText.toLowerCase();
    
    // Dental issues
    if (lowerSymptoms.match(/tooth|teeth|dental|cavity|gum|jaw pain|toothache|wisdom tooth/)) {
      return 'dentist';
    }
    
    // Eye issues
    if (lowerSymptoms.match(/eye|vision|blind|sight|glasses|contact lens/)) {
      return 'ophthalmologist';
    }
    
    // Skin issues
    if (lowerSymptoms.match(/skin|rash|acne|eczema|psoriasis|mole|dermat/)) {
      return 'dermatologist';
    }
    
    // Mental health
    if (lowerSymptoms.match(/depress|anxiety|mental|stress|panic|therapy|psychiatr/)) {
      return 'psychiatrist';
    }
    
    // Bone/joint issues
    if (lowerSymptoms.match(/bone|joint|fracture|sprain|orthoped|back pain|neck pain|shoulder pain/)) {
      return 'orthopedic';
    }
    
    // Heart issues
    if (lowerSymptoms.match(/heart|chest pain|cardio|blood pressure|palpitation/)) {
      return 'cardiologist';
    }
    
    // Children
    if (lowerSymptoms.match(/child|baby|infant|pediatr|kid/)) {
      return 'pediatrician';
    }
    
    // Pregnancy/women's health
    if (lowerSymptoms.match(/pregnan|gynecolog|period|menstrual|obstetr/)) {
      return 'obstetrician';
    }
    
    // Default to general practitioner
    return 'doctor';
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
    
    let matchedDoctors = [];
    
    // Try Google Places API if enabled (new Text Search API - much faster!)
    if (useGooglePlaces) {
      try {
        addAiProgress('🌍 Searching Google Places for real doctors near you...', 'processing');
        await new Promise(resolve => setTimeout(resolve, 500));
        
        const specialty = detectSpecialty(symptoms);
        addAiProgress(`🔍 Detected specialty needed: ${specialty}`, 'info');
        
        // Use new fast Text Search API (no need for Maps JS API to be loaded)
        const places = await searchDoctorsByTextSearch(
          specialty,
          searchInfo.location,
          4.0,  // Min rating
          10    // Max results
        );
        
        if (places && places.length > 0) {
          addAiProgress(`✅ Found ${places.length} doctors via Google Places`, 'success');
          
          // Transform Google Places results to our format
          matchedDoctors = places.slice(0, 8).map((place, index) => 
            transformNewPlaceToDoctor(place, index)
          );
          
          // Calculate match scores based on symptoms
          matchedDoctors = matchedDoctors.map(doctor => ({
            ...doctor,
            matchScore: calculateMatchScore(doctor, diagnosisResult)
          }));
          
          // Sort by match score
          matchedDoctors.sort((a, b) => b.matchScore - a.matchScore);
        } else {
          addAiProgress('⚠️ No doctors found via Google Places, using mock data', 'info');
          matchedDoctors = findMatchingDoctors(symptoms, true, mockDoctorDatabase);
        }
      } catch (error) {
        console.error('Error searching Google Places:', error);
        addAiProgress('⚠️ Google Places search failed, using mock data', 'info');
        matchedDoctors = findMatchingDoctors(symptoms, true, mockDoctorDatabase);
      }
    } else {
      addAiProgress('🔎 Searching for qualified doctors in your area...', 'processing');
      await new Promise(resolve => setTimeout(resolve, 1500));
      matchedDoctors = findMatchingDoctors(symptoms, true, mockDoctorDatabase);
    }
    
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
    if (searchInfo.autoBook) {
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

  const calculateMatchScore = (doctor, diagnosis) => {
    let score = 50; // Base score
    
    // Specialty match
    const doctorSpecialty = doctor.specialty.toLowerCase();
    const hasMatch = diagnosis.specialties.some(spec => 
      doctorSpecialty.includes(spec.toLowerCase()) || 
      spec.toLowerCase().includes(doctorSpecialty)
    );
    if (hasMatch) score += 30;
    
    // Rating bonus
    score += (doctor.rating / 5) * 10;
    
    // Distance bonus (closer is better)
    if (doctor.distance <= 3) score += 10;
    else if (doctor.distance <= 5) score += 5;
    
    return Math.min(100, Math.round(score));
  };

  const confirmAppointment = () => {
    setCurrentStep('success');
  };

  const startOver = () => {
    setCurrentStep('symptom'); // Go back to symptom input, persona stays
    setSearchInfo({
      location: '',
      symptoms: '',
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
    patientPersona,
    setPatientPersona,
    searchInfo,
    setSearchInfo,
    symptoms,
    setSymptoms,
    diagnosis,
    allDoctors,
    selectedDoctor,
    selectedSlot,
    isLoading,
    aiProgress,
    comparisonData,
    useGooglePlaces,
    setUseGooglePlaces,
    analyzeAndFindDoctors,
    confirmAppointment,
    startOver
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};
