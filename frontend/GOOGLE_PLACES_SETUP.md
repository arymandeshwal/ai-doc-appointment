# Google Places API Integration Guide

## Overview
This application now integrates with Google Places API to search for real doctors near the patient's location.

## Features
- Real-time doctor search based on location
- Specialty-based filtering
- Distance calculation
- Google ratings and reviews
- Operating hours
- Contact information

## Setup Instructions

### 1. Get Google Places API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to "APIs & Services" > "Library"
4. Enable the following APIs:
   - **Places API**
   - **Geocoding API**
   - **Maps JavaScript API**

### 2. Create API Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "API Key"
3. Copy the generated API key
4. (Optional but recommended) Click "Restrict Key":
   - Add HTTP referrers (for production): `https://yourdomain.com/*`
   - Add API restrictions: Select only the APIs you enabled

### 3. Configure the Application

1. Create a `.env` file in the project root:
```bash
cp .env.example .env
```

2. Add your API key to `.env`:
```env
REACT_APP_GOOGLE_PLACES_API_KEY=YOUR_API_KEY_HERE
```

3. Restart your development server

### 4. Test the Integration

1. Enter a location (e.g., "New York, NY")
2. Check the "Search real doctors via Google Places" option
3. Enter symptoms and click "Let AI Find & Book Doctor"
4. The app will search for real doctors via Google Places API

## How It Works

### Search Flow

1. **Geocoding**: User's location is converted to latitude/longitude
2. **Places Search**: Google Places API searches for doctors within radius
3. **Data Transformation**: API results are transformed to app format
4. **Distance Calculation**: Distance from patient to each doctor
5. **Match Scoring**: AI scores doctors based on symptoms and criteria

### Data Retrieved from Google Places

- Doctor/Clinic name
- Address
- Phone number
- Google rating
- Number of reviews
- Operating hours
- Website
- Distance from patient
- Photos

### Match Score Calculation

The AI calculates a match score (0-100) based on:
- **Specialty Match (30 points)**: Does the doctor's type match the diagnosis?
- **Base Score (50 points)**: All doctors start with 50 points
- **Rating Bonus (10 points)**: Based on Google rating (up to 10 points)
- **Distance Bonus (10 points)**: Closer doctors get more points

## API Usage Limits

### Free Tier (Google Places API)
- **Places Nearby Search**: $32 per 1,000 requests
- **Place Details**: $17 per 1,000 requests
- **Geocoding**: $5 per 1,000 requests
- **$200 free credit per month**

### Cost Estimation
- Each search uses: 1 Geocoding + 1 Nearby Search = ~$0.037
- With free credit: ~5,400 searches per month free

## Fallback Mode

If Google Places API is unavailable or disabled:
- App automatically falls back to mock data
- User can toggle "Search real doctors via Google Places" checkbox
- Mock data provides 5 sample doctors for testing

## Troubleshooting

### API Key Not Working
- Ensure all required APIs are enabled
- Check API key restrictions
- Verify `.env` file is in the root directory
- Restart development server after adding API key

### No Results Found
- Check if location is valid
- Increase search radius (default: 5 miles)
- Try different location format (zip code, city name, address)

### CORS Errors
- Google Places API requires client-side loading via script tag
- The app uses Google Maps JavaScript API (no CORS issues)
- Direct REST API calls would require a backend proxy

## Production Considerations

### Security
- Never commit `.env` file to version control
- Use environment variables in production
- Restrict API key to your domain
- Monitor API usage in Google Cloud Console

### Performance
- Implement caching to reduce API calls
- Use Place IDs for subsequent requests
- Consider server-side implementation for sensitive operations

### Scaling
- Set up billing alerts in Google Cloud Console
- Monitor monthly API usage
- Implement rate limiting if needed
- Consider Places API alternatives for high volume

## Alternative: Backend Proxy

For production, consider implementing a backend proxy:

```javascript
// Backend endpoint (Node.js/Express)
app.get('/api/search-doctors', async (req, res) => {
  const { location, specialty } = req.query;
  // Call Google Places API from server
  // Return results to frontend
});
```

Benefits:
- Hide API key from client
- Implement caching
- Add rate limiting
- Better error handling

## Resources

- [Google Places API Documentation](https://developers.google.com/maps/documentation/places/web-service)
- [Places API Pricing](https://developers.google.com/maps/billing-and-pricing/pricing)
- [Google Cloud Console](https://console.cloud.google.com/)
