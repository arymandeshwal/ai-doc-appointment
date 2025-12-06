import React, { createContext, useContext, useState, useRef } from 'react';
import { mockDoctorDatabase } from '../utils/mockData';
import { analyzeSymptomText, findMatchingDoctors } from '../utils/helpers';
import { initiateCall, subscribeToCallEvents } from '../services/api';

const AppContext = createContext();

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within AppProvider');
  }
  return context;
};

// Helper function for delays
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

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

  // New state for real call integration
  const [callResult, setCallResult] = useState(null); // 'success' | 'failed' | null
  const [failureReason, setFailureReason] = useState('');
  const [activeCallSid, setActiveCallSid] = useState(null);

  // Ref to track if booking succeeded (for async callback)
  const bookingSucceededRef = useRef(false);

  const addAiProgress = (message, type = 'info') => {
    setAiProgress(prev => [...prev, { message, type, timestamp: new Date().toISOString() }]);
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
        const response = await initiateCall(doctor.name);

        if (response.error) {
          addAiProgress(`Failed to call ${doctor.name}: ${response.error}`, 'error');
          resolve(false);
          return;
        }

        const { call_sid } = response;
        setActiveCallSid(call_sid);
        addAiProgress(`Ringing ${doctor.name}...`, 'processing');

        // Subscribe to real-time events
        const eventSource = subscribeToCallEvents(call_sid, (event) => {
          console.log('SSE Event:', event);

          if (event.type === 'status') {
            addAiProgress(event.message, 'processing');
          }

          if (event.type === 'tool_call') {
            if (event.tool === 'check_availability' && event.status === 'executing') {
              addAiProgress(`Checking calendar availability...`, 'processing');
            }
            if (event.tool === 'book_appointment' && event.result?.success) {
              // Booking succeeded!
              bookingSucceededRef.current = true;
              setSelectedSlot({
                date: event.result.date,
                time: event.result.time
              });
              addAiProgress(`Appointment booked for ${event.result.date} at ${event.result.time}!`, 'success');
            }
          }

          if (event.type === 'call_ended') {
            eventSource.close();

            if (event.outcome === 'success' || bookingSucceededRef.current) {
              setCallResult('success');
              setCurrentStep('success');
              resolve(true);
            } else {
              addAiProgress(`${doctor.name} - ${event.reason || 'Could not book appointment'}`, 'error');
              resolve(false);
            }
          }

          if (event.type === 'error') {
            eventSource.close();
            addAiProgress(`Connection error: ${event.message}`, 'error');
            resolve(false);
          }
        });

      } catch (error) {
        console.error('Call error:', error);
        addAiProgress(`Error calling ${doctor.name}: ${error.message}`, 'error');
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

    // Step 1: Analyze symptoms
    addAiProgress('Analyzing your symptoms...', 'processing');
    await delay(1500);

    const diagnosisResult = analyzeSymptomText(symptoms);
    setDiagnosis(diagnosisResult);
    addAiProgress(`Diagnosis: ${diagnosisResult.condition}`, 'success');
    addAiProgress(`Recommended specialties: ${diagnosisResult.specialties.join(', ')}`, 'info');

    // Step 2: Find doctors
    await delay(1000);
    addAiProgress('Searching for qualified doctors in your area...', 'processing');
    await delay(1500);

    const matchedDoctors = findMatchingDoctors(symptoms, true, mockDoctorDatabase);
    setAllDoctors(matchedDoctors);
    addAiProgress(`Found ${matchedDoctors.length} qualified doctors`, 'success');

    // Step 3: AI evaluation
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

    addAiProgress(`Calling top doctors to check availability...`, 'processing');

    // Step 4: Doctors 1 & 2 - Simulated unavailable
    const simulatedReasons = ['No available slots this week', 'Line busy - try again later'];

    for (let i = 0; i < 2 && i < matchedDoctors.length; i++) {
      await delay(1500);
      const doctor = matchedDoctors[i];
      addAiProgress(`Calling ${doctor.name}...`, 'processing');
      await delay(2000);
      addAiProgress(`${doctor.name} - ${simulatedReasons[i]}`, 'error');
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
      reasons.push(`Highly rated (${doctor.rating} from ${doctor.reviews} reviews)`);
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
    setCallResult(null);
    setFailureReason('');
    setActiveCallSid(null);
    bookingSucceededRef.current = false;
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
    callResult,
    failureReason,
    analyzeAndFindDoctors,
    confirmAppointment,
    startOver,
    retryCall
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};
