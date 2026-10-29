"""Turning the TMDB CSVs into the catalogue (recommender.build_movies and the
small parsing functions it uses - the steps from notebook.ipynb)."""
import json

import pandas as pd
import pytest

from recommender import build_movies, directors, names, top_cast, without_spaces


def tmdb_list(*entries):
    return json.dumps(list(entries))


def person(name, job=None):
    return {"name": name, "job": job} if job else {"name": name}


# ── parsing TMDB's JSON columns ──────────────────────────────────────

@pytest.mark.parametrize("text, expected", [
    ('[{"id": 28, "name": "Action"}, {"id": 12, "name": "Adventure"}]', ["Action", "Adventure"]),
    ('[{"id": 18, "name": "Drama"}]', ["Drama"]),
    ("[]", []),
])
def test_names_reads_every_name_in_order(text, expected):
    assert names(text) == expected


@pytest.mark.parametrize("bad", ["", "not json", "[{'id': 1}]"])
def test_malformed_data_fails_loudly_at_build_time(bad):
    # Better a failed build than a catalogue with silently missing genres.
    with pytest.raises((ValueError, SyntaxError, KeyError)):
        names(bad)


@pytest.mark.parametrize("billed, kept", [
    (0, 0), (1, 1), (2, 2),
    (3, 3),     # exactly the limit
    (4, 3),     # one over: the fourth actor is dropped
    (25, 3),
])
def test_top_cast_keeps_at_most_three_actors(billed, kept):
    cast = tmdb_list(*(person(f"Actor {i}") for i in range(billed)))
    assert top_cast(cast) == [f"Actor {i}" for i in range(kept)]


@pytest.mark.parametrize("crew, expected", [
    (tmdb_list(person("Christopher Nolan", "Director"), person("Hans Zimmer", "Original Music Composer")), ["Christopher Nolan"]),
    (tmdb_list(person("Joel Coen", "Director"), person("Ethan Coen", "Director")), ["Joel Coen", "Ethan Coen"]),
    (tmdb_list(person("Roger Deakins", "Director of Photography")), []),   # a different job, not a director
    (tmdb_list(), []),
])
def test_directors_are_exactly_the_people_credited_as_director(crew, expected):
    assert directors(crew) == expected


@pytest.mark.parametrize("before, after", [
    (["Johnny Depp"], ["JohnnyDepp"]),
    (["Science Fiction", "Drama"], ["ScienceFiction", "Drama"]),
    (["Gabriel  García  Márquez"], ["GabrielGarcíaMárquez"]),
    ([], []),
])
def test_names_become_single_words(before, after):
    assert without_spaces(before) == after


# ── building the catalogue ───────────────────────────────────────────

def csvs(*movies):
    """Minimal movies/credits CSV frames. Each movie: (id, title, overview, date, genres, cast, director)."""
    movie_rows, credit_rows = [], []
    for movie_id, title, overview, date, genres, cast, director in movies:
        movie_rows.append({"id": movie_id, "title": title, "overview": overview, "release_date": date,
                           "genres": tmdb_list(*({"name": g} for g in genres)), "keywords": "[]"})
        credit_rows.append({"movie_id": movie_id, "title": title,
                            "cast": tmdb_list(*(person(a) for a in cast)),
                            "crew": tmdb_list(person(director, "Director"))})
    return pd.DataFrame(movie_rows), pd.DataFrame(credit_rows)


def test_two_films_with_the_same_title_each_keep_their_own_cast():
    # The notebook joined on title, so each "Batman" also got the other's cast.
    movies, credits = csvs(
        (268, "Batman", "The Dark Knight of Gotham City", "1989-06-23", ["Action"], ["Michael Keaton"], "Tim Burton"),
        (2661, "Batman", "The Dynamic Duo faces four villains", "1966-07-30", ["Comedy"], ["Adam West"], "Leslie H. Martinson"),
    )

    catalogue = build_movies(movies, credits)

    assert len(catalogue) == 2
    burton, martinson = catalogue["tags"]
    assert "MichaelKeaton" in burton and "AdamWest" not in burton
    assert "AdamWest" in martinson and "MichaelKeaton" not in martinson


def test_the_catalogue_has_exactly_these_columns():
    movies, credits = csvs((1, "Up", "x", "2009-05-13", [], [], "D"))
    assert list(build_movies(movies, credits).columns) == ["movie_id", "title", "year", "genres", "tags"]


def test_years_are_whole_numbers_so_the_dropdown_reads_batman_1989():
    # A year stored as a decimal still equals 1989 in Python, but the user
    # would see "Batman (1989.0)" (mutation testing showed nothing checked this).
    from recommender import display_titles
    movies, credits = csvs(
        (268, "Batman", "x", "1989-06-23", [], [], "Tim Burton"),
        (2661, "Batman", "y", "1966-07-30", [], [], "Leslie H. Martinson"),
    )

    assert display_titles(build_movies(movies, credits)) == ["Batman (1989)", "Batman (1966)"]


def test_the_tags_are_overview_genres_keywords_cast_then_director():
    movies, credits = csvs((1, "Up", "An old man flies away", "2009-05-13", ["Animation", "Family"],
                            ["Ed Asner", "Jordan Nagai", "Christopher Plummer", "Bob Peterson"], "Pete Docter"))

    [tags] = build_movies(movies, credits)["tags"]

    assert tags == "An old man flies away Animation Family EdAsner JordanNagai ChristopherPlummer PeteDocter"


def test_a_film_without_an_overview_is_kept_rather_than_dropped():
    movies, credits = csvs((1, "Food Chains", None, "2014-04-26", ["Documentary"], ["Eva Longoria"], "Sanjay Rawal"))

    catalogue = build_movies(movies, credits)

    assert catalogue["tags"].tolist() == ["Documentary EvaLongoria SanjayRawal"]


def test_rows_are_numbered_from_zero_whatever_the_csv_order():
    movies, credits = csvs(
        (500, "C", "c", "2001-01-01", [], [], "X"),
        (7, "A", "a", "2002-01-01", [], [], "Y"),
        (42, "B", "b", "2003-01-01", [], [], "Z"),
    )

    catalogue = build_movies(movies, credits.iloc[::-1])   # credits in a different order

    assert catalogue.index.tolist() == [0, 1, 2]
    assert catalogue["movie_id"].tolist() == [500, 7, 42]


def test_the_year_comes_from_the_release_date():
    movies, credits = csvs((1, "X", "x", "1989-06-23", [], [], "D"))
    assert build_movies(movies, credits)["year"].tolist() == [1989]


@pytest.mark.parametrize("date", ["", None, "not a date"])
def test_a_missing_or_unreadable_date_gives_no_year(date):
    movies, credits = csvs((1, "X", "x", date, [], [], "D"))
    assert build_movies(movies, credits)["year"].isna().all()


def test_a_movie_credited_twice_is_a_build_error_not_a_duplicate_row():
    movies, credits = csvs((1, "X", "x", "2000-01-01", [], [], "D"))
    credits = pd.concat([credits, credits])

    with pytest.raises(pd.errors.MergeError):
        build_movies(movies, credits)
