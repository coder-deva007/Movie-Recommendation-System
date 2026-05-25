# 🎬 Hybrid Movie Recommendation Engine

A full-stack, end-to-end movie recommendation system that leverages deep learning and natural language processing to deliver personalized movie suggestions. 

This project implements a **Hybrid Recommendation Engine**, combining **Neural Collaborative Filtering (NeuMF)** for personalized user recommendations and **Content-Based Filtering (Word2Vec + Cosine Similarity)** for title-to-title similarities. It features a fast, asynchronous FastAPI backend and a responsive Vanilla JS/HTML frontend, enriched with real-time poster and metadata fetching via the TMDB API.

---

## ✨ Features

* **Hybrid AI Recommendations:** Combines deep learning (user tastes) with NLP (movie content) for highly accurate suggestions.
* **Intelligent Cold Start Handling:** Automatically hides personalized recommendations for brand-new users, serving trending TMDB content until they rate their first movie.
* **"Graceful Degradation" Fallbacks:** If a user searches for a brand new movie that isn't in the ML model's local vocabulary, the backend seamlessly falls back to the live TMDB API to fetch similar movies.
* **Asynchronous API Enrichment:** Utilizes `asyncio.gather` to fetch multiple movie posters and metadata from TMDB in parallel, resulting in lightning-fast page loads.
* **Proxy-Enabled TMDB Fetching:** Uses a Google Apps Script proxy to bypass ISP blocking for TMDB image loading.
* **Safe-Write Data Pipeline:** Separates the model's read-only dataset (`ratings_old.csv`) from the active user-input database (`ratings.csv`) to prevent `IndexError` crashes during real-time interaction while safely collecting data for nightly batch retraining.

---

## 🧠 Machine Learning Architecture

### 1. Collaborative Filtering (NeuMF)
* **What it does:** Recommends movies based on a user's past viewing history by finding hidden patterns between users with similar tastes.
* **How it works:** Implements **Neural Matrix Factorization (NeuMF)** using TensorFlow/Keras. It combines Generalized Matrix Factorization (GMF) to capture linear interactions and a Multi-Layer Perceptron (MLP) to capture complex, non-linear user-item interactions. 
* **Pipeline:** The model outputs prediction scores for unseen movies, sorts them, and returns the top *K* recommendations.

### 2. Content-Based Filtering (Word2Vec)
* **What it does:** Recommends movies similar to a specific title (e.g., "If you liked *Inception*, you might like *Interstellar*").
* **How it works:** Movie metadata (genres, tags, overviews) was processed and vectorized using **Word2Vec** to capture semantic relationships between words. These embeddings are stored locally as NumPy arrays (`movie_vectors.npy`). 
* **Pipeline:** When a user clicks a movie, the system calculates the **Cosine Similarity** between that movie's vector and all other movies in the database, returning the closest mathematical matches.

---

## 🛠️ Tech Stack

* **Frontend:** HTML5, CSS3, Vanilla JavaScript (Fetch API)  
* **Backend:** Python, FastAPI, Uvicorn, Asyncio  
* **Machine Learning:** TensorFlow / Keras (NeuMF), Scikit-Learn, Gensim (Word2Vec), NumPy, Pandas  
* **External APIs:** TMDB API (The Movie Database)  

---

## 📂 Project Structure

```text
movie-recommendation-system/
│
├── backend/
│   ├── main.py                  # FastAPI server, routing, and auth logic
│   ├── ml_services.py           # Handles NeuMF predictions, Cosine Similarity, and rating saving
│   ├── tmdb_service.py          # Async TMDB API fetching and proxy handling
│   ├── data/
│   │   ├── users.csv            # User authentication database
│   │   ├── ratings.csv          # Active write-only database for new user clicks
│   │   ├── ratings_old.csv      # Static read-only dataset for NeuMF inference
│   │   └── movies.csv           # TMDB to internal ID mapping
│   └── models/
│       ├── NeuMF/               # Keras .pkl models and user2idx/movie2idx dictionaries
│       └── cbf/                 # movie_vectors.npy and movie_index.parquet
|       |__ Notebook files      # Jupyter notebooks used for data prep and model training
│
├── frontend/
│   ├── index.html               # Home page (Trending & Collaborative Recs)
│   ├── title.html               # Movie Details page (Content-Based Recs)
│   ├── login.html               # Authentication page
│   ├── style.css                # Cinematic, dark-mode UI styling
│   └── app.js                   # Client-side logic and API fetching
|                 
└── README.md
```
# 🚀 Installation & Setup

## 📌 Prerequisites

Before starting, make sure you have:

- Python 3.9+
- A TMDB API Key (Get one free from https://www.themoviedb.org)

---

# 1️⃣ Clone the Repository

```bash
git clone https://github.com/yourusername/movie-recommendation-system.git
cd movie-recommendation-system
```

---

# 2️⃣ Set Up the Backend (Python)

Create a virtual environment and install all required dependencies.

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment

# Linux / Mac
source venv/bin/activate

# Windows
venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn pandas numpy scikit-learn tensorflow requests pyarrow fastparquet
```

---

# 3️⃣ Add Your TMDB API Key

Open:

```bash
backend/tmdb_service.py
```

Replace the placeholder API key with your own API key.

OR set it as an environment variable:

```bash
# Linux / Mac
export TMDB_API_KEY="your_api_key_here"

# Windows (CMD)
set TMDB_API_KEY=your_api_key_here

# Windows (PowerShell)
$env:TMDB_API_KEY="your_api_key_here"
```

---

# 4️⃣ Run the FastAPI Server

Start the backend server using Uvicorn:

```bash
uvicorn main:app --reload
```

The API will be available at:

```text
http://localhost:8000
```

Interactive API Documentation:

```text
http://localhost:8000/docs
```

---

# 5️⃣ Launch the Frontend

The frontend uses vanilla HTML, CSS, and JavaScript, so no Node.js server is required.

Simply open:

```text
frontend/login.html
```

in your web browser.

You can also use:

- VS Code Live Server Extension
- Python Simple HTTP Server
- Any static file server

---

# 💡 How to Test the Application

## ✅ Test NeuMF (Collaborative Filtering)

Log in using one of the legacy dataset accounts to instantly view personalized recommendations.

```text
Username: 15
Password: password123
```

---

## ✅ Test the Cold Start Problem

1. Create a brand new account using the Signup page.
2. Notice that the **"Recommended for You"** section is initially hidden.
3. This simulates how recommendation systems behave for new users with no interaction history.

---

## ✅ Test Content-Based Filtering

1. Click on any movie card.
2. Scroll down to the **Similar Movies** section.
3. Recommendations are generated locally using:
   - Word2Vec embeddings
   - Cosine similarity
   - Movie metadata features

---

## ✅ Test Dynamic Data Collection

1. Rate any movie.
2. Open:

```text
backend/data/ratings.csv
```

3. You will see the new user interaction safely appended to the dataset.

This data can later be used for:
- Incremental training
- Model retraining
- Improving collaborative filtering accuracy

---