# import os
# import requests
# import asyncio

# TMDB_API_KEY = os.getenv("TMDB_API_KEY", "7bb6a574cbd826050686b6546698de2d")
# BASE_URL = "https://api.themoviedb.org/3"

# async def fetch_tmdb(endpoint: str, params: dict = None):
#     if params is None:
#         params = {}
#     params["api_key"] = TMDB_API_KEY
    
#     url = f"{BASE_URL}{endpoint}"
    
#     try:
#         # The blocking requests call
#         def _do_request():
#             resp = requests.get(url, params=params, timeout=10)
#             resp.raise_for_status()
#             return resp.json()
            
#         # Python 3.8 compatible background thread execution
#         loop = asyncio.get_running_loop()
#         return await loop.run_in_executor(None, _do_request)
        
#     except Exception as e:
#         print(f"⚠️ Fetch failed ({e}). Serving fallback data.")
        
#         # Minimal fallback
#         mock_movies = [
#             {"id": 27205, "title": "Inception", "poster_path": "", "overview": "Dream heist.", "release_date": "2010"},
#             {"id": 157336, "title": "Interstellar", "poster_path": "", "overview": "Space travel.", "release_date": "2014"},
#             {"id": 155, "title": "The Dark Knight", "poster_path": "", "overview": "Batman.", "release_date": "2008"}
#         ]
        
#         endpoint_parts = endpoint.strip("/").split("/")
#         if len(endpoint_parts) >= 2 and endpoint_parts[1].isdigit():
#             movie_id = int(endpoint_parts[1])
#             return {"id": movie_id, "title": f"Mock Movie {movie_id}", "poster_path": "", "overview": "Details unavailable."}
            
#         return {"results": mock_movies}

# # ==========================================
# # TRIMMED TO 18 RESULTS
# # ==========================================

# async def get_trending_movies():
#     data = await fetch_tmdb("/trending/movie/week")
#     if "results" in data:
#         data["results"] = data["results"][:18]
#     return data

# async def get_popular_movies():
#     data = await fetch_tmdb("/movie/popular")
#     if "results" in data:
#         data["results"] = data["results"][:18]
#     return data

# async def get_upcoming_movies():
#     data = await fetch_tmdb("/movie/upcoming")
#     if "results" in data:
#         data["results"] = data["results"][:18]  # Slices Upcoming to 18
#     return data

# async def get_top_rated_movies():
#     data = await fetch_tmdb("/movie/top_rated")
#     if "results" in data:
#         data["results"] = data["results"][:18]  # Slices Top Rated to 18
#     return data

# async def search_movies(query: str):
#     data = await fetch_tmdb("/search/movie", {"query": query})
#     if "results" in data:
#         data["results"] = data["results"][:18]
#     return data

import os
import requests
import asyncio
import urllib.parse

TMDB_API_KEY = os.getenv("TMDB_API_KEY", "7bb6a574cbd826050686b6546698de2d")
BASE_URL = "https://api.themoviedb.org/3"

# Paste your Google Apps Script Web App URL here:
GOOGLE_PROXY_URL = "https://script.google.com/macros/s/AKfycbxEtAvc_k0LHfME0u46o7EcaogtzTRiXpLWbYYUA7PMQiouQDNsYM2321OrUWLXIqzm/exec"

async def fetch_tmdb(endpoint: str, params: dict = None):
    if params is None:
        params = {}
    params["api_key"] = TMDB_API_KEY
    
    # 1. Build the actual TMDB URL
    query_string = urllib.parse.urlencode(params)
    target_tmdb_url = f"{BASE_URL}{endpoint}?{query_string}"
    
    # 2. Safely encode the TMDB URL to pass it to Google
    encoded_target_url = urllib.parse.quote(target_tmdb_url, safe="")
    google_fetch_url = f"{GOOGLE_PROXY_URL}?url={encoded_target_url}"
    
    try:
        def _do_request():
            # Python only talks to Google, completely bypassing the ISP block
            resp = requests.get(google_fetch_url, timeout=15)
            resp.raise_for_status()
            return resp.json()
            
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _do_request)
        
    except Exception as e:
        print(f"⚠️ Google Proxy failed ({e}). Serving fallback data.")
        
        # Minimal fallback
        mock_movies = [
            {"id": 27205, "title": "Inception", "poster_path": "", "overview": "Dream heist.", "release_date": "2010"},
            {"id": 157336, "title": "Interstellar", "poster_path": "", "overview": "Space travel.", "release_date": "2014"}
        ]
        
        endpoint_parts = endpoint.strip("/").split("/")
        if len(endpoint_parts) >= 2 and endpoint_parts[1].isdigit():
            movie_id = int(endpoint_parts[1])
            return {"id": movie_id, "title": f"Mock Movie {movie_id}", "poster_path": "", "overview": "Details unavailable."}
            
        return {"results": mock_movies}

# ==========================================
# TRIMMED TO 18 RESULTS
# ==========================================

async def get_trending_movies():
    data = await fetch_tmdb("/trending/movie/week")
    if "results" in data:
        data["results"] = data["results"][:18]
    return data

async def get_popular_movies():
    data = await fetch_tmdb("/movie/popular")
    if "results" in data:
        data["results"] = data["results"][:18]
    return data

async def get_upcoming_movies():
    data = await fetch_tmdb("/movie/upcoming")
    if "results" in data:
        data["results"] = data["results"][:18]  # Slices Upcoming to 18
    return data

async def get_top_rated_movies():
    data = await fetch_tmdb("/movie/top_rated")
    if "results" in data:
        data["results"] = data["results"][:18]  # Slices Top Rated to 18
    return data

async def search_movies(query: str):
    data = await fetch_tmdb("/search/movie", {"query": query})
    if "results" in data:
        data["results"] = data["results"][:18]
    return data