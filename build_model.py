"""Rebuilds movie_list.csv, the catalogue the app loads, from the two TMDB
CSVs:

    python build_model.py

The similarity matrix is not saved: the app computes it from the tags when
it starts (a few seconds), which keeps a ~180 MB file out of the repository.
"""
import pandas as pd

from recommender import build_movies

CATALOGUE_FILE = "movie_list.csv"
COLUMNS = ["movie_id", "title", "year", "tags"]


def main() -> None:
    movies = build_movies(pd.read_csv("tmdb_5000_movies.csv"), pd.read_csv("tmdb_5000_credits.csv"))
    movies[COLUMNS].to_csv(CATALOGUE_FILE, index=False)
    print(f"wrote {CATALOGUE_FILE}: {len(movies)} movies")


if __name__ == "__main__":
    main()
