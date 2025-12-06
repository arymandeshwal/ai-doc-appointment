// Google Places API Configuration
export const GOOGLE_PLACES_CONFIG = {
  apiKey: process.env.REACT_APP_GOOGLE_PLACES_API_KEY || '',
  libraries: ['places'],
};

// NEW: Fast Text Search using Places API (New)
export const searchDoctorsByTextSearch = async (specialty, location, minRating = 4.0, maxResults = 10) => {
  const apiKey = GOOGLE_PLACES_CONFIG.apiKey;
  
  if (!apiKey) {
    console.error('Google Places API key is not configured');
    return [];
  }

  try {
    // Construct search query similar to Python version
    const searchQuery = `${specialty} in ${location}`;
    console.log(`🔎 Searching: "${searchQuery}"`);

    const url = 'https://places.googleapis.com/v1/places:searchText';
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': apiKey,
        'X-Goog-FieldMask': 'places.displayName,places.formattedAddress,places.internationalPhoneNumber,places.rating,places.userRatingCount,places.location,places.regularOpeningHours,places.businessStatus,places.websiteUri,places.id,places.types'
      },
      body: JSON.stringify({
        textQuery: searchQuery,
        minRating: minRating,
        maxResultCount: maxResults,
        languageCode: 'en',
        rankPreference: 'RELEVANCE'
      })
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} - ${response.statusText}`);
    }

    const data = await response.json();
    const places = data.places || [];
    
    console.log(`✅ Found ${places.length} doctors`);
    return places;

  } catch (error) {
    console.error('Error in text search:', error);
    return [];
  }
};

// Transform new Places API format to our doctor format
export const transformNewPlaceToDoctor = (place, index) => {
  // Calculate distance (would need patient coordinates for accurate distance)
  // For now, we'll use a default or extract from the data if available
  const distance = 5.0; // Default placeholder

  const phone = place.internationalPhoneNumber || 'Not available';
  const rating = place.rating || 4.0;
  const reviews = place.userRatingCount || 0;
  const name = place.displayName?.text || 'Unknown Doctor';
  const address = place.formattedAddress || 'Address not available';
  
  // Extract specialty from types
  const types = place.types || [];
  const specialty = extractSpecialtyFromTypes(types);

  // Check if open now
  const isOpen = place.businessStatus === 'OPERATIONAL';

  return {
    id: place.id || `doctor-${index}`,
    name: name,
    specialty: specialty,
    education: 'Licensed Medical Professional',
    experience: estimateExperienceFromReviews(reviews),
    distance: distance,
    rating: rating,
    reviews: reviews,
    address: address,
    phone: phone,
    price: estimatePrice(rating, reviews),
    insurance: true, // Assume true
    acceptsPrivateInsurance: true, // Most doctors accept private insurance
    acceptsPublicInsurance: rating >= 4.0, // Higher rated doctors more likely to accept public insurance
    languages: ['English'],
    availability: generateMockAvailability(),
    placeId: place.id,
    isOpen: isOpen,
    website: place.websiteUri || null,
    location: place.location,
    matchScore: 85 // Will be calculated based on symptoms
  };
};

// Helper: Extract specialty from types
const extractSpecialtyFromTypes = (types = []) => {
  const specialtyMap = {
    'dentist': 'Dentist',
    'doctor': 'General Practitioner',
    'hospital': 'Hospital',
    'health': 'Healthcare Provider',
    'medical': 'Medical Professional',
    'physiotherapist': 'Physiotherapist',
    'pharmacy': 'Pharmacy'
  };

  for (const type of types) {
    const lowerType = type.toLowerCase();
    for (const [key, value] of Object.entries(specialtyMap)) {
      if (lowerType.includes(key)) {
        return value;
      }
    }
  }
  
  return 'Medical Professional';
};

// Helper: Estimate experience from review count
const estimateExperienceFromReviews = (reviewCount = 0) => {
  if (reviewCount > 500) return 20;
  if (reviewCount > 300) return 15;
  if (reviewCount > 150) return 12;
  if (reviewCount > 50) return 8;
  return 5;
};

// Helper: Estimate price from rating and reviews
const estimatePrice = (rating, reviews) => {
  let price = 150; // Base price
  
  if (rating >= 4.5 && reviews > 200) price = 200;
  else if (rating >= 4.5) price = 175;
  else if (reviews > 300) price = 180;
  else if (rating < 4.0) price = 125;
  
  return price;
};

// Helper: Generate mock availability
const generateMockAvailability = () => {
  const availability = [];
  const today = new Date();
  
  for (let i = 1; i <= 5; i++) {
    const date = new Date(today);
    date.setDate(date.getDate() + i);
    const dateStr = date.toISOString().split('T')[0];
    
    availability.push(
      { date: dateStr, time: '9:00 AM' },
      { date: dateStr, time: '2:00 PM' }
    );
  }
  
  return availability;
};
