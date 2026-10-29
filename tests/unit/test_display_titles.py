"""display_titles(): what the dropdown shows. Every entry must name exactly
one film, so a shared title gets its year."""
import pandas as pd

from recommender import display_titles


def catalogue(*rows):
    return pd.DataFrame(rows, columns=["title", "year"]).astype({"year": "Int64"})


def test_a_unique_title_is_shown_as_it_is():
    assert display_titles(catalogue(("Avatar", 2009), ("Up", 2009))) == ["Avatar", "Up"]


def test_films_sharing_a_title_are_told_apart_by_year():
    shown = display_titles(catalogue(("Batman", 1989), ("Avatar", 2009), ("Batman", 1966)))

    assert shown == ["Batman (1989)", "Avatar", "Batman (1966)"]


def test_a_shared_title_without_a_year_is_shown_plain():
    # No year to add. Not the case in today's catalogue (checked in
    # data/test_catalogue.py), but it must not crash or print "<NA>".
    assert display_titles(catalogue(("Batman", 1989), ("Batman", None))) == ["Batman (1989)", "Batman"]


def test_the_same_title_with_different_capitals_is_not_treated_as_shared():
    assert display_titles(catalogue(("Batman", 1989), ("BATMAN", 2010))) == ["Batman", "BATMAN"]
