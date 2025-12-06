# AI Doctor Appointment System (React Version) 🏥

A modern, intelligent React web application for booking doctor appointments with AI-powered doctor matching and automated scheduling.

## Features ✨

### 1. **Patient Symptom Input**
- Easy-to-use form for entering symptoms
- Patient information collection (name, location)
- Insurance status tracking
- Urgency level selection

### 2. **AI-Powered Doctor Matching**
- Intelligent symptom analysis
- Automatic specialty recommendation
- Multi-factor matching algorithm considering:
  - Symptom-specialty alignment
  - Insurance compatibility
  - Doctor ratings and reviews
  - Geographic proximity

### 3. **Advanced Filtering & Sorting**
- **Sort by:**
  - Best Match (AI score)
  - Distance from patient
  - Doctor rating
  - Education level
  - Price (low to high)
  - Earliest availability
  
- **Filter by:**
  - Maximum distance (5, 10, 25, or any distance)
  - Minimum rating (3+, 4+, or 4.5+ stars)

### 4. **Automated Doctor Contact**
- AI simulates calling doctors to check availability
- Real-time status updates during the process
- Finds best available appointment slots

### 5. **Smart Appointment Confirmation**
- Option 1: Patient manually confirms appointment
- Option 2: Let AI decide the best option automatically
- Automatic calendar integration (.ics file download)
- Email confirmation (simulated)

## Technology Stack 💻

- **React 18** - Component-based UI framework
- **Context API** - State management
- **CSS3** - Modern responsive design with animations
- **Vanilla JavaScript** - Utility functions and helpers

## Project Structure 📁

```
ai-doc-appointment/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   ├── SymptomInput.js
│   │   ├── DoctorResults.js
│   │   ├── Confirmation.js
│   │   └── Success.js
│   ├── context/
│   │   └── AppContext.js
│   ├── utils/
│   │   ├── mockData.js
│   │   └── helpers.js
│   ├── App.js
│   ├── App.css
│   ├── index.js
│   └── index.css
├── package.json
└── README.md
```

## Setup & Installation 🚀

### Prerequisites
- Node.js (v14 or higher)
- npm or yarn

### Installation Steps

1. Navigate to the project directory:
```bash
cd ai-doc-appointment
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

4. Open your browser and visit:
```
http://localhost:3000
```

### Building for Production

```bash
npm run build
```

This creates an optimized production build in the `build` folder.

## How It Works 🔄

1. **Patient enters symptoms** → AI analyzes and determines likely conditions
2. **AI searches database** → Finds doctors matching the condition
3. **Smart ranking** → Sorts doctors by multiple factors (distance, reviews, education, price, availability)
4. **Patient reviews options** → Can filter and sort based on preferences
5. **AI contacts doctors** → Simulates checking real-time availability
6. **Patient confirms** → Either manually or lets AI decide the best option
7. **Appointment booked** → Added to calendar with all details

## Component Overview 📦

### SymptomInput
- Collects patient information and symptoms
- Form validation
- Triggers AI analysis

### DoctorResults
- Displays matched doctors
- Filter and sort controls
- Doctor card interactions
- AI calling simulation

### Confirmation
- Shows selected appointment details
- Confirmation options
- AI decision functionality

### Success
- Confirmation display
- Calendar download
- Restart workflow

### AppContext
- Global state management
- API simulation
- Business logic

## Features Explained 📋

### AI Symptom Analysis
The system analyzes symptom text to determine:
- Likely condition
- Severity level
- Recommended medical specialties
- Urgency assessment

### Doctor Matching Algorithm
Doctors receive a match score (0-100%) based on:
- **Specialty Match (40%)** - Does their specialty align with symptoms?
- **Insurance Compatibility (20%)** - Do they accept your insurance?
- **Rating Bonus (20%)** - Higher rated doctors score better
- **Proximity Bonus (20%)** - Closer doctors receive higher scores

### Price Calculation
- **With Insurance**: Shows copay (20% of full price)
- **Without Insurance**: Shows full consultation fee

### Availability System
Each doctor has multiple available time slots. The AI:
1. Checks all available slots
2. Considers patient urgency
3. Selects the earliest appropriate time
4. Confirms availability before presenting

## Customization 🎨

### Adding More Doctors
Edit the `mockDoctorDatabase` array in `src/utils/mockData.js`:

```javascript
{
  id: 6,
  name: "Dr. Your Name",
  specialty: "Your Specialty",
  education: "MD, Your University",
  experience: 10,
  distance: 5.0,
  rating: 4.8,
  reviews: 200,
  address: "Your Address",
  phone: "(555) 000-0000",
  price: 150,
  insurance: true,
  languages: ["English"],
  availability: [
    { date: "2025-12-10", time: "10:00 AM" }
  ]
}
```

### Modifying AI Logic
The symptom analysis function in `src/utils/helpers.js` can be enhanced with:
- More condition patterns
- Advanced NLP
- Integration with real medical APIs
- Machine learning models

### Styling Customization
All colors and styles are in CSS variables at the top of `src/App.css`:

```css
:root {
  --primary-color: #4F46E5;
  --secondary-color: #10B981;
  /* Modify these for custom branding */
}
```

## Future Enhancements 🚀

- [ ] Integration with real doctor databases
- [ ] Real-time availability checking via APIs
- [ ] Payment processing
- [ ] Video consultation booking
- [ ] Multi-language support
- [ ] Mobile app version (React Native)
- [ ] Electronic health records integration
- [ ] Prescription management
- [ ] Follow-up appointment reminders
- [ ] Doctor reviews and feedback system
- [ ] SMS notifications
- [ ] Backend API integration

## Browser Support 🌐

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Available Scripts

### `npm start`
Runs the app in development mode at [http://localhost:3000](http://localhost:3000)

### `npm test`
Launches the test runner in interactive watch mode

### `npm run build`
Builds the app for production to the `build` folder

### `npm run eject`
**Note: this is a one-way operation!** Ejects from Create React App

## License 📄

This project is open source and available for educational purposes.

## Support 💬

For questions or issues, please open an issue in the repository.

---

**Made with ❤️ for better healthcare access using React**