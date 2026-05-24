const API_BASE = "http://localhost:8000/api";
const TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500";

// ==========================================
// 1. AUTHENTICATION LOGIC
// ==========================================

document.addEventListener("DOMContentLoaded", () => {
    const isLoginPage = window.location.pathname.endsWith("login.html");
    const userId = localStorage.getItem("user_id");
    
    // Redirect to login if not authenticated
    if (!userId && !isLoginPage) {
        window.location.href = "login.html";
    }
    // Redirect to home if already authenticated and trying to view login
    if (userId && isLoginPage) {
        window.location.href = "index.html";
    }
});

function getCurrentUserId() {
    return localStorage.getItem("user_id");
}

function logout() {
    localStorage.removeItem("user_id");
    localStorage.removeItem("username");
    window.location.href = "login.html";
}

function toggleAuth() {
    const loginForm = document.getElementById("login-form");
    const signupForm = document.getElementById("signup-form");
    const title = document.getElementById("auth-title");
    
    if (loginForm.style.display === "none") {
        loginForm.style.display = "block";
        signupForm.style.display = "none";
        title.innerText = "Welcome Back";
    } else {
        loginForm.style.display = "none";
        signupForm.style.display = "block";
        title.innerText = "Create Account";
    }
}

async function login() {
    const username = document.getElementById("login-username").value.trim();
    const password = document.getElementById("login-password").value;
    
    try {
        const res = await fetch(`${API_BASE}/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });
        
        if (res.ok) {
            const data = await res.json();
            localStorage.setItem("user_id", data.user_id);
            localStorage.setItem("username", data.username);
            window.location.href = "index.html";
        } else {
            const err = await res.json();
            document.getElementById("auth-error").innerText = err.detail || "Login failed";
        }
    } catch (e) {
        document.getElementById("auth-error").innerText = "Network error connecting to API";
    }
}

async function signup() {
    const username = document.getElementById("signup-username").value.trim();
    const password = document.getElementById("signup-password").value;
    
    if (username.length < 3 || password.length < 3) {
        document.getElementById("auth-error").innerText = "Username and password must be at least 3 characters";
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/signup`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });
        
        if (res.ok) {
            const data = await res.json();
            localStorage.setItem("user_id", data.user_id);
            localStorage.setItem("username", data.username);
            window.location.href = "index.html";
        } else {
            const err = await res.json();
            document.getElementById("auth-error").innerText = err.detail || "Signup failed";
        }
    } catch (e) {
        document.getElementById("auth-error").innerText = "Network error connecting to API";
    }
}

// ==========================================
// 2. RENDERING & PAGE LOADERS
// ==========================================

function renderRow(containerId, movies) {
    const container = document.getElementById(containerId);
    if (!container) return;

    // AUTO-HIDE TRICK: If the array is empty, hide the row and its <h2> title
    if (!movies || movies.length === 0) {
        container.style.display = "none";
        if (container.previousElementSibling && container.previousElementSibling.tagName === "H2") {
            container.previousElementSibling.style.display = "none";
        }
        return; 
    }

    // Ensure it's visible if it has data (in case they rate a movie and come back)
    container.style.display = "grid";
    if (container.previousElementSibling && container.previousElementSibling.tagName === "H2") {
        container.previousElementSibling.style.display = "block";
    }

    container.innerHTML = "";
    movies.forEach(movie => {
        const tile = document.createElement("div");
        tile.className = "movie-tile";
        tile.onclick = () => window.location.href = `title.html?id=${movie.id}`;
        
        const imgSrc = movie.poster_path ? `${TMDB_IMAGE_BASE}${movie.poster_path}` : 'https://via.placeholder.com/150x225?text=No+Img';
        tile.innerHTML = `<img src="${imgSrc}" alt="${movie.title}"><p>${movie.title}</p>`;
        container.appendChild(tile);
    });
}

async function loadHome() {
    try {
        const userId = getCurrentUserId();
        const res = await fetch(`${API_BASE}/home?user_id=${userId}`);
        const data = await res.json();
        
        renderRow("personalized-row", data.personalized);
        renderRow("trending-row", data.trending);
        renderRow("popular-row", data.popular);
        renderRow("toprated-row", data.top_rated);
        renderRow("upcoming-row", data.upcoming);
    } catch (err) {
        console.error("Error loading home:", err);
    }
}

async function loadTitle() {
    const params = new URLSearchParams(window.location.search);
    const movieId = params.get("id");
    if (!movieId) return;

    try {
        const userId = getCurrentUserId();
        const res = await fetch(`${API_BASE}/movie/${movieId}?user_id=${userId}`);
        const data = await res.json();
        
        // Safe Extractor
        const movie = data.details || data; 
        const similar = data.similar_content || [];

        // Get DOM elements
        const movieBanner = document.getElementById('movie-banner');
        const movieTitle = document.getElementById('movie-title');
        const movieDesc = document.getElementById('movie-desc');

        // Populate Text
        movieTitle.innerText = movie.title || "Unknown Title";
        movieDesc.innerText = movie.description || movie.overview || "No description available.";
        
        // Populate Row (Only CBF now)
        renderRow("similar-row", similar);

        // Inject Image into the <img> tag
        const backdrop = movie.backdrop_url || (movie.backdrop_path ? `${TMDB_IMAGE_BASE}${movie.backdrop_path}` : null);
        const poster = movie.poster_url || (movie.poster_path ? `${TMDB_IMAGE_BASE}${movie.poster_path}` : null);

        const finalImage = backdrop || poster;

        if (finalImage) {
            movieBanner.src = finalImage;
            movieBanner.style.display = "block";
        } else {
            movieBanner.style.display = "none";
        }
    } catch (err) {
        console.error("Error loading title:", err);
    }
}

// ==========================================
// 3. INTERACTION LOGIC (RATING & SEARCH)
// ==========================================

async function submitRating() {
    const params = new URLSearchParams(window.location.search);
    const movieId = params.get("id");
    const ratingValue = document.getElementById("rating-value").value;
    
    // NEW: Grab the movie title directly from the HTML element on the page
    const movieTitle = document.getElementById("movie-title").innerText;
    
    const payload = { 
        user_id: parseInt(getCurrentUserId()), 
        movie_id: parseInt(movieId), 
        rating: parseFloat(ratingValue),
        title: movieTitle   // NEW: Send it to the backend
    };

    try {
        const response = await fetch(`${API_BASE}/rate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });


        const msg = document.getElementById("rating-msg");
        if (response.ok) {
            msg.innerText = "Rating saved successfully!";
            msg.style.color = "#4CAF50";
            setTimeout(() => msg.innerText = "", 3000);
        } else {
            msg.innerText = "Error saving rating.";
            msg.style.color = "#ff4d4d";
        }
    } catch (err) {
        console.error("Error saving rating:", err);
    }
}

let searchTimeout = null;
function debounceSearch() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(executeSearch, 300);
}

async function executeSearch() {
    const query = document.getElementById("search-box").value.trim();
    const resultsDiv = document.getElementById("search-results");
    
    if (query.length < 2) {
        resultsDiv.style.display = "none";
        return; 
    }

    try {
        const res = await fetch(`${API_BASE}/search?q=${query}`);
        const movies = await res.json();
        
        resultsDiv.innerHTML = "";
        if (movies.length === 0) {
            resultsDiv.innerHTML = `<div style="padding: 15px; color: #888;">No results found.</div>`;
        } else {
            movies.slice(0, 6).forEach(movie => { 
                const item = document.createElement("div");
                item.className = "search-item";
                item.onclick = () => window.location.href = `title.html?id=${movie.id}`;
                
                const imgSrc = movie.poster_path ? `${TMDB_IMAGE_BASE}${movie.poster_path}` : 'https://via.placeholder.com/40x60?text=No+Img';
                const year = movie.release_date ? movie.release_date.split('-')[0] : 'N/A';
                
                item.innerHTML = `<img src="${imgSrc}" alt="${movie.title}"><div><strong>${movie.title}</strong><div style="font-size: 12px; color: #aaa;">${year}</div></div>`;
                resultsDiv.appendChild(item);
            });
        }
        resultsDiv.style.display = "block";
    } catch (err) {
        console.error("Search failed:", err);
    }
}

// Close search dropdown when clicking outside
document.addEventListener("click", (e) => {
    const searchBox = document.getElementById("search-box");
    const resultsDiv = document.getElementById("search-results");
    if (searchBox && resultsDiv) {
        if (e.target !== searchBox && !resultsDiv.contains(e.target)) {
            resultsDiv.style.display = "none";
        }
    }
});