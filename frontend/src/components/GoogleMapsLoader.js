import { useEffect } from 'react';

const GOOGLE_MAPS_API_KEY = process.env.REACT_APP_GOOGLE_PLACES_API_KEY || '';

const GoogleMapsLoader = ({ onLoad }) => {
  useEffect(() => {
    // Check if already loaded
    if (window.google && window.google.maps) {
      if (onLoad) onLoad();
      return;
    }

    // Check if script is already being loaded
    const existingScript = document.querySelector('script[src*="maps.googleapis.com"]');
    if (existingScript) {
      existingScript.addEventListener('load', () => {
        if (onLoad) onLoad();
      });
      return;
    }

    // Load the script
    const script = document.createElement('script');
    script.src = `https://maps.googleapis.com/maps/api/js?key=${GOOGLE_MAPS_API_KEY}&libraries=places`;
    script.async = true;
    script.defer = true;
    
    script.onload = () => {
      console.log('Google Maps API loaded successfully');
      if (onLoad) onLoad();
    };

    script.onerror = () => {
      console.error('Failed to load Google Maps API');
    };

    document.head.appendChild(script);

    return () => {
      // Cleanup if needed
    };
  }, [onLoad]);

  return null;
};

export default GoogleMapsLoader;
