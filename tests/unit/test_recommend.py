"""recommend(): the k movies most similar to the chosen one.

Rules, each tested below:
  best first · never the movie itself · ties keep catalogue order ·
  zero similarity is not a recommendation · at most k
"""
import numpy as np
import pytest
from hypothesis import given, strategies as st

from recommender import N_RECOMMENDATIONS, recommend

# Similarity between six movies (symmetric, 1.0 on the diagonal).
S = np.array([
    #  0     1     2     3     4     5
    [1.00, 0.20, 0.90, 0.00, 0.50, 0.50],   # 0
    [0.20, 1.00, 0.10, 0.30, 0.00, 0.00],   # 1
    [0.90, 0.10, 1.00, 0.00, 0.40, 0.00],   # 2
    [0.00, 0.30, 0.00, 1.00, 0.00, 0.00],   # 3
    [0.50, 0.00, 0.40, 0.00, 1.00, 0.00],   # 4
    [0.50, 0.00, 0.00, 0.00, 0.00, 1.00],   # 5
])


def test_the_most_similar_movies_come_first():
    assert recommend(S, 0, k=3) == [2, 4, 5]


def test_ties_keep_catalogue_order():
    # 4 and 5 both score 0.50 against movie 0; 4 comes first in the catalogue.
    assert recommend(S, 0, k=5) == [2, 4, 5, 1]


def test_a_large_tie_still_keeps_catalogue_order():
    # Six movies were not enough to tell sorts apart: NumPy's default sort
    # only reorders ties on longer arrays (mutation testing showed this).
    tie = np.full((200, 200), 0.5)
    np.fill_diagonal(tie, 1.0)

    assert recommend(tie, 0) == [1, 2, 3, 4, 5]


def test_the_chosen_movie_is_never_recommended_even_when_another_ties_with_it():
    duplicate = np.array([[1.0, 1.0, 0.2], [1.0, 1.0, 0.2], [0.2, 0.2, 1.0]])
    assert recommend(duplicate, 1) == [0, 2]


def test_movies_with_nothing_in_common_are_not_recommendations():
    # Movie 3 shares words only with movie 1, so it gets one recommendation,
    # not four made-up ones.
    assert recommend(S, 3) == [1]


def test_a_movie_with_nothing_in_common_with_anything_gets_none():
    alone = np.array([[0.0, 0.0], [0.0, 1.0]])   # an all-zero row: no words survived
    assert recommend(alone, 0) == []


@pytest.mark.parametrize("k, expected", [(0, []), (1, [2]), (4, [2, 4, 5, 1]), (5, [2, 4, 5, 1])])
def test_at_most_k_come_back(k, expected):
    assert recommend(S, 0, k=k) == expected


def test_five_by_default():
    many = np.full((10, 10), 0.5)
    assert len(recommend(many, 0)) == N_RECOMMENDATIONS == 5


@st.composite
def similarity_matrices(draw):
    n = draw(st.integers(min_value=1, max_value=12))
    upper = draw(st.lists(st.sampled_from([0.0, 0.1, 0.25, 0.5, 0.75, 1.0]), min_size=n * n, max_size=n * n))
    m = np.array(upper).reshape(n, n)
    m = np.triu(m, 1)
    m = m + m.T
    np.fill_diagonal(m, 1.0)
    return m, draw(st.integers(min_value=0, max_value=n - 1)), draw(st.integers(min_value=0, max_value=6))


@given(similarity_matrices())
def test_recommendations_are_always_the_true_top_k(case):
    s, chosen, k = case
    picks = recommend(s, chosen, k=k)

    assert chosen not in picks
    assert len(picks) == len(set(picks)) <= k
    assert all(s[chosen, p] > 0 for p in picks)
    scores = [s[chosen, p] for p in picks]
    assert scores == sorted(scores, reverse=True)
    if picks:   # nothing left out scores better than the last pick
        left_out = set(range(len(s))) - set(picks) - {chosen}
        assert all(s[chosen, o] <= scores[-1] for o in left_out)
