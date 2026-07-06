# 🎬 Cinematica: AI Movie Recommender System

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Scikit-Learn](https://img.shields.io/badge/scikit--learn-%23F7931E.svg?style=for-the-badge&logo=scikit-learn&logoColor=white)

**[🔥 View Live Application on Streamlit Cloud](https://your-app-name.streamlit.app/)**

Welcome to **Cinematica**, a highly intelligent, content-based Movie Recommendation Engine built organically with Machine Learning and Natural Language Processing. It leverages mathematical cosine similarity algorithms to deduce relationship proximity between thousands of cinematic configurations, wrapped dynamically inside a premium, Netflix-inspired dark-mode interface.

Developed by **Komal Mittal**.

---

## 🏗️ Step-by-Step Data Engineering Pipeline

The entire machine learning model is structurally documented and compiled inside `notebook.ipynb`. Here is an in-depth breakdown of the exact sequential step-by-step logic executed to train this AI engine:

### Step 1: Data Aggregation & Merging
We began by importing the `tmdb_5000_movies` and `tmdb_5000_credits` CSV datasets natively via Pandas. Since cast and crew details are intrinsically separated from general movie properties, we mathematically **Merged** the two datasets directly using the `title` variable as the explicit primary joining key.

### Step 2: Dimensionality Reduction (Feature Selection)
The native dataset contains over 20+ columns of metadata (e.g., Budget, Homepage, Spoken Languages). These introduce massive statistical noise. We stripped the structural matrix down to exclusively keep the 7 most mathematically relevant NLP features:
*   `movie_id` & `title` (Identifiers)
*   `overview`, `genres`, `keywords`, `cast`, `crew` (Content vectors)

### Step 3: Granular Data Preprocessing
The textual attributes natively arrived as stringified JSON dictionaries. We utilized `ast.literal_eval` to programmatically extract the raw string values:
*   **Genres & Keywords**: Extracted purely the literal name attributes (e.g., 'Action', 'Sci-Fi').
*   **Cast**: Sliced the arrays structurally to retain exclusively the Top 3 main lead actors.
*   **Crew**: Parsed the enormous production JSON strictly filtering and isolating exclusively for the `Director`.
*   **Whitespace Removal**: Dynamically stripped spaces between names (e.g., converting `"Johnny Depp"` into `"JohnnyDepp"`). This strictly prevents the AI from falsely assuming an actor named "Johnny Depp" and a director named "Johnny Galecki" are mathematically related simply because they share the keyword "Johnny".

### Step 4: The "Tag" Generation
We mathematically concatenated every single text-based value (`overview` list + `genres` + `keywords` + `cast` + `crew`) dynamically into one massive sequential string for every movie. This unified meta-string is explicitly defined as the **`tags`** string.

### Step 5: Natural Language Processing (Stemming)
Before vectorization, we applied **Porter Stemming** (via the `nltk` library). This mathematically collapses varying grammatical iterations of identical root strings natively into the exact same token (e.g., converting "acted", "acting", "actor" fundamentally all into "act"), massively optimizing algorithmic efficiency.

### Step 6: Text Vectorization & Mathematics (Bag of Words)
We executed the `CountVectorizer(max_features=5000, stop_words='english')` mathematical framework.
*   **Stop Words Removal**: Automatically destroyed irrelevant filler text (e.g., 'and', 'the', 'is').
*   **Vectorization**: Extracted the exact Top 5,000 most frequently appearing mathematical words across all `tags` strings natively mapped in the dataset. Each movie is then geometrically converted explicitly into a highly dimensional 5000x5000 coordinate vector.

### Step 7: Cosine Similarity Calculation
Rather than relying on basic numerical distance, the engine explicitly utilized **`cosine_similarity`** comparing mathematical vector angles. A similarity score approaching `1.0` strictly means the movies are effectively completely parallel coordinates natively mirroring identical contexts!

---

## 🚀 Features

*   **Intelligent Machine Learning Core**: Natively extracts thousands of variables processing explicitly real-time Cosine relationships on a compressed `tmdb_5000` database framework.
*   **API Data Hook Architecture**: Dynamically interacts exactly organically with the external TMDB API (`api.themoviedb.org`) structurally pulling beautiful high-resolution graphical movie posters linearly mapped natively to your exact ML predictions! 
*   **Premium Custom UI**: Bypasses traditional Streamlit static layouts leveraging incredibly responsive, custom CSS-grid mapped HTML components mirroring premium dynamic UX/UI systems like Netflix.

---

## 🛠 Installation & Usage natively

### 1. Clone the repository essentially
```bash
git clone https://github.com/your-username/movie-recommender-system.git
cd movie-recommender-system
```

### 2. Install explicitly required dependencies
Create your virtual environment natively cleanly, then strictly implicitly install directly:
```bash
pip install -r requirements.txt
```

### 3. Launching Locally natively
Ensure your `.pkl` and explicit `app.py` parameters are structurally seated, then execute:
```bash
python3 -m streamlit run app.py
```
Open exactly `http://localhost:8501` securely in your browser cleanly mapping the cinematic AI!

---

## 📊 Dataset Reference
The ML modeling pipeline relies entirely natively upon the publicly mapped **Kaggle TMDB 5000 Movie Dataset**, aggregating comprehensive metadata specifically spanning 5,000 explicit cinematic artifacts completely securely!
