"""build_similarity: how alike two movies' tags are (cosine similarity of
word counts, English stop words removed, vocabulary capped)."""
import numpy as np
import pandas as pd
import pytest
from hypothesis import given, strategies as st

import recommender
from recommender import build_similarity


def similarity_of(a: str, b: str) -> float:
    return build_similarity(pd.Series([a, b]))[0, 1]


def test_identical_tags_are_fully_similar():
    assert similarity_of("space alien war", "space alien war") == pytest.approx(1.0)


def test_tags_with_no_word_in_common_are_not_similar_at_all():
    assert similarity_of("space alien war", "wedding comedy romance") == pytest.approx(0.0)


def test_stop_words_alone_never_make_two_movies_similar():
    assert similarity_of("the cat and the hat", "the dog and the bone") == pytest.approx(0.0)


def test_word_order_does_not_matter():
    assert similarity_of("alien space war", "war space alien") == pytest.approx(1.0)


def test_single_word_names_keep_two_different_johnnys_apart():
    # Why the pipeline removes spaces from names.
    assert similarity_of("JohnnyDepp pirate", "JohnnyGalecki sitcom") == pytest.approx(0.0)
    assert similarity_of("Johnny Depp pirate", "Johnny Galecki sitcom") > 0


def test_only_the_most_common_words_count(monkeypatch):
    monkeypatch.setattr(recommender, "VOCABULARY_SIZE", 1)
    # "space" is the most common word; "zebra" falls outside the vocabulary,
    # so the two zebra movies share nothing that counts.
    tags = pd.Series(["space zebra", "space", "space", "zebra quokka"])

    assert build_similarity(tags)[0, 3] == pytest.approx(0.0)


def test_a_catalogue_with_no_usable_words_has_no_similarities_instead_of_crashing():
    s = build_similarity(pd.Series(["the", "and the", "of"]))

    assert s.shape == (3, 3) and not s.any()


words = st.sampled_from(["space", "alien", "war", "love", "comedy", "heist", "ninja", "robot", "the", "and"])
corpora = st.lists(st.lists(words, min_size=1, max_size=8).map(" ".join), min_size=2, max_size=8)


@given(corpora)
def test_similarity_is_symmetric_between_zero_and_one(tags):
    s = build_similarity(pd.Series(tags))

    assert np.allclose(s, s.T)
    assert (s >= -1e-9).all() and (s <= 1 + 1e-9).all()


@given(corpora)
def test_every_movie_with_a_real_word_is_fully_similar_to_itself(tags):
    s = build_similarity(pd.Series(tags))
    for i, text in enumerate(tags):
        if set(text.split()) - {"the", "and"}:
            assert s[i, i] == pytest.approx(1.0)
