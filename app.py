import streamlit as st
import requests
import os
from math import radians, sin, cos, sqrt, atan2
from dotenv import load_dotenv
from streamlit_geolocation import streamlit_geolocation
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

# Load API keys
load_dotenv()
OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

# Constants
MOOD_ACTIVITIES = {
    "bored": ["park", "museum", "amusement_park", "movie_theater"],
    "excited": ["amusement_park", "stadium", "casino", "bowling_alley"],
    "hungry": ["restaurant", "cafe", "bakery", "food_court"],
    "romantic": ["spa", "restaurant", "park", "art_gallery"],
    "adventurous": ["hiking_trail", "campground", "ski_resort", "climbing_gym"],
    "cultural": ["museum", "art_gallery", "place_of_worship", "cultural_center"],
    "shopping": ["shopping_mall", "clothing_store", "jewelry_store", "market"],
    "relaxed": ["spa", "library", "book_store", "park"],
    "sporty": ["gym", "stadium", "sports_complex", "swimming_pool"],
    "nature": ["park", "zoo", "botanical_garden", "beach"],
    "historical": ["temples","museum", "monument", "historical_landmark", "archaeological_site"],
    "social": ["bar", "night_club", "bowling_alley", "karaoke_bar"],
    "family": ["aquarium", "zoo", "playground", "family_entertainment_center"]
}

POPULAR_CATEGORIES = [
    "tourist_attraction", "museum", "park", "landmark",
    "shopping_mall", "art_gallery", "zoo", "church"
]

DEFAULT_RADIUS = 5000  # meters
MAX_CONCURRENT_REQUESTS = 5
PLACE_DETAILS_CACHE = {}

# --------------------------
# Weather Functions
# --------------------------

def get_weather(city):
    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    complete_url = f"{base_url}q={city}&appid={OPENWEATHERMAP_API_KEY}&units=metric"
    
    try:
        response = requests.get(complete_url, timeout=10)
        data = response.json()
        if data["cod"] != "404":
            main = data["main"]
            weather = {
                "temp": main["temp"],
                "feels_like": main["feels_like"],
                "humidity": main["humidity"],
                "main": data["weather"][0]["main"]
            }
            return weather
        return None
    except:
        return None

def get_clothing_advice(temp):
    if temp > 25:
        return "Light clothing 🩳👕 and sunscreen"
    elif temp > 15:
        return "Light jacket 🧥 or sweater"
    else:
        return "Warm coat 🧥 and layers"

# --------------------------
# Core Functions
# --------------------------

def calculate_distance(user_lat, user_lng, place_lat, place_lng):
    R = 6371  # Earth radius in km
    lat_diff = radians(place_lat - user_lat)
    lng_diff = radians(place_lng - user_lng)
    a = (sin(lat_diff/2) ** 2 + cos(radians(user_lat)) *
         cos(radians(place_lat)) * sin(lng_diff/2) ** 2)
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

def get_place_details(place_id):
    if place_id in PLACE_DETAILS_CACHE:
        return PLACE_DETAILS_CACHE[place_id]
    
    url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=name,formatted_address,website,formatted_phone_number,opening_hours,rating,reviews,photos&key={GOOGLE_PLACES_API_KEY}"
    response = requests.get(url).json()
    
    if response.get("status") == "OK":
        result = response["result"]
        photos = [f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={p['photo_reference']}&key={GOOGLE_PLACES_API_KEY}"
                 for p in result.get('photos', [])[:3]]
        
        details = {
            "full_address": result.get("formatted_address", "N/A"),
            "website": result.get("website", "N/A"),
            "phone": result.get("formatted_phone_number", "N/A"),
            "hours": "\n".join(result.get("opening_hours", {}).get("weekday_text", [])),
            "photos": photos,
            "reviews": result.get("reviews", [])
        }
        PLACE_DETAILS_CACHE[place_id] = details
        return details
    
    return {}

@st.cache_data(ttl=3600, show_spinner=False)
def get_nearby_places(location, place_types, radius=DEFAULT_RADIUS, min_rating=4.0):
    user_lat, user_lng = map(float, location.split(','))
    places = []
    
    def process_place_type(place_type):
        params = {
            "location": location,
            "radius": radius,
            "type": place_type,
            "key": GOOGLE_PLACES_API_KEY,
        }
        try:
            response = requests.get("https://maps.googleapis.com/maps/api/place/nearbysearch/json", params=params, timeout=10)
            return response.json().get("results", [])
        except:
            return []
    
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_REQUESTS) as executor:
        results = list(executor.map(process_place_type, place_types))
    
    for place_type, results in zip(place_types, results):
        for result in results:
            place_rating = result.get("rating", 0)
            if place_rating < min_rating:
                continue
            
            place_coords = result["geometry"]["location"]
            distance = calculate_distance(user_lat, user_lng, 
                                         place_coords['lat'], place_coords['lng'])
            
            # Get first available photo
            photo_url = None
            if 'photos' in result:
                photo_ref = result['photos'][0]['photo_reference']
                photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_ref}&key={GOOGLE_PLACES_API_KEY}"
            
            places.append({
                "name": result["name"],
                "type": place_type,
                "rating": place_rating,
                "distance": distance,
                "coordinates": place_coords,
                "place_id": result["place_id"],
                "review_count": result.get("user_ratings_total", 0),
                "photo_url": photo_url  # Added photo URL
            })
    
    return sorted(places, key=lambda x: (-x['rating'], x['distance']))[:15]

def display_place_card(place, key_suffix):
    with st.container():
        # Show main image from nearby search
        if place.get('photo_url'):
            st.image(place['photo_url'], use_container_width=True, caption=place['name'])
        else:
            st.image("https://via.placeholder.com/400x200?text=No+Preview", use_column_width=True)
        
        st.subheader(place['name'])
        st.caption(f"⭐ {place['rating']} | 📍 {place['distance']:.1f} km | 📝 {place['review_count']} reviews")
        
        # Show quick feedback badges
        feedback = generate_feedback(place, st.session_state.weather_data)
        if feedback:
            st.markdown(" ".join([f"`{f}`" for f in feedback[:2]]))
        
        with st.expander("📌 Show Details", expanded=False):
            if 'details' not in place:
                with st.spinner("Loading details..."):
                    place['details'] = get_place_details(place['place_id'])
            
            details = place['details']
            
            # Show additional photos if available
            if details.get('photos'):
                cols = st.columns(3)
                for i, img in enumerate(details['photos'][:3]):
                    cols[i].image(img, use_column_width=True)
            
            # Display detailed information
            st.markdown(f"**Address:** {details['full_address']}")
            if details['website'] != "N/A":
                st.markdown(f"**Website:** [{details['website']}]({details['website']})")
            
            if st.button("🗺️ Show on Map", key=f"map_{key_suffix}"):
                map_data = pd.DataFrame({
                    "lat": [place['coordinates']['lat']],
                    "lon": [place['coordinates']['lng']]
                })
                st.map(map_data, zoom=14, use_container_width=True)
            
            if details['hours']:
                st.markdown("**Opening Hours:**")
                st.code(details['hours'])
            
            if details['reviews']:
                st.markdown("**Recent Reviews**")
                for review in details['reviews'][:2]:
                    st.markdown(f"_{review['text']}_")
                    st.caption(f"— {review['author_name']}")

@st.cache_data(ttl=3600)
def get_popular_places(location, radius=DEFAULT_RADIUS):
    user_lat, user_lng = map(float, location.split(','))
    places = []
    
    for category in POPULAR_CATEGORIES:
        params = {
            "location": location,
            "radius": radius,
            "type": category,
            "key": GOOGLE_PLACES_API_KEY,
            "rankby": "prominence"
        }
        
        try:
            response = requests.get("https://maps.googleapis.com/maps/api/place/nearbysearch/json", params=params, timeout=10)
            results = response.json().get("results", [])
        except:
            results = []
        
        for result in results:
            if result.get("user_ratings_total", 0) < 100:
                continue
            
            place_coords = result["geometry"]["location"]
            distance = calculate_distance(user_lat, user_lng,
                                         place_coords['lat'], place_coords['lng'])
            
            # Get first available photo
            photo_url = None
            if 'photos' in result and result['photos']:
                photo_ref = result['photos'][0]['photo_reference']
                photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_ref}&key={GOOGLE_PLACES_API_KEY}"
            
            places.append({
                "name": result["name"],
                "rating": result.get("rating", 0),
                "distance": distance,
                "review_count": result.get("user_ratings_total", 0),
                "coordinates": place_coords,
                "place_id": result["place_id"],
                "type": category,
                "photo_url": photo_url  # Added photo URL
            })
    
    return sorted(places, key=lambda x: (-x['rating'], -x['review_count']))[:10]

def display_popular_place(place, key_suffix):
    """Special display function for popular places with image outside card"""
    # Display image outside the container
    if place.get('photo_url'):
        st.image(place['photo_url'], use_container_width=True, caption=place['name'])
    else:
        st.image("https://via.placeholder.com/400x200?text=No+Preview", use_column_width=True)
    
    # Card container
    with st.container():
        st.subheader(place['name'])
        st.caption(f"⭐ {place['rating']} | 📍 {place['distance']:.1f} km | 📝 {place['review_count']} reviews")
        
        feedback = generate_feedback(place, st.session_state.weather_data)
        if feedback:
            st.markdown(" ".join([f"`{f}`" for f in feedback[:2]]))
        
        with st.expander("📌 Show Details", expanded=False):
            if 'details' not in place:
                with st.spinner("Loading details..."):
                    place['details'] = get_place_details(place['place_id'])
            
            details = place['details']
            
            if details.get('photos'):
                cols = st.columns(3)
                for i, img in enumerate(details['photos'][:3]):
                    cols[i].image(img, use_column_width=True)
            
            st.markdown(f"**Address:** {details['full_address']}")
            if details['website'] != "N/A":
                st.markdown(f"**Website:** [{details['website']}]({details['website']})")
            
            if st.button("🗺️ Show on Map", key=f"map_pop_{key_suffix}"):
                map_data = pd.DataFrame({
                    "lat": [place['coordinates']['lat']],
                    "lon": [place['coordinates']['lng']]
                })
                st.map(map_data, zoom=14, use_container_width=True)
            
            if details['hours']:
                st.markdown("**Opening Hours:**")
                st.code(details['hours'])
            
            if details['reviews']:
                st.markdown("**Recent Reviews**")
                for review in details['reviews'][:2]:
                    st.markdown(f"_{review['text']}_")
                    st.caption(f"— {review['author_name']}")

        if st.button("❤️ Save to Favorites", key=f"fav_pop_{key_suffix}"):
            st.session_state.favorites.append(place)
            st.success("Added to favorites!")

# --------------------------
# UI Components
# --------------------------


def mood_selector():
    st.subheader("🎭 Select Your Mood")
    selected_mood = st.session_state.get("selected_mood", "")
    
    if selected_mood:
        if st.button("❌ Clear Mood Selection"):
            st.session_state.selected_mood = ""
            st.rerun()
    
    moods = list(MOOD_ACTIVITIES.keys())
    cols = st.columns(4)
    
    for i, mood in enumerate(moods):
        with cols[i%4]:
            btn_type = "primary" if mood == selected_mood else "secondary"
            label = f"⭐ {mood.upper()}" if mood == selected_mood else mood.upper()
            
            if st.button(label, key=f"mood_{i}", help=f"Find {mood} activities", type=btn_type):
                st.session_state.selected_mood = mood
                st.rerun()
    
    return selected_mood

def generate_feedback(place, weather_data):
    feedback = []
    
    
    distance = place.get('distance', 0)
    if distance < 1.0:
        feedback.append("🚶 Conveniently located nearby")
    elif distance < 3.0:
        feedback.append("📍 Just a short trip away")
    
    if weather_data:
        weather_condition = weather_data.get('main', '').lower()
        temp = weather_data.get('temp', 20)
        place_type = place.get('type', '')
        
        if place_type in ['park', 'beach', 'botanical_garden', 'nature']:
            if 'rain' not in weather_condition and temp > 15:
                feedback.append("🌤️ Perfect for enjoying the nice weather")
            elif 'rain' in weather_condition:
                feedback.append("☔ Beautiful even in rain - bring an umbrella!")
        elif place_type in ['museum', 'art_gallery', 'cultural_center']:
            if 'rain' in weather_condition or temp < 15:
                feedback.append("🏛️ Great indoor activity for today's weather")
            else:
                feedback.append("❄️ Cool escape from the heat")
    
    type_feedback = {
        'spa': "💆 Relaxing ambience perfect for unwinding",
        'amusement_park': "🎢 Exciting rides and fun atmosphere",
        'restaurant': "🍽️ Known for delicious cuisine and great service",
        'museum': "🎨 Rich in culture and history",
        'park': "🌳 Peaceful natural surroundings",
        'shopping_mall': "🛍️ Great variety of stores and amenities",
        'tourist_attraction': "📸 Must-see spot in the area",
        'landmark': "🏰 Iconic historical location",
        'art_gallery': "🖼️ Explore beautiful artworks",
        'zoo': "🐅 Family-friendly wildlife experience",
        'church': "⛪ Architectural beauty and serenity",
        'beach': "🏖️ Sandy shores and ocean views",
        'hiking_trail': "🥾 Adventure with scenic trails",
        'library': "📚 Quiet space for peaceful time"
    }
    place_type = place.get('type', '')
    feedback.append(type_feedback.get(place_type, "🌟 Great choice for your current mood"))
    
    return feedback[:3]

# --------------------------
# Main App
# --------------------------

def main():
    
    st.set_page_config(page_title="Smart City Explorer", page_icon="🌇", layout="wide")
    
    if 'selected_mood' not in st.session_state:
        st.session_state.selected_mood = ""
    if 'favorites' not in st.session_state:
        st.session_state.favorites = []
    if 'weather_data' not in st.session_state:
        st.session_state.weather_data = None

    st.header("🌆 Smart City Explorer")
    
    # Location Section
    current_loc = None
    detected_city = "your area"
    
    with st.expander("📍 SET YOUR LOCATION", expanded=True):
        loc_col1, loc_col2 = st.columns([2,1])
        with loc_col1:
            location = streamlit_geolocation()
            if location and location.get("latitude"):
                current_loc = f"{location['latitude']},{location['longitude']}"
                st.success("📍 Location detected automatically!")
        
        with loc_col2:
            city = st.text_input("Or Enter City Name")
            if city:
                try:
                    geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={city}&key={GOOGLE_PLACES_API_KEY}"
                    response = requests.get(geocode_url, timeout=10)
                    if response.json().get("status") == "OK":
                        location = response.json()["results"][0]["geometry"]["location"]
                        current_loc = f"{location['lat']},{location['lng']}"
                        detected_city = city
                except:
                    pass

    # Weather Section
    if current_loc:
        try:
            weather_data = get_weather(detected_city) if detected_city else None
            if weather_data:
                cols = st.columns(4)
                cols[0].subheader(f"⛅ {detected_city.capitalize()} Weather")
                cols[0].markdown(f"**Temp:** {weather_data['temp']}°C | **Feels Like:** {weather_data['feels_like']}°C")
                cols[1].markdown(f"**Humidity:** {weather_data['humidity']}% | **Condition:** {weather_data['main']}")
                cols[2].markdown(f"**Clothing:** {get_clothing_advice(weather_data['temp'])}")
                st.session_state.weather_data = weather_data
        except:
            pass

    # Mood Selection
    selected_mood = mood_selector()

    # Sidebar Controls
    with st.sidebar:
        st.subheader("🔍 Search Filters")
        min_rating = st.slider("Minimum Rating", 1.0, 5.0, 4.0, 0.5)
        search_radius = st.select_slider("Search Radius (km)", options=[1, 2, 5, 10, 20], value=5)
        st.session_state.min_rating = min_rating
        st.session_state.search_radius = search_radius
        
        st.markdown("---")
        st.subheader("❤️ Favorites")
        if st.session_state.favorites:
            for i, fav in enumerate(st.session_state.favorites):
                st.markdown(f"{i+1}. {fav['name']}")
        else:
            st.markdown("No favorites saved yet")

    # Main Content
    if current_loc:
        if selected_mood:
            with st.spinner("🔍 Finding best matches..."):
                places = get_nearby_places(
                    current_loc,
                    MOOD_ACTIVITIES[selected_mood],
                    radius=st.session_state.search_radius*1000,
                    min_rating=st.session_state.min_rating
                )
                
                if places:
                    st.header(f"🏆 Top {selected_mood.capitalize()} Recommendations")
                    cols = st.columns(3)
                    for i, place in enumerate(places):
                        with cols[i%3]:
                            display_place_card(place, f"mood_{i}")
                            if st.button("❤️ Save to Favorites", key=f"fav_{i}"):
                                st.session_state.favorites.append(place)
                                st.success("Added to favorites!")

        # Popular Places
        st.header("🌟 Must-Visit Popular Places")
        with st.spinner("Finding top attractions..."):
            places = get_popular_places(current_loc)
            if places:
                cols = st.columns(3)
                for i, place in enumerate(places):
                    with cols[i%3]:
                        display_popular_place(place, f"popular_{i}")
                        if st.button("❤️", key=f"heart_{i}"):
                            st.session_state.favorites.append(place)
                            st.success("Added to favorites!")

if __name__ == "__main__":
    main()