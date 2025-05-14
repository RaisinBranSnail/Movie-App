"""
FILE: app.py
CONTRIBUTORS:
- Caleb Stark: Initial TMDB API integration, landing and detail page routes
- Brandon Grimaldo: Authentication system, database integration, watchlist/ratings functionality, 
                   profile management, search, movies and TV routes
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import requests
import json
from datetime import datetime

# Loads from .env - Implemented by: Caleb Stark
load_dotenv()
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_ANON_KEY")
tmdb_key = os.getenv("TMDB_API_KEY")
tmdb_base_url = os.getenv("TMDB_BASE_URL")

# Initialize Supabase client - Configured by: Caleb Stark, Extended by: Brandon Grimaldo
supabase: Client = create_client(supabase_url, supabase_key)

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a secure random key in production

# Get data from api - Implemented by: Caleb Stark
def tmdb_get(path, params=None):
    params = params or {}
    params["api_key"] = tmdb_key
    resp = requests.get(f"{tmdb_base_url}/{path}", params=params)
    resp.raise_for_status()
    return resp.json()

# Enhanced API data fetching - Implemented by: Caleb Stark
def tmdb_get_data():
    return {
        "popular_movies": tmdb_get("movie/popular", {"page": 1}),
        "top_rated_movies": tmdb_get("movie/top_rated", {"page": 1}),
        "popular_tv_shows": tmdb_get("tv/popular", {"page": 1}),
        "top_rated_tv_shows": tmdb_get("tv/top_rated", {"page": 1})
    }

# Movie genres function - Implemented by: Brandon Grimaldo
def get_movie_genres():
    return tmdb_get("genre/movie/list")["genres"]

# List of countries for the profile setup form - Implemented by: Brandon Grimaldo
COUNTRIES = [
    "United States", "Canada", "United Kingdom", "Australia", "India", 
    "Germany", "France", "Japan", "China", "Brazil", "Mexico", "Italy",
    "Spain", "Russia", "South Korea", "Netherlands", "Sweden", "Norway",
    "Denmark", "Finland", "New Zealand", "Ireland", "Belgium", "Switzerland"
]

# Landing page route - Implemented by: Caleb Stark
@app.route('/')
def landing():
    tmdb_data = tmdb_get_data()
    return render_template('landing.html', tmdb_data=tmdb_data)

# Search route - Implemented by: Brandon Grimaldo
@app.route('/search')
def search():
    query = request.args.get('query', '')
    if not query:
        return redirect(url_for('landing'))
    
    # Search for movies
    movie_results = tmdb_get("search/movie", {"query": query, "page": 1})
    
    # Search for TV shows
    tv_results = tmdb_get("search/tv", {"query": query, "page": 1})
    
    search_data = {
        "movie_results": movie_results,
        "tv_results": tv_results,
        "query": query
    }
    
    return render_template('search.html', search_data=search_data)

# Detail page route - Implemented by: Caleb Stark
@app.route('/detail/<title>')
def detail(title):
    tmdb_data = tmdb_get_data()
    return render_template('detail.html', title=title, tmdb_data=tmdb_data)

# --- Authentication Routes (All implemented by: Brandon Grimaldo) ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Authenticate user with Supabase
        try:
            response = supabase.auth.sign_in_with_password({"email": email, "password": password})
            
            # Store user session data - make sure to save the UUID exactly as returned
            session['user'] = {
                'id': response.user.id,  # This is the UUID from Supabase Auth
                'email': response.user.email,
            }
            
            # Verify session immediately
            user_id = session['user']['id']
            flash(f'Login successful! User ID: {user_id}', 'success')
            return redirect(url_for('landing'))
            
        except Exception as e:
            flash(f'Login failed: {str(e)}', 'error')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        verify_password = request.form.get('verify-password')
        
        # Validate password match
        if password != verify_password:
            flash('Passwords do not match!', 'error')
            return render_template('signup.html')
        
        # Register user with Supabase
        try:
            response = supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            
            # Store user session data for profile setup - ensure UUID is stored correctly
            session['user'] = {
                'id': response.user.id,  # This is the UUID string from auth
                'email': response.user.email,
            }
            
            # Debug info
            user_id = session['user']['id']
            flash(f'Registration successful! User ID: {user_id}. Please complete your profile.', 'success')
            return redirect(url_for('profile_setup'))
            
        except Exception as e:
            flash(f'Registration failed: {str(e)}', 'error')
    
    return render_template('signup.html')

# --- Profile Management Routes (All implemented by: Brandon Grimaldo) ---

@app.route('/profile-setup', methods=['GET', 'POST'])
def profile_setup():
    # Check if user is logged in
    if not session.get('user'):
        flash('Please log in first!', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        user_id = session['user']['id']
        
        # Get form data
        bio = request.form.get('bio')
        preferred_genres = request.form.getlist('preferred_genres')
        date_of_birth = request.form.get('date_of_birth')
        country = request.form.get('country')
        
        # Verify the user session is valid
        try:
            # Get the current auth user to confirm the session is valid
            user = supabase.auth.get_user()
            
            # Debug check if session user ID matches auth user ID
            if user.user.id != user_id:
                flash(f'Session mismatch! Session ID: {user_id}, Auth ID: {user.user.id}', 'error')
                # Update session with correct ID
                session['user']['id'] = user.user.id
                user_id = user.user.id
            
            # Convert preferred genres to string (comma-separated ids)
            preferred_genres_str = ','.join(preferred_genres) if preferred_genres else None
            
            # Create user profile in Supabase
            profile_data = {
                "user_id": user_id,  # Now this is a UUID string
                "bio": bio,
                "preferred_genres": preferred_genres_str,
                "date_of_birth": date_of_birth,
                "country": country,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # Insert the profile data
            response = supabase.table("user_profiles").insert(profile_data).execute()
            
            flash('Profile setup complete!', 'success')
            return redirect(url_for('landing'))
                
        except Exception as e:
            flash(f'Profile setup failed: {str(e)}', 'error')
    
    # For GET request, render the profile setup form
    genres = get_movie_genres()
    return render_template('profile_setup.html', genres=genres, countries=COUNTRIES)

@app.route('/profile-setup-rpc', methods=['POST'])
def profile_setup_rpc():
    """Alternative profile setup using RPC for bypass"""
    if not session.get('user'):
        flash('Please log in first!', 'error')
        return redirect(url_for('login'))
    
    user_id = session['user']['id']
    
    # Get form data
    bio = request.form.get('bio')
    preferred_genres = request.form.getlist('preferred_genres')
    date_of_birth = request.form.get('date_of_birth')
    country = request.form.get('country')
    
    # Convert preferred genres to string
    preferred_genres_str = ','.join(preferred_genres) if preferred_genres else None
    
    try:
        # Log the exact values we're about to insert
        print(f"Attempting to insert profile for user: {user_id}")
        print(f"Bio: {bio}, Genres: {preferred_genres_str}, DOB: {date_of_birth}, Country: {country}")
        
        # Call the function that bypasses RLS
        response = supabase.rpc(
            'insert_profile_bypassing_rls',
            {
                'p_user_id': user_id,
                'p_bio': bio,
                'p_preferred_genres': preferred_genres_str,
                'p_date_of_birth': date_of_birth,
                'p_country': country
            }
        ).execute()
        
        flash('Profile setup complete! (Bypass RLS method)', 'success')
        return redirect(url_for('landing'))
        
    except Exception as e:
        flash(f'Profile setup failed (RPC): {str(e)}', 'error')
        return redirect(url_for('profile_setup'))

@app.route('/profile-setup-service', methods=['POST'])
def profile_setup_service():
    """Direct profile setup using service role (admin access) to bypass RLS"""
    if not session.get('user'):
        flash('Please log in first!', 'error')
        return redirect(url_for('login'))
    
    # Hardcode service key for testing - REMOVE in production and use .env
    service_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZqaG50a3docGp5Ynlyd2htd21rIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTY5NjgyNjk2OSwiZXhwIjoyMDEyNDAyOTY5fQ.kn-pqHjfLNiW2n8NKCVz87_-ljvA61BoQ2Q8kv36XIg"
    user_id = session['user']['id']
    
    # Get form data
    bio = request.form.get('bio')
    preferred_genres = request.form.getlist('preferred_genres')
    date_of_birth = request.form.get('date_of_birth')
    country = request.form.get('country')
    
    # Convert preferred genres to string
    preferred_genres_str = ','.join(preferred_genres) if preferred_genres else None
    
    try:
        # Create a service role client that bypasses RLS
        service_client = create_client(supabase_url, service_key)
        
        profile_data = {
            "user_id": user_id,
            "bio": bio,
            "preferred_genres": preferred_genres_str,
            "date_of_birth": date_of_birth,
            "country": country,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Direct insert using service role client
        response = service_client.table("user_profiles").insert(profile_data).execute()
        
        flash('Profile setup complete! (Service role method)', 'success')
        return redirect(url_for('landing'))
        
    except Exception as e:
        flash(f'Profile setup failed (Service role): {str(e)}', 'error')
        return redirect(url_for('profile_setup'))

@app.route('/logout')
def logout():
    # Sign out from Supabase
    supabase.auth.sign_out()
    
    # Clear session
    session.clear()
    
    flash('You have been logged out.', 'info')
    return redirect(url_for('landing'))

@app.route('/watchlist')
def watchlist():
    # Check if user is logged in
    if not session.get('user'):
        flash('Please log in to view your watchlist.', 'error')
        return redirect(url_for('login'))
    
    user_id = session['user']['id']
    
    try:
        # Get user's watchlist items from database
        watchlist_query = supabase.table("watchlist").select("*").eq("user_id", user_id).execute()
        watchlist_data = watchlist_query.data
        
        # If no watchlist items, return empty list
        if not watchlist_data:
            return render_template('watchlist.html', watchlist_items=[])
        
        # Get movie details for each watchlist item
        watchlist_items = []
        for item in watchlist_data:
            # Get movie details from TMDB
            movie_data = tmdb_get(f"movie/{item['movie_id']}")
            movie_data['added_date'] = datetime.fromisoformat(item['added_date'].replace('Z', '+00:00'))
            movie_data['id'] = item['id']  # Use watchlist item id for removal
            watchlist_items.append(movie_data)
        
        # Get user profile for display
        profile_query = supabase.table("user_profiles").select("*").eq("user_id", user_id).execute()
        user_profile = profile_query.data[0] if profile_query.data else None
        
        # Get genre names if user has preferred genres
        user_genres = []
        if user_profile and user_profile.get('preferred_genres'):
            genre_ids = user_profile['preferred_genres'].split(',')
            genres = get_movie_genres()
            genre_map = {str(g['id']): g['name'] for g in genres}
            user_genres = [genre_map[gid] for gid in genre_ids if gid in genre_map]
        
        return render_template('watchlist.html', 
                              watchlist_items=watchlist_items,
                              user_profile=user_profile,
                              user_genres=user_genres)
    
    except Exception as e:
        flash(f'Error loading watchlist: {str(e)}', 'error')
        return render_template('watchlist.html', watchlist_items=[])

@app.route('/watchlist/add/<int:movie_id>', methods=['POST'])
def add_to_watchlist(movie_id):
    # Check if user is logged in
    if not session.get('user'):
        return {"success": False, "message": "Please log in to add to watchlist."}, 401
    
    user_id = session['user']['id']
    
    try:
        # Check if movie is already in watchlist
        existing = supabase.table("watchlist").select("*").eq("user_id", user_id).eq("movie_id", movie_id).execute()
        
        if existing.data:
            return {"success": False, "message": "Movie already in watchlist."}, 400
        
        # Add movie to watchlist
        watchlist_data = {
            "user_id": user_id,
            "movie_id": movie_id,
            "added_date": datetime.now().isoformat()
        }
        
        supabase.table("watchlist").insert(watchlist_data).execute()
        
        return {"success": True, "message": "Added to watchlist!"}, 200
    
    except Exception as e:
        return {"success": False, "message": str(e)}, 500

@app.route('/watchlist/remove/<int:item_id>', methods=['POST'])
def remove_from_watchlist(item_id):
    # Check if user is logged in
    if not session.get('user'):
        return {"success": False, "message": "Please log in to remove from watchlist."}, 401
    
    user_id = session['user']['id']
    
    try:
        # Remove movie from watchlist
        supabase.table("watchlist").delete().eq("id", item_id).eq("user_id", user_id).execute()
        
        return {"success": True, "message": "Removed from watchlist!"}, 200
    
    except Exception as e:
        return {"success": False, "message": str(e)}, 500

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    # Check if user is logged in
    if not session.get('user'):
        flash('Please log in to view your profile.', 'error')
        return redirect(url_for('login'))
    
    user_id = session['user']['id']
    
    if request.method == 'POST':
        # Get form data
        bio = request.form.get('bio')
        preferred_genres = request.form.getlist('preferred_genres')
        date_of_birth = request.form.get('date_of_birth')
        country = request.form.get('country')
        
        # Convert preferred genres to string (comma-separated ids)
        preferred_genres_str = ','.join(preferred_genres) if preferred_genres else None
        
        try:
            # Check if profile exists
            profile_query = supabase.table("user_profiles").select("*").eq("user_id", user_id).execute()
            
            profile_data = {
                "bio": bio,
                "preferred_genres": preferred_genres_str,
                "date_of_birth": date_of_birth,
                "country": country,
                "updated_at": datetime.now().isoformat()
            }
            
            if profile_query.data:
                # Update existing profile
                supabase.table("user_profiles").update(profile_data).eq("user_id", user_id).execute()
            else:
                # Create new profile
                profile_data["user_id"] = user_id
                profile_data["created_at"] = datetime.now().isoformat()
                supabase.table("user_profiles").insert(profile_data).execute()
            
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))
            
        except Exception as e:
            flash(f'Profile update failed: {str(e)}', 'error')
    
    # Get user profile data
    try:
        profile_query = supabase.table("user_profiles").select("*").eq("user_id", user_id).execute()
        user_profile = profile_query.data[0] if profile_query.data else None
        
        # Get genres for the form
        genres = get_movie_genres()
        
        # Get user's selected genre ids as a list
        selected_genre_ids = []
        if user_profile and user_profile.get('preferred_genres'):
            selected_genre_ids = user_profile['preferred_genres'].split(',')
        
        # Get watchlist count
        watchlist_query = supabase.table("watchlist").select("count", count="exact").eq("user_id", user_id).execute()
        watchlist_count = watchlist_query.count if hasattr(watchlist_query, 'count') else 0
        
        # Get ratings count
        ratings_query = supabase.table("ratings").select("count", count="exact").eq("user_id", user_id).execute()
        ratings_count = ratings_query.count if hasattr(ratings_query, 'count') else 0
        
        # Get watchlist items with movie details
        watchlist_items = []
        watchlist_data_query = supabase.table("watchlist").select("*").eq("user_id", user_id).execute()
        if watchlist_data_query.data:
            for item in watchlist_data_query.data:
                try:
                    # Get movie details from TMDB
                    movie_data = tmdb_get(f"movie/{item['movie_id']}")
                    movie_data['added_date'] = datetime.fromisoformat(item['added_date'].replace('Z', '+00:00')) if item.get('added_date') else datetime.now()
                    movie_data['watchlist_id'] = item['id']  # Use watchlist item id for removal
                    watchlist_items.append(movie_data)
                except Exception as e:
                    print(f"Error fetching movie {item['movie_id']}: {str(e)}")
                    continue
        
        # Get user ratings with movie details
        ratings_items = []
        ratings_data_query = supabase.table("ratings").select("*").eq("user_id", user_id).execute()
        if ratings_data_query.data:
            for item in ratings_data_query.data:
                try:
                    # Get movie details from TMDB
                    movie_data = tmdb_get(f"movie/{item['movie_id']}")
                    movie_data['rating'] = item['rating']
                    movie_data['review'] = item['review']
                    movie_data['rating_id'] = item['id']  # Use rating id for removal
                    movie_data['created_at'] = datetime.fromisoformat(item['created_at'].replace('Z', '+00:00')) if item.get('created_at') else datetime.now()
                    ratings_items.append(movie_data)
                except Exception as e:
                    print(f"Error fetching movie {item['movie_id']}: {str(e)}")
                    continue
        
        return render_template('profile.html', 
                              user_profile=user_profile,
                              genres=genres,
                              selected_genre_ids=selected_genre_ids,
                              countries=COUNTRIES,
                              watchlist_count=watchlist_count,
                              ratings_count=ratings_count,
                              watchlist_items=watchlist_items,
                              ratings_items=ratings_items)
    
    except Exception as e:
        flash(f'Error loading profile: {str(e)}', 'error')
        return render_template('profile.html', 
                              user_profile=None, 
                              genres=[], 
                              countries=COUNTRIES,
                              watchlist_count=0,
                              ratings_count=0,
                              watchlist_items=[],
                              ratings_items=[])

@app.route('/api/ratings', methods=['POST'])
def add_rating():
    # Check if user is logged in
    if not session.get('user'):
        return {"success": False, "message": "Please log in to rate movies."}, 401
    
    user_id = session['user']['id']
    
    try:
        data = request.json
        movie_id = data.get('movie_id')
        rating_value = data.get('rating')
        review = data.get('review', '')
        
        if not movie_id or not rating_value:
            return {"success": False, "message": "Missing required fields."}, 400
        
        # Check if user has already rated this movie
        existing = supabase.table("ratings").select("*").eq("user_id", user_id).eq("movie_id", movie_id).execute()
        
        rating_data = {
            "rating": rating_value,
            "review": review,
            "updated_at": datetime.now().isoformat()
        }
        
        if existing.data:
            # Update existing rating
            supabase.table("ratings").update(rating_data).eq("user_id", user_id).eq("movie_id", movie_id).execute()
            return {"success": True, "message": "Rating updated!"}, 200
        else:
            # Create new rating
            rating_data["user_id"] = user_id
            rating_data["movie_id"] = movie_id
            rating_data["created_at"] = datetime.now().isoformat()
            supabase.table("ratings").insert(rating_data).execute()
            return {"success": True, "message": "Rating submitted!"}, 201
    
    except Exception as e:
        return {"success": False, "message": str(e)}, 500

@app.route('/profile/watchlist/remove/<int:item_id>', methods=['POST'])
def profile_remove_from_watchlist(item_id):
    # Check if user is logged in
    if not session.get('user'):
        return {"success": False, "message": "Please log in to remove from watchlist."}, 401
    
    user_id = session['user']['id']
    
    try:
        # Remove movie from watchlist
        supabase.table("watchlist").delete().eq("id", item_id).eq("user_id", user_id).execute()
        
        flash('Item removed from watchlist!', 'success')
        return redirect(url_for('profile'))
    
    except Exception as e:
        flash(f'Error removing from watchlist: {str(e)}', 'error')
        return redirect(url_for('profile'))

@app.route('/profile/rating/remove/<int:item_id>', methods=['POST'])
def profile_remove_rating(item_id):
    # Check if user is logged in
    if not session.get('user'):
        return {"success": False, "message": "Please log in to remove rating."}, 401
    
    user_id = session['user']['id']
    
    try:
        # Remove rating
        supabase.table("ratings").delete().eq("id", item_id).eq("user_id", user_id).execute()
        
        flash('Rating removed!', 'success')
        return redirect(url_for('profile'))
    
    except Exception as e:
        flash(f'Error removing rating: {str(e)}', 'error')
        return redirect(url_for('profile'))

@app.route('/movies')
def movies():
    """Movies page showing popular and top rated movies"""
    try:
        # Get popular and top rated movies
        movies_data = {
            "popular_movies": tmdb_get("movie/popular", {"page": 1}),
            "top_rated_movies": tmdb_get("movie/top_rated", {"page": 1}),
            "now_playing_movies": tmdb_get("movie/now_playing", {"page": 1}),
            "upcoming_movies": tmdb_get("movie/upcoming", {"page": 1})
        }
        
        # Get genres for filter options
        genres = get_movie_genres()
        
        return render_template('movies.html', movies_data=movies_data, genres=genres)
    except Exception as e:
        flash(f'Error loading movies: {str(e)}', 'error')
        return redirect(url_for('landing'))

@app.route('/tv')
def tv_shows():
    """TV Shows page showing popular and top rated TV shows"""
    try:
        # Get popular and top rated TV shows
        tv_data = {
            "popular_tv": tmdb_get("tv/popular", {"page": 1}),
            "top_rated_tv": tmdb_get("tv/top_rated", {"page": 1}),
            "on_the_air_tv": tmdb_get("tv/on_the_air", {"page": 1}),
            "airing_today_tv": tmdb_get("tv/airing_today", {"page": 1})
        }
        
        # Get TV genres
        tv_genres = tmdb_get("genre/tv/list")["genres"]
        
        return render_template('tv_shows.html', tv_data=tv_data, genres=tv_genres)
    except Exception as e:
        flash(f'Error loading TV shows: {str(e)}', 'error')
        return redirect(url_for('landing'))

if __name__ == '__main__':
    app.run(debug=True)
