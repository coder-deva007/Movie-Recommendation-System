import os
import time
import pickle
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Suppress TF warnings if needed
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# ==========================================
# 1. LOAD MODELS & VECTORS
# ==========================================
try:
    with open("models/NeuMF/mplgmf_model.pkl", "rb") as f:
        neumf_model = pickle.load(f)
    print("✅ NeuMF model loaded.")
except Exception as e:
    print(f"⚠️ NeuMF model missing or failed to load: {e}")
    neumf_model = None

try:
    movie_vectors = np.load("models/cbf/movie_vectors.npy")
    movie_index = pd.read_parquet("models/cbf/movie_index.parquet")
    print("✅ CBF vectors loaded.")
except Exception as e:
    print(f"⚠️ CBF models missing or failed to load: {e}")
    movie_vectors, movie_index = None, None

# ==========================================
# 2. LOAD MAPPINGS (NeuMF Dictionaries & TMDB Links)
# ==========================================
try:
    # Load the dictionaries you used during training to map IDs to matrix indices
    with open("models/NeuMF/user2idx.pkl", "rb") as f:
        user2idx = pickle.load(f)
    with open("models/NeuMF/movie2idx.pkl", "rb") as f:
        movie2idx = pickle.load(f)
    print("✅ NeuMF index mappings loaded.")
except Exception as e:
    print(f"⚠️ user2idx/movie2idx missing. NeuMF will fail: {e}")
    user2idx, movie2idx = {}, {}

try:
    # Load your dataset that links internal movieId to tmdbId 
    links_df = pd.read_csv("data/movies.csv") 
    links_df = links_df.dropna(subset=['tmdbId'])
    
    # Create fast O(1) lookup dictionaries
    movie2tmdb = dict(zip(links_df['movieId'], links_df['tmdbId'].astype(int)))
    tmdb2movie = dict(zip(links_df['tmdbId'].astype(int), links_df['movieId']))
    print("✅ ID Translation maps loaded.")
except Exception as e:
    print(f"⚠️ ID Mappings failed to load: {e}")
    movie2tmdb, tmdb2movie = {}, {}


# ==========================================
# 3. RECOMMENDATION FUNCTIONS
# ==========================================

def get_content_based_recommendations(tmdb_id: int, top_k: int = 18):
    """Returns similar movies using optimized vector similarity."""
    if movie_vectors is None or movie_index is None:
        return []
    
    movie_id = tmdb2movie.get(tmdb_id)
    if not movie_id:
        print(f"⚠️ TMDB ID {tmdb_id} not found in our local dataset.")
        return []

    id_col = next((col for col in ['movie_id', 'movieId', 'id'] if col in movie_index.columns), 'movieId')
    
    if movie_id not in movie_index[id_col].values:
        return []
        
    idx = movie_index.index[movie_index[id_col] == movie_id][0]
    query_vector = movie_vectors[idx].reshape(1, -1)
    similarities = cosine_similarity(query_vector, movie_vectors)[0]
    
    top_indices = similarities.argsort()[-(top_k + 1):][::-1]
    top_indices = [i for i in top_indices if i != idx][:top_k]
    
    recommended_internal_ids = movie_index.iloc[top_indices][id_col].tolist()
    
    results = []
    for internal_id in recommended_internal_ids:
        rec_tmdb_id = movie2tmdb.get(internal_id)
        if rec_tmdb_id:
            results.append({"id": rec_tmdb_id})
            
    return results

def get_collaborative_recommendations(user_id: int, raw_ratings_data, top_k: int = 18):
    """Returns personalized recommendations using NeuMF."""
    if not neumf_model or not user2idx or not movie2idx:
        return []

    if user_id not in user2idx:
        print(f"⚠️ User {user_id} is new (Cold Start). CF skipping.")
        return []

    ratings_df = pd.DataFrame(raw_ratings_data)
    if not ratings_df.empty and 'userId' in ratings_df.columns:
        watched = set(ratings_df[ratings_df['userId'] == user_id]['movieId'].values)
    else:
        watched = set()

    unseen = [m for m in movie2idx if m not in watched]
    if not unseen:
        return []

    user_idx_arr  = np.array([user2idx[user_id]] * len(unseen))
    movie_idx_arr = np.array([movie2idx[m] for m in unseen])

    scores = neumf_model.predict({
        'user': user_idx_arr,
        'movie': movie_idx_arr
    }, verbose=0).flatten()

    top_idx = np.argsort(scores)[::-1][:top_k]
    recommended_internal_ids = [unseen[i] for i in top_idx]

    results = []
    for internal_id in recommended_internal_ids:
        rec_tmdb_id = movie2tmdb.get(internal_id)
        if rec_tmdb_id:
            results.append({"id": rec_tmdb_id})

    return results

# ==========================================
# 4. DATA PIPELINE FUNCTIONS
# ==========================================

def save_user_rating(user_id: int, tmdb_id: int, rating: float, title: str):
    """Appends the new rating strictly to ratings.csv"""
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # STRICTLY Save to ratings.csv
    file_path = os.path.join(CURRENT_DIR, "data", "ratings.csv")
    
    movie_id = tmdb2movie.get(tmdb_id)
    if not movie_id:
        print(f"⚠️ Cannot save rating. TMDB ID {tmdb_id} has no internal mapping.")
        return False

    new_data = {
        "userId": [user_id],
        "movieId": [movie_id],
        "title": [title],
        "tmdbId": [tmdb_id],
        "rating": [rating],
        "timestamp": [int(time.time())]
    }
    new_row = pd.DataFrame(new_data)
    
    file_exists = os.path.exists(file_path)
    
    if file_exists:
        existing_columns = pd.read_csv(file_path, nrows=0).columns
        for col in existing_columns:
            if col not in new_row.columns:
                new_row[col] = None
        new_row = new_row[existing_columns]

    new_row.to_csv(file_path, mode='a', header=not file_exists, index=False)
    print(f"✅ Saved to: {file_path}")
    return True