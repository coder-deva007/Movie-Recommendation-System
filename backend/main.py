from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import os
import asyncio

import tmdb_service
import ml_services

class AuthInput(BaseModel):
    username: str
    password: str

app = FastAPI(title="Hybrid Movie Recommender API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class RatingInput(BaseModel):
    user_id: int
    movie_id: int
    rating: float
    title: str

# ==========================================
# 1. DATABASE INITIALIZATION
# ==========================================
@app.on_event("startup")
def init_users_db():
    users_file = "data/users.csv"
    os.makedirs("data", exist_ok=True)
    
    if not os.path.exists(users_file):
        print("🔧 Initializing users.csv with 610 legacy dataset users...")
        legacy_users = []
        for i in range(1, 611):
            legacy_users.append({
                "user_id": i,
                "username": str(i),
                "password": "password123"
            })
        pd.DataFrame(legacy_users).to_csv(users_file, index=False)
        print("✅ users.csv created successfully.")

# ==========================================
# 2. HELPER: ID Enrichment
# ==========================================
async def enrich_recommendations(raw_recs):
    tasks = []
    for rec in raw_recs:
        if "id" in rec:
            tasks.append(tmdb_service.fetch_tmdb(f"/movie/{rec['id']}"))
            
    if not tasks:
        return []

    results = await asyncio.gather(*tasks, return_exceptions=True)
    enriched = [res for res in results if isinstance(res, dict) and "title" in res]
    return enriched

# ==========================================
# 3. STRICT AUTHENTICATION ENDPOINTS
# ==========================================
@app.post("/api/signup")
async def signup(data: AuthInput):
    users_file = "data/users.csv"
    if not os.path.exists(users_file):
        pd.DataFrame(columns=["user_id", "username", "password"]).to_csv(users_file, index=False)
        
    users_df = pd.read_csv(users_file)
    if data.username in users_df['username'].astype(str).values:
        raise HTTPException(status_code=400, detail="Username already exists")
        
    max_new_id = users_df['user_id'].max() if not users_df.empty else 0
    new_user_id = max_new_id + 1
    
    new_user = pd.DataFrame({
        "user_id": [new_user_id], 
        "username": [data.username], 
        "password": [data.password]
    })
    new_user.to_csv(users_file, mode='a', header=False, index=False)
    return {"user_id": int(new_user_id), "username": data.username}

@app.post("/api/login")
async def login(data: AuthInput):
    users_file = "data/users.csv"
    if not os.path.exists(users_file):
        raise HTTPException(status_code=500, detail="User database not found. Restart server.")
        
    users_df = pd.read_csv(users_file)
    match = users_df[
        ((users_df['username'].astype(str) == data.username) | 
         (users_df['user_id'].astype(str) == data.username)) & 
        (users_df['password'].astype(str) == data.password)
    ]
    
    if not match.empty:
        user_record = match.iloc[0]
        return {"user_id": int(user_record['user_id']), "username": str(user_record['username'])}
        
    raise HTTPException(status_code=401, detail="Invalid User ID/Username or password")

# ==========================================
# 4. PAGE ENDPOINTS
# ==========================================
@app.get("/api/home")
async def get_home_page(user_id: int = 1):
    trending, popular, top_rated, upcoming = await asyncio.gather(
        tmdb_service.get_trending_movies(),
        tmdb_service.get_popular_movies(),
        tmdb_service.get_upcoming_movies(),
        tmdb_service.get_top_rated_movies(),
        return_exceptions=True
    )
    
    trending = trending if isinstance(trending, dict) else {}
    popular = popular if isinstance(popular, dict) else {}
    top_rated = top_rated if isinstance(top_rated, dict) else {}
    upcoming = upcoming if isinstance(upcoming, dict) else {}
    
    personalized = []
    
    # STRICTLY read from ratings_old.csv
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    ratings_path = os.path.join(CURRENT_DIR, "data", "ratings_old.csv")
    
    if os.path.exists(ratings_path):
        print('✅ Found ratings_old.csv')
        current_ratings = pd.read_csv(ratings_path)
        
        # Check if the user is in the OLD dataset
        user_has_history = user_id in current_ratings['userId'].values
        
        if user_has_history:
            print('✅ User has watch history in NeuMF dataset!')
            raw_personalized = ml_services.get_collaborative_recommendations(user_id, current_ratings, 18)
            personalized = await enrich_recommendations(raw_personalized)
        else:
            print('⚠️ User not in NeuMF dataset. Sending empty list.')
            personalized = [] 
    else:
        print(f"❌ Could not find file at: {ratings_path}")
        personalized = []
    
    return {
        "trending": trending.get("results", []),
        "popular": popular.get("results", []),
        "top_rated": top_rated.get("results", []),
        "upcoming": upcoming.get("results", []),
        "personalized": personalized
    }

@app.get("/api/search")
async def search(q: str):
    results = await tmdb_service.search_movies(q)
    return results.get("results", [])

@app.get("/api/movie/{movie_id}")
async def get_movie_details(movie_id: int, user_id: int = 1):
    details = await tmdb_service.fetch_tmdb(f"/movie/{movie_id}")
    raw_similar = ml_services.get_content_based_recommendations(movie_id, 16)
    
    if raw_similar:
        similar_content = await enrich_recommendations(raw_similar)
    else:
        print(f"🔄 Model missed TMDB ID {movie_id}. Falling back to TMDB API.")
        tmdb_fallback = await tmdb_service.fetch_tmdb(f"/movie/{movie_id}/recommendations")
        similar_content = tmdb_fallback.get("results", [])[:16]
    
    return {
        "details": details,
        "similar_content": similar_content
    }

@app.post("/api/rate")
async def rate_movie(rating: RatingInput):
    success = ml_services.save_user_rating(
        rating.user_id, 
        rating.movie_id, 
        rating.rating, 
        rating.title
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save rating")
    return {"status": "success"}