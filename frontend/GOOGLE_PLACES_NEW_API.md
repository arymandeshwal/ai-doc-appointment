# Google Places API (New) - Fast Text Search Setup

This application uses the **Google Places API (New)** Text Search endpoint for fast, efficient doctor searches.

## Why the New API?

✅ **Much Faster**: Direct REST API calls (no Maps JavaScript library needed)
✅ **More Efficient**: Lower latency and bandwidth usage  
✅ **Better Results**: Text-based search with relevance ranking
✅ **Simpler**: No need to load and initialize Maps JS API
✅ **Modern**: Uses the latest Places API v1

## Required APIs

Enable only ONE API in Google Cloud Console:

1. **Places API (New)** - For text search

**Note**: You do NOT need Maps JavaScript API or the old Places API!

## Setup Steps

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Name: "AI Doctor Appointment"
4. Click "Create"

### 2. Enable Places API (New)

1. Go to **APIs & Services** → **Library**
2. Search for: **"Places API (New)"** 
3. Click on it and press **"Enable"**

⚠️ **Important**: Make sure it says "Places API (New)" not just "Places API"!

### 3. Create API Key

1. Go to **APIs & Services** → **Credentials**
2. Click **"+ CREATE CREDENTIALS"** → **"API key"**
3. Copy your API key
4. Click on the key name to configure restrictions

### 4. Restrict API Key (Security)

#### For Development:
**Application Restrictions**: None

**API Restrictions**:
- Select "Restrict key"
- Check only: ✅ Places API (New)

#### For Production:
**Application Restrictions**: HTTP referrers
- Add: `https://yourdomain.com/*`

**API Restrictions**:
- Select "Restrict key"  
- Check only: ✅ Places API (New)

### 5. Add to Project

Create `.env` file in project root:

```env
REACT_APP_GOOGLE_PLACES_API_KEY=your_actual_api_key_here
```

### 6. Restart Server

```bash
npm start
```

## Verify It's Working

1. Check status message on symptom input page:
   - ✅ "API Key configured" = Working!
   - ⚠️ "API Key not configured" = Add key to `.env`

2. Search for doctors and check console:
   ```
   🔎 Searching: "Dentist in New York"
   ✅ Found 10 doctors
   ```

## API Details

**Endpoint**: `https://places.googleapis.com/v1/places:searchText`

**Request**:
```javascript
POST https://places.googleapis.com/v1/places:searchText
Headers:
  Content-Type: application/json
  X-Goog-Api-Key: YOUR_KEY
  X-Goog-FieldMask: places.displayName,places.formattedAddress,...

Body:
{
  "textQuery": "Dentist in New York",
  "minRating": 4.0,
  "maxResultCount": 10
}
```

## Pricing (2024)

**Text Search**: $32 per 1,000 requests

**Free Tier**: $200 credit/month = **~6,250 searches FREE**

### Cost Optimization:
- ✅ Use `minRating` to filter server-side
- ✅ Limit `maxResultCount` (we use 10)
- ✅ Use Field Mask (only request needed fields)
- ✅ Set billing alerts

## Troubleshooting

### "API key not configured"
- Create `.env` file in project root
- Key name must be: `REACT_APP_GOOGLE_PLACES_API_KEY`
- Restart dev server after creating `.env`

### "API Error: 403"
- Enable "Places API (New)" in Cloud Console
- Check API key restrictions
- Verify key is active

### "No doctors found"
- Try broader search ("doctor" vs specific specialty)
- Verify location is valid
- Check area has medical facilities

### Still using old API?
- Delete `GoogleMapsLoader.js` (not needed)
- Update imports to use `searchDoctorsByTextSearch`
- Remove Maps JavaScript API from enabled APIs

## Performance Comparison

| Feature | Old API (Maps JS) | New API (Text Search) |
|---------|------------------|----------------------|
| Load time | ~2-3 seconds | ~500ms |
| Library size | ~100KB+ | None |
| Initialization | Required | Not needed |
| CORS issues | Possible | None |
| Modern | No | Yes |

## Resources

- [Places API (New) Docs](https://developers.google.com/maps/documentation/places/web-service/text-search)
- [Pricing](https://mapsplatform.google.com/pricing/)
- [Field Mask Guide](https://developers.google.com/maps/documentation/places/web-service/place-details#fields)

---

**Pro Tip**: This API returns results in ~500ms because it's a simple REST call with no overhead! 🚀
