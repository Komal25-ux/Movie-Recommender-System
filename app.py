import streamlit as st
import pickle
import requests

import sklearn
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ==================== Page Config ==================== #
st.set_page_config(page_title="Cinematica | AI Recommender", page_icon="🍿", layout="wide", initial_sidebar_state="collapsed")

# ================= Advanced UI CSS ==================== #
st.markdown("""
<style>
/* Import Poppins Font for a clean, modern aesthetic */
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Poppins', sans-serif;
}

/* Deep immersive dark background with subtle red glows */
.stApp {
    background-color: #050505 !important;
    background-image: 
        radial-gradient(circle at 20% 30%, rgba(229, 9, 20, 0.12), transparent 40%),
        radial-gradient(circle at 80% 70%, rgba(229, 9, 20, 0.12), transparent 40%);
    background-attachment: fixed;
    color: white;
}

/* Hide Streamlit Native UI items */
header {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {display: none;}

/* Layout adjustment to bring content higher up */
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 5rem !important;
    max-width: 1200px;
}

/* Title Design */
.brand {
    font-size: 4.5rem;
    font-weight: 800;
    text-align: center;
    text-transform: uppercase;
    letter-spacing: -2px;
    background: linear-gradient(135deg, #ffffff 0%, #aaaaaa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0px;
    padding-top: 0px;
    line-height: 1.1;
}

.brand-red {
    background: linear-gradient(to right, #E50914, #ff6b6b, #E50914);
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: shine 4s linear infinite;
}

@keyframes shine {
    to { background-position: 200% center; }
}

.sub-brand {
    text-align: center;
    color: #8c8c8c;
    font-weight: 300;
    font-size: 1.1rem;
    letter-spacing: 4px;
    text-transform: uppercase;
    margin-bottom: 3.5rem;
    margin-top: 5px;
}

/* Customizing the Selectbox */
.stSelectbox label {
    color: #cccccc !important;
    font-weight: 600;
    font-size: 1.1rem;
    letter-spacing: 0.5px;
    margin-bottom: 15px;
}

div[data-baseweb="select"] > div {
    background-color: #141414 !important;
    border: 1px solid #333333 !important;
    border-radius: 8px;
    color: white !important;
    transition: all 0.3s;
    box-shadow: inset 0 2px 5px rgba(0,0,0,0.5);
    height: 50px;
}

div[data-baseweb="select"] > div:hover {
    border-color: #E50914 !important;
}

/* Primary Button Styling */
.stButton>button {
    background-color: #E50914;
    color: white;
    font-weight: 700;
    font-size: 1rem;
    border: none;
    border-radius: 8px;
    padding: 0px 10px; /* Reduced horizontal padding to prevent text cutoff */
    width: 100%;
    margin-top: 0px; /* Removed margin-top to align directly with selectbox */
    height: 50px; /* Force height to match exactly with selectbox */
    text-transform: uppercase;
    letter-spacing: 1px; /* Slightly reduced letter spacing for fit */
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(229, 9, 20, 0.3);
}

.stButton>button:hover {
    background-color: #f40612;
    transform: scale(1.02);
    box-shadow: 0 8px 25px rgba(229, 9, 20, 0.5);
    color: white;
}

.stButton>button:active {
    transform: scale(0.98);
}

.stButton>button:focus:not(:active) {
    color: white;
}

/* Netflix Style Cards built with custom HTML structure */
.movie-grid {
    display: flex;
    justify-content: center;
    gap: 25px;
    flex-wrap: wrap;
    margin-top: 2rem;
    padding: 20px 0;
}

.movie-card {
    position: relative;
    width: 200px;
    height: 300px;
    border-radius: 10px;
    overflow: hidden;
    cursor: pointer;
    background-color: #111;
    box-shadow: 0 10px 20px rgba(0,0,0,0.6);
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.movie-card img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform 0.5s ease;
}

.movie-card::after {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    box-shadow: inset 0px 0px 0px 2px transparent;
    transition: box-shadow 0.3s;
    pointer-events: none;
    border-radius: 10px;
}

.movie-card:hover {
    transform: scale(1.1) translateY(-10px);
    box-shadow: 0 15px 30px rgba(229, 9, 20, 0.4);
    z-index: 10;
}

.movie-card:hover::after {
    box-shadow: inset 0px 0px 0px 2px #E50914;
}

.movie-card:hover img {
    transform: scale(1.1);
}

.movie-info {
    position: absolute;
    bottom: 0; left: 0; right: 0;
    padding: 40px 15px 15px 15px;
    background: linear-gradient(to top, rgba(0,0,0,0.95) 0%, rgba(0,0,0,0.6) 50%, transparent 100%);
    color: white;
    opacity: 0;
    transform: translateY(20px);
    transition: all 0.4s ease;
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
}

.movie-card:hover .movie-info {
    opacity: 1;
    transform: translateY(0);
}

.movie-title {
    font-size: 1.1rem;
    font-weight: 700;
    line-height: 1.2;
    text-shadow: 0 2px 4px rgba(0,0,0,1);
    margin: 0;
}

.movie-subtitle {
    font-size: 0.8rem;
    color: #aaaaaa;
    font-weight: 400;
    margin-top: 5px;
}

/* Results text */
.results-header {
    text-align: center;
    font-size: 1.8rem;
    font-weight: 300;
    color: #e5e5e5;
    margin-top: 3rem;
}
.results-header span {
    font-weight: 700;
    color: white;
}

/* Separator line */
.separator {
    height: 1px;
    background: linear-gradient(to right, transparent, rgba(255,255,255,0.1), transparent);
    margin: 3rem 0;
}

/* Custom Footer */
.custom-footer {
    text-align: center;
    color: #FFFFFF;
    font-size: 1rem;
    margin-top: 5rem;
    font-weight: 300;
}
</style>
""", unsafe_allow_html=True)

# ==================== Functions ==================== #
def fetch_poster(movie_id):
    url = "https://api.themoviedb.org/3/movie/{}?api_key=078f6f4300295e24391e10cf756c47af&language=en-US".format(movie_id)
    try:
        data = requests.get(url).json()
        poster_path = data['poster_path']
        full_path = "https://image.tmdb.org/t/p/w500" + poster_path
        return full_path
    except:
        return "https://via.placeholder.com/500x750/000000/FFFFFF?text=Poster+Unavailable"

def recommend(movie):
    index = movies[movies['title'] == movie].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
    recommended_movie_names = []
    recommended_movie_posters = []
    
    # Check if we have 5 movies, otherwise adjust the limit
    range_limit = min(6, len(distances))
    
    for i in distances[1:range_limit]:
        movie_id = movies.iloc[i[0]].movie_id
        recommended_movie_posters.append(fetch_poster(movie_id))
        recommended_movie_names.append(movies.iloc[i[0]].title)
    return recommended_movie_names, recommended_movie_posters

# ==================== Load Data ==================== #
@st.cache_data
def load_data():
    movies = pickle.load(open('movie_list.pkl','rb'))
    
    # Rather than shipping a 180MB file to the cloud, we calculate the similarity 
    # vector geometry on the fly once when the server boots!
    cv = CountVectorizer(max_features=5000, stop_words='english')
    vector = cv.fit_transform(movies['tags']).toarray()
    similarity = cosine_similarity(vector)
    
    return movies, similarity

movies, similarity = load_data()
movies_list = movies['title'].values

# ==================== App Layout ==================== #
# Headline Brand
st.markdown("<h1 class='brand'>Cinema<span class='brand-red'>tica</span></h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-brand'>Intelligence meets Entertainment</p>", unsafe_allow_html=True)

# Create a sleek centralized search bar
# We use a slightly wider central column ratio to fit the button better
col_space1, col_content, col_space2 = st.columns([1, 2.8, 1])

with col_content:
    st.markdown("<p style='color: #cccccc; font-weight: 600; font-size: 1.1rem; margin-bottom: 10px; letter-spacing: 0.5px;'>Select a foundation movie to base recommendations on</p>", unsafe_allow_html=True)
    
    # A smaller 2-column grid to hold the select box and button tightly side by side
    inner_c1, inner_c2 = st.columns([4, 1.8]) # Increased right ratio for the button
    
    with inner_c1:
        selected_movie = st.selectbox(
            "Hidden_Label",
            movies_list,
            help="Type to search or select a film from the dropdown.",
            label_visibility="collapsed" # Hides label, keeping field flush with the button
        )
    with inner_c2:
        submit_btn = st.button('Recommend')
        
    # Placing the loading spinner inside the centered 'col_content' restricts its width
    # and forces it to display directly underneath the search bar.
    if submit_btn:
        with st.spinner("Analyzing parameters and gathering posters..."):
            recommended_movie_names, recommended_movie_posters = recommend(selected_movie)

# ==================== Recommend Action ==================== #
if submit_btn:
    st.markdown("<div class='separator'></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='results-header'>Matches based on <span>{selected_movie}</span></div>", unsafe_allow_html=True)
    
    # We output pure HTML to completely bypass Streamlit UI limitations
    # IMPORTANT: Kept in a single line without newlines to prevent Streamlit from parsing inner text as Markdown
    cards_html = ""
    for name, poster in zip(recommended_movie_names, recommended_movie_posters):
        # Escape any potential double quotes in the movie name to avoid HTML parsing errors
        safe_name = str(name).replace('"', '&quot;')
        cards_html += f'<div class="movie-card"><img src="{poster}" alt="{safe_name}"><div class="movie-info"><h3 class="movie-title">{safe_name}</h3><p class="movie-subtitle">Recommended Match</p></div></div>'
        
    final_output = f'<div class="movie-grid">{cards_html}</div>'
    st.markdown(final_output, unsafe_allow_html=True)

# ==================== Footer ==================== #
st.markdown("<div class='custom-footer'>Developed by Komal Mittal</div>", unsafe_allow_html=True)
