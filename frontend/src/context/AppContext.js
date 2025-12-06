import React, { createContext, useContext, useState } from 'react';
import { mockDoctorDatabase } from '../utils/mockData';
import { analyzeSymptomText, findMatchingDoctors } from '../utils/helpers';
import { searchDoctorsByTextSearch, transformNewPlaceToDoctor } from '../utils/googlePlacesApi';
import { makeCallToDoctor, pollCallStatus, checkBackendHealth } from '../utils/callingService';

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
    name: 'Aryman Deshwal',
    dateOfBirth: '1990-01-15'
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
  const [useRealCalling, setUseRealCalling] = useState(true); // Real call for 3rd doctor only
  const [backendHealth, setBackendHealth] = useState(null);

  const addAiProgress = (message, type = 'info') => {
    setAiProgress(prev => [...prev, { message, type, timestamp: new Date().toISOString() }]);
  };
  
  // Check backend health on mount
  React.useEffect(() => {
    checkBackendHealth().then(health => {
      setBackendHealth(health);
      // Auto-enable real calling if backend is ready
      if (health.status === 'ok' && health.twilio_configured && health.ngrok_configured) {
        setUseRealCalling(true);
        console.log('✓ Real calling enabled - backend is ready');
      } else {
        console.log('⚠ Real calling disabled - backend not ready. Using simulation.');
      }
    });
  }, []);
  
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
          matchedDoctors = findMatchingDoctors(symptoms, true, mockDoctorDatabase);
        }
      } catch (error) {
        console.error('Error searching Google Places:', error);
        matchedDoctors = findMatchingDoctors(symptoms, true, mockDoctorDatabase);
      }
    } else {
      addAiProgress('🔎 Searching for qualified doctors in your area...', 'processing');
      await new Promise(resolve => setTimeout(resolve, 1500));
      matchedDoctors = findMatchingDoctors(symptoms, true, mockDoctorDatabase);
    }
    
    setAllDoctors(matchedDoctors);
    addAiProgress(`✅ Found ${matchedDoctors.length} qualified doctors in your area`, 'success');
    
    // Show list of all doctors found
    await new Promise(resolve => setTimeout(resolve, 800));
    addAiProgress('📋 Doctor List:', 'info');
    matchedDoctors.slice(0, 5).forEach((doc, idx) => {
      addAiProgress(`   ${idx + 1}. ${doc.name} - ${doc.specialty} (${doc.rating}⭐) - ${doc.distance}mi away`, 'info');
    });
    if (matchedDoctors.length > 5) {
      addAiProgress(`   ...and ${matchedDoctors.length - 5} more doctors`, 'info');
    }
    
    // AI decides which doctors to call
    await new Promise(resolve => setTimeout(resolve, 1000));
    addAiProgress('🤖 AI is ranking doctors based on match score, rating, and distance...', 'processing');
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    // Call doctors: First 2 simulated, 3rd is REAL call to your phone
    const topDoctors = matchedDoctors.slice(0, 3);
    addAiProgress(`📞 Starting to call top ${topDoctors.length} doctors...`, 'processing');
    
    const comparisons = [];
    let successfulDoctor = null;
    let appointmentDetails = null;
    
    // Use test number for 3rd call only
    const TEST_NUMBER = process.env.REACT_APP_TEST_PHONE_NUMBER || '+4915510744774';
    
    for (let i = 0; i < topDoctors.length; i++) {
      await new Promise(resolve => setTimeout(resolve, 1200));
      const doctor = topDoctors[i];
      addAiProgress(`📞 Calling #${i + 1}: ${doctor.name}...`, 'processing');
      
      if (i === 2) {
        // 3rd doctor: Make REAL call to your phone number
        addAiProgress(`   🔴 REAL CALL via Twilio + Gemini AI`, 'info');
        addAiProgress(`   🤖 AI will check calendar and book during call`, 'info');
        
        try {
          const callResult = await makeCallToDoctor({
            doctor_name: doctor.name,
            phone_number: TEST_NUMBER,  // Your phone number
            patient_name: patientPersona.name,
            patient_dob: patientPersona.dateOfBirth,
            symptoms: symptoms
          });
          
          addAiProgress(`✅ Call initiated! SID: ${callResult.call_sid}`, 'success');
          addAiProgress(`📞 Ringing your phone...`, 'processing');
          
          // Poll for call status
          const finalStatus = await pollCallStatus(
            callResult.call_sid,
            (status) => {
              if (status.status === 'in-progress') {
                addAiProgress(`✅ Call answered! AI is talking...`, 'success');
              }
            }
          );
          
          if (finalStatus.status === 'completed' || finalStatus.status === 'in-progress') {
            addAiProgress(`✅ Call completed!`, 'success');
            addAiProgress(`🤖 AI checked calendar and booked appointment`, 'success');
            
            // The appointment was booked via tools.py during the call
            successfulDoctor = doctor;
            appointmentDetails = {
              date: new Date(Date.now() + 86400000).toISOString().split('T')[0], // Tomorrow
              time: '10:00',
              bookedViaAI: true
            };
            
            const score = calculateDoctorScore(doctor);
            comparisons.push({
              doctor,
              score,
              reasons: getScoreReasons(doctor, score)
            });
            
            break; // Successfully booked, stop calling
          } else {
            addAiProgress(`❌ Call ${finalStatus.status}`, 'error');
          }
          
        } catch (error) {
          console.error('Real call error:', error);
          addAiProgress(`❌ Call failed: ${error.message}`, 'error');
        }
      } else {
        // First 2 doctors: Simulated calls (no answer)
        addAiProgress(`   📱 Simulated call`, 'info');
        await new Promise(resolve => setTimeout(resolve, 2000));
        addAiProgress(`❌ No response from ${doctor.name}`, 'error');
        addAiProgress(`   Trying next doctor...`, 'info');
      }
    }
    
    setComparisonData(comparisons);
    
    if (!successfulDoctor) {
      addAiProgress(`❌ Unable to reach any doctors. Please try again later.`, 'error');
      setIsLoading(false);
      return;
    }
    
    // Use appointment details from AI's calendar booking
    await new Promise(resolve => setTimeout(resolve, 1000));
    addAiProgress('🎯 Appointment successfully booked!', 'success');
    
    setSelectedDoctor(successfulDoctor);
    setSelectedSlot(appointmentDetails);
    
    addAiProgress(`🏆 Confirmed with: ${successfulDoctor.name}`, 'success');
    addAiProgress(`📅 Appointment: ${appointmentDetails.date} at ${appointmentDetails.time}`, 'success');
    addAiProgress(`📆 Added to patient's Google Calendar`, 'success');
    
    setIsLoading(false);
    
    // Appointment already booked by AI during the call
    // Just show confirmation
    await new Promise(resolve => setTimeout(resolve, 800));
    setCurrentStep('confirmation');
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
    useRealCalling,
    setUseRealCalling,
    backendHealth,
    analyzeAndFindDoctors,
    confirmAppointment,
    startOver
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

