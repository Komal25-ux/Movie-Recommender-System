"""The shipped catalogue, movie_list.csv: its shape, and what happens for
every one of its 4,803 movies."""
import pandas as pd

from build_model import COLUMNS
from recommender import N_RECOMMENDATIONS, display_titles, recommend


def test_the_catalogue_has_one_row_per_tmdb_movie(catalogue):
    assert list(catalogue.columns) == ["movie_id", "title", "year", "tags"]
    assert len(catalogue) == 4803          # every film in TMDB 5000; none dropped, none duplicated
    assert catalogue["movie_id"].is_unique


def test_rows_are_numbered_zero_to_n_minus_one(catalogue):
    # The original pickle had gaps here (from dropna), so for 45% of movies
    # a row's label pointed at another movie's row in the similarity matrix.
    assert catalogue.index.tolist() == list(range(len(catalogue)))


def test_every_movie_has_tags_to_compare(catalogue):
    assert catalogue["tags"].str.strip().ne("").all()


def test_every_dropdown_entry_names_exactly_one_film(catalogue):
    labels = display_titles(catalogue)

    assert len(set(labels)) == len(labels)
    assert {"Batman (1966)", "Batman (1989)", "The Host (2006)", "The Host (2013)"} <= set(labels)


def test_the_shipped_file_is_exactly_what_build_model_produces(catalogue, built_from_csvs):
    # Guards against the catalogue and the code drifting apart, which is how
    # the notebook's pickle ended up with bugs the code didn't show.
    pd.testing.assert_frame_equal(catalogue, built_from_csvs[COLUMNS])


def test_every_movie_gets_five_recommendations_and_never_itself(similarity):
    for position in range(len(similarity)):
        picks = recommend(similarity, position)
        assert len(picks) == N_RECOMMENDATIONS, position
        assert position not in picks, position


def test_the_three_movies_that_used_to_crash_the_app_now_work(similarity, position_of):
    for title in ["Signed, Sealed, Delivered", "Shanghai Calling", "My Date with Drew"]:
        assert len(recommend(similarity, position_of(title))) == N_RECOMMENDATIONS
