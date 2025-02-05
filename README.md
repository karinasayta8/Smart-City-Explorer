Smart-City-Explorer


  An interactive web application that helps users find nearby places based on their mood and location. The app integrates weather data and provides personalized recommendations for activities, places, and events. Features include real-time geolocation, activity suggestions, weather-based clothing advice, and detailed place information, including ratings, reviews, and photos.

Technologies Used
   - Frontend: Streamlit
   - Backend: Python (requests, geolocation, threading)
   - APIs: OpenWeatherMap, Google Places
   - Geolocation: Streamlit Geolocation
   - Additional Libraries: pandas, dotenv, concurrent.futures

Features
   -  Mood-Based Recommendations:   Suggests activities and places based on selected moods (e.g., adventurous, romantic, sporty).
   -   Weather-Dependent Clothing Suggestions:   Provides clothing advice based on the current weather.
   -   Nearby Places Search:   Displays places based on the user's location and selected categories.
   -   Place Details:   Shows detailed information for places, including opening hours, reviews, photos, and website links.
   -   Favorites:   Users can save their favorite places for easy access later.
   -   Real-Time Geolocation:   Uses the user's real-time location to suggest places and activities nearby.

Installation Instructions  
     Prerequisites:  
   - Python 3.8+
   - Required Python libraries (listed below)
   
     Steps to Run Locally:  
   1. Clone the repository:
      ```bash
      git clone https://github.com/yourusername/smart-city-explorer.git
      cd smart-city-explorer
      ```
   2. Install required dependencies:
      ```bash
      pip install -r requirements.txt
      ```
   3. Create a `.env` file and add your API keys:
      ```text
      OPENWEATHERMAP_API_KEY=your_openweathermap_api_key
      GOOGLE_PLACES_API_KEY=your_google_places_api_key
      ```
   4. Run the app:
      ```bash
      streamlit run app.py
      ```

   Usage Instructions  
   -   Mood Selection:   Choose your current mood to get personalized activity suggestions.
   -   Weather Updates:   View weather data for your location and receive clothing suggestions.
   -   Nearby Places:   See nearby places based on your location and selected activities.
   -   Favorites:   Save places to your favorites for future reference.
   -   View Place Details:   Explore more about a place, including reviews and operating hours.

   API Keys  
   - You will need to sign up for API keys from:
     -   OpenWeatherMap   (for weather data)
     -   Google Places API   (for location-based services)
   - Add these keys to your `.env` file for the application to function correctly.
