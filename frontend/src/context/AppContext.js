import React, { createContext, useContext, useState, useRef } from 'react';
import { mockDoctorDatabase } from '../utils/mockData';
import { analyzeSymptomText, findMatchingDoctors } from '../utils/helpers';
import { searchDoctorsByTextSearch, transformNewPlaceToDoctor } from '../utils/googlePlacesApi';
import { initiateCall, subscribeToCallEvents } from '../services/api';

// Helper function for delays
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

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
    name: 'John Smith',
    dateOfBirth: '2001-12-01',
    insuranceType: 'public' // 'public', 'private', or 'none'
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

  // Real call integration state
  const [callResult, setCallResult] = useState(null); // 'success' | 'failed' | null
  const [failureReason, setFailureReason] = useState('');
  const [activeCallSid, setActiveCallSid] = useState(null);

  // Ref to track if booking succeeded (for async callback)
  const bookingSucceededRef = useRef(false);

  const addAiProgress = (message, type = 'info') => {
    setAiProgress(prev => [...prev, { message, type, timestamp: new Date().toISOString() }]);
  };

  // Update the last progress item (useful for replacing "Calling..." with result)
  const updateLastProgress = (message, type) => {
    setAiProgress(prev => {
      if (prev.length === 0) return prev;
      const updated = [...prev];
      updated[updated.length - 1] = {
        ...updated[updated.length - 1],
        message,
        type
      };
      return updated;
    });
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

  /**
   * Attempt a real call to a doctor via the backend.
   * Returns a Promise that resolves to true if booking succeeded, false otherwise.
   */
  const attemptRealCall = (doctor) => {
    return new Promise(async (resolve) => {
      setSelectedDoctor(doctor);
      addAiProgress(`Calling ${doctor.name}...`, 'processing');

      try {
        const response = await initiateCall({
          doctorName: doctor.name,
          patientName: patientPersona.name,
          dateOfBirth: patientPersona.dateOfBirth,
          symptoms: symptoms,
          insuranceType: patientPersona.insuranceType
        });

        if (response.error) {
          updateLastProgress(`${doctor.name} - Failed to connect: ${response.error}`, 'error');
          resolve(false);
          return;
        }

        const { call_sid } = response;
        setActiveCallSid(call_sid);
        // Update "Calling..." to "Ringing..." (same message slot)
        updateLastProgress(`Ringing ${doctor.name}...`, 'processing');

        // Subscribe to real-time events
        const eventSource = subscribeToCallEvents(call_sid, (event) => {
          console.log('SSE Event:', event);

          if (event.type === 'status') {
            // Check if this is a completion message
            const msg = event.message.toLowerCase();
            if (msg.includes('booked successfully') || msg.includes('appointment confirmed')) {
              updateLastProgress(event.message, 'success');
            } else if (msg.includes('call ended') || msg.includes('failed') || msg.includes('error')) {
              updateLastProgress(event.message, 'error');
            } else {
              // Still in progress
              updateLastProgress(event.message, 'processing');
            }
          }

          if (event.type === 'tool_call') {
            if (event.tool === 'check_availability') {
              if (event.status === 'executing') {
                updateLastProgress(`Checking calendar availability...`, 'processing');
              } else if (event.result) {
                // Tool completed - show result
                if (event.result.available) {
                  updateLastProgress(`✓ Calendar slot is available`, 'success');
                } else {
                  updateLastProgress(`Calendar conflict - trying another time...`, 'info');
                }
              }
            }
            if (event.tool === 'find_available_slots') {
              if (event.status === 'executing') {
                updateLastProgress(`Finding available time slots...`, 'processing');
              } else if (event.result) {
                const count = event.result.count || event.result.available_slots?.length || 0;
                updateLastProgress(`Found ${count} available slots`, 'success');
              }
            }
            if (event.tool === 'book_appointment') {
              if (event.status === 'executing') {
                updateLastProgress(`Booking appointment...`, 'processing');
              } else if (event.result?.success) {
                // Booking succeeded!
                bookingSucceededRef.current = true;
                setSelectedSlot({
                  date: event.result.date,
                  time: event.result.time
                });
                updateLastProgress(`✓ Appointment booked for ${event.result.date} at ${event.result.time}!`, 'success');
              }
            }
            if (event.tool === 'end_call') {
              // Call is ending - update progress
              if (bookingSucceededRef.current) {
                updateLastProgress(`✓ Call completed - appointment confirmed!`, 'success');
              }
            }
          }

          if (event.type === 'call_ended') {
            eventSource.close();

            if (event.outcome === 'success' || bookingSucceededRef.current) {
              // Make sure to show success before transitioning
              updateLastProgress(`✓ Appointment successfully booked!`, 'success');
              setCallResult('success');
              setCurrentStep('success');
              resolve(true);
            } else {
              updateLastProgress(`${doctor.name} - Appointment failed: ${event.reason || 'Could not book appointment'}`, 'error');
              resolve(false);
            }
          }

          if (event.type === 'error') {
            eventSource.close();
            updateLastProgress(`${doctor.name} - Connection error: ${event.message}`, 'error');
            resolve(false);
          }
        });

      } catch (error) {
        console.error('Call error:', error);
        updateLastProgress(`${doctor.name} - Error: ${error.message}`, 'error');
        resolve(false);
      }
    });
  };

  const analyzeAndFindDoctors = async () => {
    setIsLoading(true);
    setAiProgress([]);
    setCallResult(null);
    setFailureReason('');
    bookingSucceededRef.current = false;
    setCurrentStep('processing');

    addAiProgress('Analyzing your symptoms...', 'processing');
    await delay(1500);

    const diagnosisResult = analyzeSymptomText(symptoms);
    setDiagnosis(diagnosisResult);
    updateLastProgress(`Diagnosis: ${diagnosisResult.condition}`, 'success');
    addAiProgress(`📋 Recommended specialties: ${diagnosisResult.specialties.join(', ')}`, 'info');
    
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    let matchedDoctors = [];
    
    // Try Google Places API if enabled (new Text Search API - much faster!)
    if (useGooglePlaces) {
      try {
        addAiProgress('🌍 Searching Google Places for real doctors near you...', 'processing');
        await new Promise(resolve => setTimeout(resolve, 500));

        const specialty = detectSpecialty(symptoms);
        // Update the same message to show specialty detection (keep spinner)
        updateLastProgress(`🔍 Detected specialty: ${specialty}. Searching nearby...`, 'processing');

        // Use new fast Text Search API (no need for Maps JS API to be loaded)
        const places = await searchDoctorsByTextSearch(
          specialty,
          searchInfo.location,
          4.0,  // Min rating
          10    // Max results
        );

        if (places && places.length > 0) {
          updateLastProgress(`🌍 Found ${places.length} ${specialty}s via Google Places`, 'success');

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
          updateLastProgress('🌍 No doctors found via Google Places, using mock data', 'info');
          matchedDoctors = findMatchingDoctors(symptoms, true, mockDoctorDatabase);
        }
      } catch (error) {
        console.error('Error searching Google Places:', error);
        updateLastProgress('🌍 Google Places search failed, using mock data', 'error');
        matchedDoctors = findMatchingDoctors(symptoms, true, mockDoctorDatabase);
      }
    } else {
      addAiProgress('Searching for qualified doctors in your area...', 'processing');
      await new Promise(resolve => setTimeout(resolve, 1500));
      updateLastProgress('Doctor search complete', 'success');
      matchedDoctors = findMatchingDoctors(symptoms, true, mockDoctorDatabase);
    }
    
    setAllDoctors(matchedDoctors);
    addAiProgress(`Found ${matchedDoctors.length} qualified doctors`, 'success');

    // AI decides which doctors to call
    await delay(1000);
    addAiProgress('AI is evaluating doctors based on multiple parameters...', 'processing');
    await delay(1500);

    // Calculate scores for top doctors
    const topDoctors = matchedDoctors.slice(0, 4); // Get top 4 for potential calls
    const comparisons = topDoctors.map(doctor => ({
      doctor,
      score: calculateDoctorScore(doctor),
      reasons: getScoreReasons(doctor, calculateDoctorScore(doctor))
    }));
    comparisons.sort((a, b) => b.score - a.score);
    setComparisonData(comparisons.slice(0, 3)); // Show top 3 in comparison

    updateLastProgress('Doctor evaluation complete', 'success');
    addAiProgress(`Calling top doctors to check availability...`, 'info');

    // Step 4: Doctors 1 & 2 - Simulated unavailable
    const simulatedReasons = ['No available slots this week', 'Line busy - try again later'];

    for (let i = 0; i < 2 && i < matchedDoctors.length; i++) {
      await delay(1500);
      const doctor = matchedDoctors[i];
      addAiProgress(`Calling ${doctor.name}...`, 'processing');
      await delay(2000);
      // Replace "Calling..." with error result (removes spinner)
      updateLastProgress(`${doctor.name} - ${simulatedReasons[i]}`, 'error');
      await delay(500);
    }

    // Step 5: Doctor 3 - REAL CALL
    if (matchedDoctors.length >= 3) {
      await delay(1000);
      addAiProgress(`Trying next available doctor...`, 'info');
      await delay(500);

      let bookingSuccess = await attemptRealCall(matchedDoctors[2]);

      // Step 6: Doctor 4 - FALLBACK if Doctor 3 failed
      if (!bookingSuccess && matchedDoctors.length >= 4) {
        await delay(1000);
        addAiProgress(`Trying another doctor...`, 'info');
        await delay(500);

        bookingSuccess = await attemptRealCall(matchedDoctors[3]);
      }

      // Step 7: If both failed, show failure screen
      if (!bookingSuccess) {
        setCallResult('failed');
        setFailureReason('Could not book an appointment with any available doctor. Please try again later.');
        setCurrentStep('failed');
      }
    } else {
      // Not enough doctors found
      setCallResult('failed');
      setFailureReason('Not enough doctors available in your area.');
      setCurrentStep('failed');
    }

    setIsLoading(false);
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

  /**
   * Retry the call sequence starting from doctor 3
   */
  const retryCall = async () => {
    setCallResult(null);
    setFailureReason('');
    bookingSucceededRef.current = false;
    setCurrentStep('processing');
    setAiProgress([]);

    addAiProgress('Retrying to book an appointment...', 'processing');
    await delay(1000);
    updateLastProgress('Retry initiated', 'success');

    // Try doctors 3 and 4 again
    if (allDoctors.length >= 3) {
      let bookingSuccess = await attemptRealCall(allDoctors[2]);

      if (!bookingSuccess && allDoctors.length >= 4) {
        await delay(1000);
        addAiProgress(`Trying another doctor...`, 'info');
        bookingSuccess = await attemptRealCall(allDoctors[3]);
      }

      if (!bookingSuccess) {
        setCallResult('failed');
        setFailureReason('Could not book an appointment. Please try again later.');
        setCurrentStep('failed');
      }
    }
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
    setCallResult(null);
    setFailureReason('');
    setActiveCallSid(null);
    bookingSucceededRef.current = false;
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
    callResult,
    failureReason,
    analyzeAndFindDoctors,
    confirmAppointment,
    startOver,
    retryCall
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};
