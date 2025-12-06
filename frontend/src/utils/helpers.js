export const analyzeSymptomText = (symptoms) => {
  const lowerSymptoms = symptoms.toLowerCase();
  
  if (lowerSymptoms.includes('fever') || lowerSymptoms.includes('cough') || lowerSymptoms.includes('cold')) {
    return {
      condition: "Possible Upper Respiratory Infection",
      severity: "Moderate",
      recommendations: "General Practitioner or Internal Medicine specialist recommended. Stay hydrated and rest.",
      specialties: ["General Practitioner", "Internal Medicine", "Family Medicine"]
    };
  } else if (lowerSymptoms.includes('pain') || lowerSymptoms.includes('ache')) {
    return {
      condition: "Pain Management Required",
      severity: "Variable",
      recommendations: "General evaluation recommended. Depending on location and severity, may need specialist referral.",
      specialties: ["General Practitioner", "Family Medicine", "Urgent Care Specialist"]
    };
  } else if (lowerSymptoms.includes('urgent') || lowerSymptoms.includes('emergency')) {
    return {
      condition: "Urgent Care Needed",
      severity: "High",
      recommendations: "Urgent Care Specialist or immediate medical attention recommended.",
      specialties: ["Urgent Care Specialist", "Emergency Medicine"]
    };
  } else {
    return {
      condition: "General Health Consultation",
      severity: "Low to Moderate",
      recommendations: "General health check-up recommended. A family doctor or general practitioner can help.",
      specialties: ["General Practitioner", "Family Medicine"]
    };
  }
};

export const findMatchingDoctors = (symptoms, privateInsurance, doctors) => {
  const diagnosis = analyzeSymptomText(symptoms);
  
  return doctors.map(doctor => {
    let matchScore = 0;
    
    if (diagnosis.specialties.includes(doctor.specialty)) {
      matchScore += 40;
    }
    
    if (privateInsurance === doctor.insurance) {
      matchScore += 20;
    }
    
    matchScore += (doctor.rating / 5) * 20;
    matchScore += Math.max(0, (10 - doctor.distance) * 2);
    
    return {
      ...doctor,
      matchScore: Math.min(100, Math.round(matchScore))
    };
  }).sort((a, b) => b.matchScore - a.matchScore);
};

export const downloadICS = (doctor, slot, symptoms) => {
  const [year, month, day] = slot.date.split('-');
  const [time, period] = slot.time.split(' ');
  let [hours, minutes] = time.split(':');
  
  if (period === 'PM' && hours !== '12') {
    hours = String(parseInt(hours) + 12);
  }
  if (period === 'AM' && hours === '12') {
    hours = '00';
  }

  const startDate = `${year}${month}${day}T${hours.padStart(2, '0')}${minutes}00`;
  const endHours = String((parseInt(hours) + 1) % 24).padStart(2, '0');
  const endDate = `${year}${month}${day}T${endHours}${minutes}00`;

  const icsContent = `BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//AI Doctor Appointment//EN
BEGIN:VEVENT
UID:${Date.now()}@aidoctorappointment.com
DTSTAMP:${startDate}
DTSTART:${startDate}
DTEND:${endDate}
SUMMARY:Doctor Appointment - ${doctor.name}
DESCRIPTION:Appointment with ${doctor.name} (${doctor.specialty})\\nSymptoms: ${symptoms}\\nPhone: ${doctor.phone}
LOCATION:${doctor.address}
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR`;

  const blob = new Blob([icsContent], { type: 'text/calendar' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `doctor-appointment-${slot.date}.ics`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
};
