"""The recommendation engine: building the catalogue from the TMDB CSVs, the
similarity matrix, recommendations and posters.

Kept apart from the Streamlit page (app.py) so every piece can be tested
without running the UI. The data steps are the ones from notebook.ipynb,
with three fixes:

- movies and credits are joined on the movie id, not the title. Three titles
  are shared by two films each (Batman, The Host, Out of the Blue), and the
  title join paired each film's story with the other film's cast.
- a movie without an overview is kept (with an empty overview) instead of
  being dropped, so it can still be chosen and recommended.
- the catalogue gets a fresh 0..n-1 index, so a row's label is also its row
  in the similarity matrix (see recommend()).
"""
import ast
from typing import Callable, List, Optional

import numpy as np
import pandas as pd
import requests
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

N_RECOMMENDATIONS = 5
TOP_CAST = 3
VOCABULARY_SIZE = 5000

POSTER_BASE_URL = "https://image.tmdb.org/t/p/w500"
PLACEHOLDER_POSTER = "https://via.placeholder.com/500x750/000000/FFFFFF?text=Poster+Unavailable"
TMDB_MOVIE_URL = "https://api.themoviedb.org/3/movie/{movie_id}"
POSTER_TIMEOUT_SECONDS = 5


# ── building the catalogue (notebook.ipynb, as functions) ───────────────

def names(json_text: str) -> List[str]:
    """The "name" of every entry in a TMDB JSON list, in order:
    '[{"id": 28, "name": "Action"}]' -> ["Action"]."""
    return [entry["name"] for entry in ast.literal_eval(json_text)]


def top_cast(json_text: str, n: int = TOP_CAST) -> List[str]:
    """The first n actors, in TMDB's billing order."""
    return names(json_text)[:n]


def directors(json_text: str) -> List[str]:
    """Everyone credited with the job "Director" (some films have two)."""
    return [entry["name"] for entry in ast.literal_eval(json_text) if entry["job"] == "Director"]


def without_spaces(values: List[str]) -> List[str]:
    """"Johnny Depp" -> "JohnnyDepp", so a name is one token: "Johnny" alone
    would otherwise make Johnny Depp and Johnny Galecki look related."""
    return [value.replace(" ", "") for value in values]


def build_movies(movies_csv: pd.DataFrame, credits_csv: pd.DataFrame) -> pd.DataFrame:
    """The catalogue: movie_id, title, year, genres and the "tags" text that
    similarity is computed from (overview words + genres + keywords + top
    cast + directors). One row per movie, index 0..n-1."""
    credits = credits_csv[["movie_id", "cast", "crew"]]
    df = movies_csv.rename(columns={"id": "movie_id"}).merge(credits, on="movie_id", validate="one_to_one")

    genres = df["genres"].apply(names).apply(without_spaces)
    tags = (
        df["overview"].fillna("").str.split()
        + genres
        + df["keywords"].apply(names).apply(without_spaces)
        + df["cast"].apply(top_cast).apply(without_spaces)
        + df["crew"].apply(directors).apply(without_spaces)
    )
    year = pd.to_datetime(df["release_date"], errors="coerce").dt.year.astype("Int64")
    return pd.DataFrame({
        "movie_id": df["movie_id"],
        "title": df["title"],
        "year": year,
        "genres": genres,
        "tags": tags.apply(" ".join),
    }).reset_index(drop=True)


def build_similarity(tags: pd.Series) -> np.ndarray:
    """Cosine similarity between every pair of movies' tag word counts
    (the 5,000 most common words, English stop words removed)."""
    vectorizer = CountVectorizer(max_features=VOCABULARY_SIZE, stop_words="english")
    if not any(vectorizer.build_analyzer()(text) for text in tags):
        # Not one word left after removing stop words: scikit-learn refuses
        # to fit an empty vocabulary. No words means no similarity, so every
        # movie gets "no close matches" rather than the app failing to start.
        # (Found by a property test, not by the real catalogue.)
        return np.zeros((len(tags), len(tags)))
    return cosine_similarity(vectorizer.fit_transform(tags))


def display_titles(movies: pd.DataFrame) -> List[str]:
    """What the dropdown shows: the title, plus the year when two films share
    a title ("Batman (1966)" and "Batman (1989)"), so each entry is one film."""
    shared = movies["title"].duplicated(keep=False)
    labels = []
    for title, year, is_shared in zip(movies["title"], movies["year"], shared):
        labels.append(f"{title} ({year})" if is_shared and pd.notna(year) else title)
    return labels


# ── recommending ─────────────────────────────────────────────────────────

def recommend(similarity: np.ndarray, position: int, k: int = N_RECOMMENDATIONS) -> List[int]:
    """Row positions of the k movies most similar to the movie at `position`,
    best first.

    `position` is a row number, never an index label: app.py used to look up
    the label, and after the notebook's dropna() labels and rows disagreed
    for 45% of the catalogue, so those movies got another film's
    recommendations (and the last three crashed the app).

    The movie itself is never recommended, ties keep catalogue order, and a
    movie with no similarity at all (score 0) is not a recommendation - so
    fewer than k can come back."""
    scores = similarity[position]
    ranked = np.argsort(-scores, kind="stable")
    picks = [int(i) for i in ranked if i != position and scores[i] > 0]
    return picks[:k]


# ── posters ──────────────────────────────────────────────────────────────

def poster_url(movie_id: int, api_key: Optional[str], get: Optional[Callable] = None) -> str:
    """The movie's poster from TMDB, or a placeholder if there is no key, the
    request fails or times out, or TMDB has no poster for it. Never raises:
    a missing poster must not stop the recommendations showing.

    `get` defaults to requests.get, looked up at call time so tests can
    replace the network."""
    if not api_key:
        return PLACEHOLDER_POSTER
    get = get or requests.get
    try:
        response = get(
            TMDB_MOVIE_URL.format(movie_id=int(movie_id)),
            params={"api_key": api_key, "language": "en-US"},
            timeout=POSTER_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        path = response.json().get("poster_path")
    except (requests.RequestException, ValueError, AttributeError):
        return PLACEHOLDER_POSTER
    if isinstance(path, str) and path.startswith("/"):
        return POSTER_BASE_URL + path
    return PLACEHOLDER_POSTER
