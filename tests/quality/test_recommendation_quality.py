"""Are the recommendations any good?

Unit tests prove the engine follows its rules; these check its output on the
real catalogue against answers a person would agree with. Two kinds:
  - franchises: a sequel should bring up the rest of its series;
  - genre agreement: across all 4,803 movies, how many recommendations share
    at least one genre with the chosen film.

Measured when these tests were written: 92.0% genre agreement. The original
app scored 76.9%, because 45% of movies were read from the wrong row.
"""
import pytest

from recommender import recommend

GENRE_AGREEMENT_FLOOR = 0.90


def titles_recommended_for(title, catalogue, similarity, position_of):
    return {catalogue.at[i, "title"] for i in recommend(similarity, position_of(title))}


@pytest.mark.parametrize("chosen, any_of", [
    ("The Dark Knight", {"Batman Begins", "The Dark Knight Rises"}),
    ("Iron Man 2", {"Iron Man", "Iron Man 3"}),
    ("Toy Story 2", {"Toy Story", "Toy Story 3"}),
    ("Harry Potter and the Chamber of Secrets", {"Harry Potter and the Philosopher's Stone", "Harry Potter and the Prisoner of Azkaban"}),
    ("Shrek 2", {"Shrek", "Shrek the Third"}),
    ("The Godfather: Part II", {"The Godfather", "The Godfather: Part III"}),
    ("Spider-Man 2", {"Spider-Man", "Spider-Man 3"}),
    ("Kung Fu Panda 2", {"Kung Fu Panda", "Kung Fu Panda 3"}),
    ("The Matrix Reloaded", {"The Matrix", "The Matrix Revolutions"}),
    ("Jurassic World", {"Jurassic Park", "The Lost World: Jurassic Park"}),
    ("Skyfall", {"Casino Royale", "Quantum of Solace", "Spectre"}),
    ("Despicable Me 2", {"Despicable Me", "Minions"}),
])
def test_a_sequel_brings_up_its_series(chosen, any_of, catalogue, similarity, position_of):
    assert titles_recommended_for(chosen, catalogue, similarity, position_of) & any_of


@pytest.mark.xfail(reason="Known limitation of word-count matching: Part II's wedding-in-Thailand plot "
                          "outweighs the shared cast, so it recommends wedding films instead.")
def test_the_hangover_part_ii_brings_up_the_hangover(catalogue, similarity, position_of):
    assert "The Hangover" in titles_recommended_for("The Hangover Part II", catalogue, similarity, position_of)


def test_a_horror_film_gets_horror_recommendations(built_from_csvs, similarity, position_of):
    # "Devil" sits past the old index gap: the original app showed it five comedies.
    picks = recommend(similarity, position_of("Devil"))

    horror = [i for i in picks if "Horror" in built_from_csvs.at[i, "genres"]]
    assert len(horror) >= 3


def test_most_recommendations_share_a_genre_with_the_chosen_film(built_from_csvs, similarity):
    genres = built_from_csvs["genres"].apply(set)
    shared = total = 0
    for position, own in enumerate(genres):
        if not own:
            continue
        for pick in recommend(similarity, position):
            total += 1
            shared += bool(own & genres[pick])

    assert shared / total >= GENRE_AGREEMENT_FLOOR
