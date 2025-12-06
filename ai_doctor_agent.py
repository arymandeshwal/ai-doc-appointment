"""
AI Doctor Recommendation Agent

Simple agent that takes symptoms as input and returns recommended doctor specialties.
Uses Google Gemini AI to analyze symptoms and suggest appropriate medical specialists.

Usage:
    python ai_doctor_agent.py "I have a headache and fever"
    
    Or import and use:
    from ai_doctor_agent import DoctorRecommendationAgent
    agent = DoctorRecommendationAgent()
    result = agent.recommend("headache, fever, sore throat")
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)


class DoctorRecommendationAgent:
    """AI Agent for recommending doctors based on symptoms."""
    
    def __init__(self):
        """Initialize the agent with Gemini API."""
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in .env file")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        
    def recommend(self, symptoms: str) -> dict:
        """
        Analyze symptoms and recommend appropriate doctor specialty.
        
        Args:
            symptoms: String describing patient symptoms
            
        Returns:
            dict with:
                - specialty: Primary doctor specialty recommended
                - specialties: List of all relevant specialties
                - urgency: low/medium/high
                - reason: Explanation of recommendation
        """
        
        prompt = f"""You are a medical triage AI assistant. Analyze the following symptoms and recommend the appropriate medical specialist.

Symptoms: {symptoms}

Provide your response in the following format:
PRIMARY_SPECIALTY: [Name of the primary medical specialty needed]
ALL_SPECIALTIES: [Comma-separated list of all relevant specialties]
URGENCY: [low/medium/high]
REASON: [Brief explanation of why this specialist is recommended]

Examples of specialties: General Practitioner, Cardiologist, Dermatologist, Neurologist, Orthopedist, ENT Specialist, Gastroenterologist, Pulmonologist, Psychiatrist, Ophthalmologist, Urologist, etc.

Keep the response clear and professional."""

        try:
            response = self.model.generate_content(prompt)
            result = self._parse_response(response.text)
            result['symptoms'] = symptoms
            return result
            
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return {
                'specialty': 'General Practitioner',
                'specialties': ['General Practitioner'],
                'urgency': 'medium',
                'reason': 'Unable to analyze symptoms. Please consult a general practitioner.',
                'symptoms': symptoms,
                'error': str(e)
            }
    
    def _parse_response(self, text: str) -> dict:
        """Parse the AI response into structured data."""
        lines = text.strip().split('\n')
        result = {
            'specialty': 'General Practitioner',
            'specialties': ['General Practitioner'],
            'urgency': 'medium',
            'reason': ''
        }
        
        for line in lines:
            line = line.strip()
            if line.startswith('PRIMARY_SPECIALTY:'):
                result['specialty'] = line.split(':', 1)[1].strip()
            elif line.startswith('ALL_SPECIALTIES:'):
                specialties_str = line.split(':', 1)[1].strip()
                result['specialties'] = [s.strip() for s in specialties_str.split(',')]
            elif line.startswith('URGENCY:'):
                result['urgency'] = line.split(':', 1)[1].strip().lower()
            elif line.startswith('REASON:'):
                result['reason'] = line.split(':', 1)[1].strip()
        
        return result
    
    def format_output(self, result: dict) -> str:
        """Format the recommendation for display."""
        urgency_emoji = {
            'low': '🟢',
            'medium': '🟡',
            'high': '🔴'
        }
        
        output = f"""
╔══════════════════════════════════════════════════════════╗
║           AI DOCTOR RECOMMENDATION AGENT                 ║
╚══════════════════════════════════════════════════════════╝

📋 Symptoms: {result['symptoms']}

🏥 Recommended Specialist
   ▸ {result['specialty']}

👨‍⚕️ All Relevant Specialists:
"""
        for specialty in result['specialties']:
            output += f"   • {specialty}\n"
        
        output += f"""
{urgency_emoji.get(result['urgency'], '🟡')} Urgency Level: {result['urgency'].upper()}

💡 Reason:
   {result['reason']}

╚══════════════════════════════════════════════════════════╝
"""
        return output


def main():
    """Command-line interface for the agent."""
    if len(sys.argv) < 2:
        print("Usage: python ai_doctor_agent.py \"your symptoms here\"")
        print("Example: python ai_doctor_agent.py \"I have a headache and fever\"")
        sys.exit(1)
    
    symptoms = ' '.join(sys.argv[1:])
    
    print("\n🤖 AI Doctor Recommendation Agent")
    print("=" * 60)
    print(f"Analyzing symptoms: {symptoms}")
    print("Please wait...\n")
    
    try:
        agent = DoctorRecommendationAgent()
        result = agent.recommend(symptoms)
        print(agent.format_output(result))
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
